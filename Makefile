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

# Makefile pour le projet
REPLICAS ?= 3

# # Détecter l'OS
# OS := $(shell uname -s)

# .PHONY: up scale down run-Controller

# # Build des images Docker
# up:
# 	@echo "Démarrage de Docker-Compose avec ${REPLICAS} Worker-Replikaten..."
# ifeq ($(OS),Linux)
# 	@docker-compose build
# 	@docker-compose up -d --scale worker=${REPLICAS}
# else
# 	@set WORKER_COUNT=${REPLICAS} && docker-compose build
# 	@set WORKER_COUNT=${REPLICAS} && docker-compose up -d --scale worker=${REPLICAS}
# endif

# down:
# 	@echo "Arrêt et suppression de l'environnement Docker-Compose..."
# ifeq ($(OS),Linux)
# 	@docker-compose down
# else
# 	@set WORKER_COUNT=${REPLICAS} && docker-compose down
# endif

# scale:
# 	@echo "Mise à l'échelle de la quantité de Workers à ${REPLICAS}..."
# ifeq ($(OS),Linux)
# 	@docker-compose up -d --scale worker=${REPLICAS}
# else
# 	@set WORKER_COUNT=${REPLICAS} && docker-compose up -d --scale worker=${REPLICAS}
# endif

# run-Controller:
# 	@echo "Exécution du Controller..."
# ifeq ($(OS),Linux)
# 	@docker-compose exec controller python3 controller.py
# else
# 	@docker-compose exec controller python controller.py
# endif