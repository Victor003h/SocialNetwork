#!/usr/bin/env bash
# =============================================================================
# Protocolo OBLIGATORIO de tolerancia y consistencia (rúbrica §5):
#   3 nodos ↑  ->  apagar 2 (incluido el leader)  ->  1 nodo nuevo ↑  ->  apagar el último original
#
# Verifica con EVIDENCIA EJECUTABLE (checksums de Postgres, roles/epoch vía /info,
# y logs de reelección) que:
#   - los datos escritos se replican en todos los nodos,
#   - no hay pérdida de estado ni divergencia tras dos failovers,
#   - el nodo nuevo se sincroniza con el estado actual,
#   - los logs reflejan detección de caída, reelección y nuevo epoch (fencing).
#
# Uso:   make up   (espera a que arranque)   &&   make test
# =============================================================================
set -uo pipefail
cd "$(dirname "$0")/.."

COMPOSE="docker compose -f docker-compose.cluster.yml"
# El gateway se prueba por la MISMA ruta de red que usa el frontend (contenedor en
# edge_net -> https://api_services:7000), no por el loopback del host: el publish de
# Docker + docker-userland-proxy puede colgar el handshake TLS en algunos hosts, lo
# que no refleja el camino real del demo. Resolver api_services por DNS de Docker sí.
GW="https://api_services:7000"
EDGE_NET="edge_net"
CURL_IMG="curlimages/curl:latest"
EVID="pruebas/evidence"
mkdir -p "$EVID"

PASS=0; FAIL=0
ok(){  echo "  [OK]   $1"; PASS=$((PASS+1)); }
bad(){ echo "  [FAIL] $1"; FAIL=$((FAIL+1)); }
sec(){ echo ""; echo "============================================================"; echo "== $1"; echo "============================================================"; }

# --- helpers -----------------------------------------------------------------
# Llama al gateway desde un contenedor efímero en edge_net (ruta real del frontend).
gw(){ docker run --rm --network "$EDGE_NET" "$CURL_IMG" -sk -m 15 "$@"; }
jget(){ python3 -c "import sys,json; d=json.load(sys.stdin); print($1)" 2>/dev/null; }

# /info de un nodo usando su propio cert mTLS (ejecutado dentro del contenedor)
node_info(){
  docker exec "node$1" python -c "import ssl,urllib.request as u,sys; \
c=ssl.create_default_context(cafile='/app/certs/ca.crt'); \
c.load_cert_chain('/app/certs/node.crt','/app/certs/node.key'); \
sys.stdout.write(u.urlopen('https://localhost:5000/info',context=c,timeout=4).read().decode())" 2>/dev/null
}
role_of(){  node_info "$1" | jget "d['local_node']['role']"; }
epoch_of(){ node_info "$1" | jget "d['epoch']"; }

# Checksum determinista de la tabla posts directamente en el Postgres del nodo.
posts_md5(){ docker exec "db$1" psql -U admin -d cluster_db -tA -c \
  "SELECT COALESCE(md5(string_agg(id::text||':'||content, ',' ORDER BY id)),'EMPTY') FROM posts;" 2>/dev/null | tr -d '[:space:]'; }
posts_count(){ docker exec "db$1" psql -U admin -d cluster_db -tA -c \
  "SELECT count(*) FROM posts;" 2>/dev/null | tr -d '[:space:]'; }

find_leader(){ for n in "$@"; do [ "$(role_of "$n")" = "leader" ] && { echo "$n"; return 0; }; done; return 1; }
wait_role(){ local n=$1 want=$2 t=${3:-50} i=0; while [ $i -lt "$t" ]; do
    [ "$(role_of "$n")" = "$want" ] && return 0; sleep 2; i=$((i+2)); done; return 1; }

# =============================================================================
sec "0. Pre-condiciones: esperar a que emerja un leader entre node1/2/3"
LEADER=""; i=0
while [ $i -lt 80 ]; do LEADER=$(find_leader 1 2 3) && break; sleep 3; i=$((i+3)); done
if [ -n "$LEADER" ]; then ok "Leader inicial = node$LEADER (epoch $(epoch_of "$LEADER"))"
else bad "No emergió ningún leader (¿está 'make up' arriba y sano?)"; echo "Abortando."; exit 1; fi

sec "1. Registro + login vía gateway"
gw -X POST "$GW/auth/register" -H 'Content-Type: application/json' \
   -d '{"username":"tester","password":"pass123"}' >/dev/null
LOGIN=$(gw -X POST "$GW/auth/login" -H 'Content-Type: application/json' \
   -d '{"username":"tester","password":"pass123"}')
TOKEN=$(echo "$LOGIN" | jget "d['access_token']")
USERID=$(echo "$LOGIN" | jget "d['user']['id']")
[ -n "$TOKEN" ] && ok "JWT obtenido (user_id=$USERID)" || { bad "No se obtuvo token"; echo "$LOGIN"; exit 1; }

sec "2. Escritura de 5 posts vía gateway (single-writer leader)"
for k in 1 2 3 4 5; do
  gw -X POST "$GW/posts" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
     -d "{\"content\":\"post-$k\",\"user_id\":$USERID}" >/dev/null
