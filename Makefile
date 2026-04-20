.PHONY: help up down build test test-unit test-integration logs clean

help:
	@echo "Available commands:"
	@echo "  make up           - Start all services"
	@echo "  make down         - Stop all services"
	@echo "  make build        - Build Docker images"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests"
	@echo "  make test-integration - Run integration tests"
	@echo "  make logs         - Tail logs"
	@echo "  make clean        - Remove containers, volumes, images"

up:
	docker-compose up -d

down:
	docker-compose down

build:
	docker-compose build

test:
	docker-compose run --rm api pytest

test-unit:
	docker-compose run --rm api pytest tests/test_api tests/test_agent

test-integration:
	docker-compose run --rm api pytest tests/integration

logs:
	docker-compose logs -f

clean:
	docker-compose down -v --rmi local