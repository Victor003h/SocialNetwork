# =============================================================================
# Orquestación de un comando del cluster distribuido (rúbrica §3).
#   make up        -> genera certs si faltan, construye imágenes y levanta 3 nodos + gateway + web
#   make add-node  -> levanta el "nodo nuevo" (node4) de la prueba §5
#   make kill-node N=2  -> apaga abruptamente un nodo (docker kill)
#   make test      -> ejecuta el protocolo de tolerancia §5 con evidencia
#   make logs / make ps / make down
# =============================================================================

COMPOSE := docker compose -f docker-compose.cluster.yml
CERT_DIR := backend/deploy_certs

.PHONY: up build add-node down logs ps certs test kill-node start-node health

## Levanta el sistema completo (3 nodos de estado + gateway + frontend)
up: certs
	$(COMPOSE) up -d --build node1 node2 node3 api_services frontend
	@echo ""
	@echo ">> Cluster levantándose. Verifica salud con:  make health"
	@echo ">> Frontend:  http://localhost:8080     Gateway:  https://localhost:7000"

build: certs
	$(COMPOSE) build

## Genera el kit de seguridad (CA + certs por nodo) solo si no existe.
certs:
	@if [ ! -f "$(CERT_DIR)/ca.crt" ]; then \
		echo ">> Generando CA y certificados mTLS en $(CERT_DIR) ..."; \
		docker run --rm -v "$(PWD)/backend:/work" -w /work python:3.11-slim \
			sh -c "pip install --quiet cryptography && python security/setup_Security.py"; \
	else \
		echo ">> Certificados ya presentes en $(CERT_DIR) (omito generación)."; \
	fi

## Levanta el nodo nuevo de la prueba §5 (perfil 'newnode').
add-node:
	$(COMPOSE) --profile newnode up -d db4 node4

## Apaga abruptamente un nodo:  make kill-node N=2
kill-node:
	docker kill node$(N)

## Reinicia/levanta un nodo concreto:  make start-node N=1
start-node:
	$(COMPOSE) up -d node$(N)

## Muestra el estado de salud de todos los nodos.
health:
	@$(COMPOSE) ps

ps:
	@$(COMPOSE) --profile newnode ps

logs:
	$(COMPOSE) logs -f --tail=80

## Ejecuta el protocolo obligatorio de tolerancia §5.
test:
	./pruebas/test_tolerancia.sh

## Derriba todo y borra volúmenes (estado limpio).
down:
	$(COMPOSE) --profile newnode down -v
