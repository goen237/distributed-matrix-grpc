# Makefile for the project
REPLICAS ?= 3

.PHONY: up scale down run-Controller

# Build des images Docker
build:
	docker-compose build

up:
	docker-compose build
	export WORKER_COUNT=$(REPLICAS)

up:
	docker-compose up -d --scale worker=$(REPLICAS)

down:
	docker-compose down

scale:
	docker-compose up -d --scale worker=$(REPLICAS)

run-Controller:
	docker-compose exec controller python3 controller.py