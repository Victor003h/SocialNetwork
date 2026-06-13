# 🧠 Red Social sobre Cluster de Base de Datos Distribuido

Red social desplegada sobre un **cluster de base de datos distribuido jerárquico**, tolerante a
fallos, con replicación por **Write-Ahead Log (WAL) lógico**, elección de líder **Bully de dos
niveles**, comunicación segura **mTLS** y despliegue reproducible de **un comando** sobre **dos
redes Docker**.

> Informe técnico completo: [`informe_final.md`](informe_final.md). Video: [`video_link.txt`](video_link.txt).

---

## Arquitectura (resumen)

```
 navegador ──HTTPS──▶ frontend ──┐
                                 ├─ edge_net (expuesta: 8080 web, 7000 api)
            api_gateway ◀────────┘
                 │  mTLS
                 ▼
   ┌─────────── cluster_net (interna, AISLADA) ───────────┐
   │  node1 ── node2 ── node3   (subleader → leader global)│
   │   │db1     │db2     │db3                              │
   └──────────────────────────────────────────────────────┘
```

- **Roles**: cada nodo es `follower`, `subleader` (líder de su PC) o `leader` (líder global entre
  subleaders). En un despliegue de un PC, el subleader es además el leader global.
- **Escrituras**: single-writer en el leader; se propagan por WAL `(epoch, lsn)` a los followers
  (y, en multi-PC, a los demás subleaders). Modelo de **consistencia eventual** con prevención de
  split-brain por **epoch + quórum**.
- **El api_gateway** dirige todo al **subleader** de su grupo, que sirve lecturas y reenvía
  escrituras al leader. El subleader vigente se anuncia al gateway (push) en cada (re)elección.

---

## Requisitos

- Docker + Docker Compose v2 (`docker compose`).
- `make`.

No hace falta nada más: los certificados mTLS se generan automáticamente la primera vez.

---

## Ejecución (un comando)

```bash
make up        # genera certs si faltan, construye imágenes y levanta 3 nodos + gateway + web
make health    # estado de los contenedores
```

- Frontend:  http://localhost:8080
- API Gateway:  https://localhost:7000  *(certificado self-signed)*

> Nota: el cluster tarda ~10 s en converger a **1 leader + 2 followers** tras `make up`.

### Otros comandos

```bash
make add-node          # levanta el "nodo nuevo" (node4) para la prueba §5
make kill-node N=2     # apaga abruptamente un nodo (docker kill)
make start-node N=2    # vuelve a levantar un nodo
make logs              # logs en vivo
make down              # derriba todo y borra volúmenes (estado limpio)
```

---

## Prueba obligatoria de tolerancia (§5)

Ejecuta el escenario **3 nodos ↑ → apagar 2 (incluido el leader) → 1 nodo nuevo ↑ → apagar el
último original**, con verificación por **checksums de Postgres**, roles/epoch vía `/info` y logs
de reelección:

```bash
make test
```

Genera evidencia en [`pruebas/evidence/`](pruebas/evidence/) (reelección, sync del nodo nuevo,
checksums, resumen). Resultado esperado: `✅ PRUEBA §5 SUPERADA` (`FAIL=0`).

---

## Estructura

```
backend/Nodes/        # nodo del cluster (estado + control): cluster, WAL, heartbeats, elección
backend/services/     # api_gateway (stateless) que encapsula los endpoints para el frontend
backend/security/     # CA + certificados mTLS (setup_Security.py, CertManager)
Frontend/             # web app
docker-compose.cluster.yml   # 2 redes, 3 nodos + Postgres, gateway, frontend
Makefile              # orquestación de un comando
pruebas/              # test_tolerancia.sh (§5) + evidencia
informe_final.md      # informe técnico de 8 secciones
```
