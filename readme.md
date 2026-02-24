# 🧠 Distributed DB Cluster + Auth Service (Manual, Docker-based)

Este proyecto implementa un **cluster de base de datos distribuido** con:

- Elección de líder (Bully)
- Heartbeats y detección de fallos
- Replicación manual mediante **Write-Ahead Log (WAL lógico)**
- Sincronización inicial de followers
- Servicios (`auth`, `user`, `post`) desacoplados del cluster DB

Actualmente el foco está en:
✅ Cluster DB  
✅ Integración con Auth  
❌ Replicación entre servicios (fase futura)

---

## 📁 Estructura del proyecto (simplificada)

---

## 1️⃣ Crear la red Docker (OBLIGATORIO)

Todos los contenedores **deben** estar en la misma red.

```bash
docker network create --driver overlay --attachable  cluster_net

```

## 1️⃣ Levantar los nodos de base de datos Postgres

Uno por cada nodo levantado
Cambiar --name :db2-postgress ,...

```bash
docker run  -d \
            --name db1-postgres \
            --network cluster_net \
            -e POSTGRES_USER=admin \
            -e POSTGRES_PASSWORD=secret \
            -e POSTGRES_DB=cluster_db \
            -v db1_data:/var/lib/postgresql/data \
            postgres:14


```

## 3️⃣ Build de la imagen del nodo de cluster DB

Desde Backend/Node

```bash
docker build -f Dockerfile.version1 -t  db_cluster_node .

```

## 4️⃣ Levantar los nodos del cluster DB (control + lógica)

A cada nodo le correspode un POSTGRES_HOST

Node 1:

```bash
docker run  -d \
            --name node1 \
            --hostname node1.cluster_net\
            --network cluster_net \
            --network-alias cluster_net_serv \
            -v "$(pwd)/deploy_certs/node_1:/app/certs" \
            -e NODE_ID=1 \
            -e NODE_PORT=5000 \
            -e POSTGRES_HOST=db1-postgres \
            -e SERVICE_NAME=cl_service   db_cluster_node

```

Node 2:

```bash
docker run   -d  \
            --name node2 \
            --hostname node2.cluster_net \
            --network cluster_net  \
            --network-alias cluster_net_serv \
            -v "$(pwd)/deploy_certs/node_2:/app/certs" \
            -e NODE_ID=2 \
            -e NODE_PORT=5000 \
            -e POSTGRES_HOST=db2-postgres \
            -e SERVICE_NAME=cl_service   db_cluster_node

```

Node 3 : similar

## 5️⃣ Verificar estado del cluster

```bash
docker logs -f node1
docker logs -f node2
docker logs -f node3


```

## 6 Levantar servico de auth

En backend/services/auth

```bash
docker build -f ./services/Dockerfile -t api_services

```

```bash
docker run  -d  \
            --name api_services \
            --hostname node4.cluster_net \
            --network cluster_net \
            -v "$(pwd)/deploy_certs/node_4:/app/certs" \
            -p 8080: 8080  \
            -e JWT_SECRET_KEY=supersecretkey   api_services

```