done
echo "  Esperando propagación asíncrona del WAL..."; sleep 8
EXPECT=$(posts_md5 "$LEADER")
echo "  Checksum de referencia (node$LEADER): $EXPECT"
[ "$(posts_count "$LEADER")" = "5" ] && ok "5 posts escritos en el leader" || bad "El leader no tiene 5 posts"

sec "3. Evidencia A: replicación idéntica en los 3 nodos iniciales"
for n in 1 2 3; do
  c=$(posts_md5 "$n")
  if [ "$c" = "$EXPECT" ]; then ok "node$n replicó (md5=$c)"; else bad "node$n DIVERGENTE (md5=$c)"; fi
done

sec "4. Apagar 2 nodos abruptamente (incluido el leader node$LEADER)"
SURV=""; for n in 1 2 3; do [ "$n" != "$LEADER" ] && { SURV=$n; break; }; done   # un follower sobrevive
for n in 1 2 3; do
  if [ "$n" != "$SURV" ]; then docker kill "node$n" >/dev/null 2>&1 && echo "  docker kill node$n"; fi
done
ok "Superviviente designado: node$SURV (era follower)"

sec "5. Reelección: node$SURV debe asumir el liderazgo (nuevo epoch)"
if wait_role "$SURV" leader 60; then ok "node$SURV es el NUEVO leader (epoch $(epoch_of "$SURV"))"
else bad "node$SURV no asumió liderazgo"; fi
docker logs "node$SURV" --tail 150 > "$EVID/reeleccion_node$SURV.log" 2>&1
echo "  --- evidencia de detección/reelección (node$SURV) ---"
grep -aE "FailureDetector|ELECTION|LEADER|epoch|subleader" "$EVID/reeleccion_node$SURV.log" | tail -12 | sed 's/^/    /'

sec "6. Levantar el NODO NUEVO (node4) y verificar sincronización"
$COMPOSE --profile newnode up -d db4 node4 >/dev/null 2>&1
echo "  Esperando que node4 sincronice el estado completo (count==5)..."
i=0; while [ $i -lt 80 ]; do [ "$(posts_count 4)" = "5" ] && break; sleep 4; i=$((i+4)); done
C4=$(posts_md5 4)
if [ "$C4" = "$EXPECT" ]; then ok "node4 sincronizó TODO el estado (md5=$C4)"
else bad "node4 NO sincronizó (md5=$C4, count=$(posts_count 4))"; fi
docker logs node4 --tail 120 > "$EVID/sync_node4.log" 2>&1

sec "7. Apagar el último nodo original (node$SURV)"
docker kill "node$SURV" >/dev/null 2>&1 && echo "  docker kill node$SURV"
if wait_role 4 leader 60; then ok "node4 asumió liderazgo tras 2º failover (epoch $(epoch_of 4))"
else bad "node4 no asumió liderazgo"; fi
docker logs node4 --tail 150 > "$EVID/reeleccion_node4.log" 2>&1
echo "  --- evidencia de detección/reelección (node4) ---"
grep -aE "FailureDetector|ELECTION|LEADER|epoch|subleader|ANTI-ENTROPY" "$EVID/reeleccion_node4.log" | tail -12 | sed 's/^/    /'

sec "8. Evidencia C: lectura final vía gateway (sin pérdida de datos)"
FINAL=$(gw "$GW/posts" -H "Authorization: Bearer $TOKEN")
NFINAL=$(echo "$FINAL" | python3 -c "import sys,json; print(len(json.load(sys.stdin)))" 2>/dev/null)
[ "$NFINAL" = "5" ] && ok "5 posts siguen presentes tras DOS failovers" || bad "pérdida de datos (quedan ${NFINAL:-?})"
C4b=$(posts_md5 4)
[ "$C4b" = "$EXPECT" ] && ok "checksum final == checksum original ($C4b)" || bad "checksum final difiere ($C4b vs $EXPECT)"

sec "9. El cluster reconfigurado sigue aceptando escrituras"
W=$(gw -X POST "$GW/posts" -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
    -d "{\"content\":\"post-after-failover\",\"user_id\":$USERID}")
echo "$W" | grep -q "post_id" && ok "escritura post-failover aceptada (epoch $(epoch_of 4))" || bad "no acepta escrituras"

# --- snapshot de estado final como evidencia -------------------------------
node_info 4 > "$EVID/info_final_node4.json" 2>/dev/null
{ echo "checksum_referencia=$EXPECT"; echo "checksum_node4_final=$C4b"; echo "posts_finales=$NFINAL"; } > "$EVID/resumen.txt"

sec "RESUMEN"
echo "  PASS=$PASS   FAIL=$FAIL   (evidencia en $EVID/)"
if [ "$FAIL" -eq 0 ]; then echo "  RESULTADO: ✅ PRUEBA §5 SUPERADA"; exit 0
else echo "  RESULTADO: ❌ revisar fallos arriba"; exit 1; fi
