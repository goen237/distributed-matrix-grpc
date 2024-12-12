# Makefile for the project
workers ?= 3

.PHONY: up scale down run-Controller

# Build des images Docker
start:
	@echo "Démarrage de Docker-Compose avec ${workers} Worker-Replikaten..."
	@set "WORKER_COUNT=${workers}" && docker-compose build
	@set "WORKER_COUNT=${workers}" && docker-compose up -d --scale worker=${workers}

down:
	@echo "Stoppe und entferne Docker-Compose-Umgebung..."
	@set "WORKER_COUNT=${workers}" && docker-compose down

scale:
	@echo "Skaliere die Anzahl der Worker auf ${workers}..."
	@set "WORKER_COUNT=${workers}" && docker-compose up -d --scale worker=${workers}

run-Controller:
	@echo "Führe Controller aus..."
	@docker-compose exec controller python3 controller.py

# Makefile pour le projet
workers ?= 3

# # Détecter l'OS
# OS := $(shell uname -s)

# .PHONY: up scale down run-Controller

# # Build des images Docker
# up:
# 	@echo "Démarrage de Docker-Compose avec ${workers} Worker-Replikaten..."
# ifeq ($(OS),Linux)
# 	@docker-compose build
# 	@docker-compose up -d --scale worker=${workers}
# else
# 	@set WORKER_COUNT=${workers} && docker-compose build
# 	@set WORKER_COUNT=${workers} && docker-compose up -d --scale worker=${workers}
# endif

# down:
# 	@echo "Arrêt et suppression de l'environnement Docker-Compose..."
# ifeq ($(OS),Linux)
# 	@docker-compose down
# else
# 	@set WORKER_COUNT=${workers} && docker-compose down
# endif

# scale:
# 	@echo "Mise à l'échelle de la quantité de Workers à ${workers}..."
# ifeq ($(OS),Linux)
# 	@docker-compose up -d --scale worker=${workers}
# else
# 	@set WORKER_COUNT=${workers} && docker-compose up -d --scale worker=${workers}
# endif

# run-Controller:
# 	@echo "Exécution du Controller..."
# ifeq ($(OS),Linux)
# 	@docker-compose exec controller python3 controller.py
# else
# 	@docker-compose exec controller python controller.py
# endif