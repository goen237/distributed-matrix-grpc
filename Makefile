# Makefile for the project
REPLICAS ?= 3

.PHONY: up scale down run-Controller

# Build des images Docker
up:
	@echo "Starte Docker-Compose mit ${REPLICAS} Worker-Replikaten..."
	@set "WORKER_COUNT=${REPLICAS}" && docker-compose build
	@set "WORKER_COUNT=${REPLICAS}" && docker-compose up -d --scale worker=${REPLICAS}

down:
	@echo "Stoppe und entferne Docker-Compose-Umgebung..."
	@set "WORKER_COUNT=${REPLICAS}" && docker-compose down

scale:
	@echo "Skaliere die Anzahl der Worker auf ${REPLICAS}..."
	@set "WORKER_COUNT=${REPLICAS}" && docker-compose up -d --scale worker=${REPLICAS}

run-Controller:
	@echo "Führe Controller aus..."
	@docker-compose exec controller python3 controller.py