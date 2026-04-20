# KVM Light Manager — Production‑Grade VM Orchestration

[![CI](https://github.com/Nersisiian/kvm-light-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/Nersisiian/kvm-light-manager)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

KVM Light Manager is a fully asynchronous, horizontally scalable VM orchestration service designed for private cloud infrastructure. It provides a REST API and WebSocket interface to manage KVM/libvirt virtual machines across a fleet of hypervisor nodes.

## ✨ Features

- **Non‑blocking I/O** – Built entirely on `asyncio` for high concurrency.
- **ZeroMQ Communication** – DEALER/ROUTER pattern for reliable agent messaging.
- **Real‑time Log Streaming** – WebSocket + Redis Pub/Sub for live provisioning progress.
- **Resilience** – Circuit breaker, retries with exponential backoff, graceful shutdown.
- **Observability** – Structured JSON logging, Prometheus metrics, health checks.
- **Production‑Ready** – Containerised, configurable via environment variables, tested with testcontainers.

## 🏗 Architecture

```mermaid
graph TD
    Client -->|REST/WS| Gateway[FastAPI Gateway]
    Gateway --> DB[(PostgreSQL)]
    Gateway --> Redis[(Redis)]
    Gateway -->|ZeroMQ| Agent1[Agent Node 1]
    Gateway -->|ZeroMQ| Agent2[Agent Node 2]
    Agent1 -->|Thread Executor| Libvirt1[(libvirt Sim)]
    Agent2 -->|Thread Executor| Libvirt2[(libvirt Sim)]
    Redis --> Gateway
    Gateway --> Metrics[Metrics]

For a detailed architecture explanation, see docs/architecture.md.
```
🚀 Quick Start

Prerequisites
Docker & Docker Compose

Make (optional)

# Clone repository
git clone https://github.com/Nersisiian/kvm-light-manager.git
cd kvm-light-manager

# Copy environment template
cp .env.example .env

# Build and start all services
make build
make up

# Check logs
make logs
Services will be available:

API: http://localhost:8000

API Docs: http://localhost:8000/docs

Agent: ZeroMQ on port 5555 (internal)

PostgreSQL: localhost:5432

Redis: localhost:6379

📖 API Examples

# Create a VM
curl -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name": "web-01", "cpu": 4, "ram": 8192}'

# Check status
curl http://localhost:8000/api/v1/vms/550e8400-e29b-41d4-a716-446655440000/status

# Start VM
curl -X POST http://localhost:8000/api/v1/vms/550e8400-e29b-41d4-a716-446655440000/power \
  -H "Content-Type: application/json" \
  -d '{"action": "start"}'

# Stream logs (using websocat)
websocat ws://localhost:8000/api/v1/ws/logs/550e8400-e29b-41d4-a716-446655440000
Full API reference: docs/api_reference.md

🔧 Development
Running Locally (without Docker)
bash
pip install -e ".[dev]"
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=secret postgres:15
docker run -d -p 6379:6379 redis:7
alembic upgrade head
uvicorn app.main:app --reload
# In another terminal:
python -m agent.main
Testing
bash
# All tests (requires Docker for testcontainers)
make test

# Unit tests only
make test-unit

# Integration tests
make test-integration
📁 Project Structure

kvm-light-manager/
├── app/               # API Gateway application
│   ├── api/           # Endpoints, dependencies
│   ├── core/          # Config, logging, middleware
│   ├── db/            # Database session, repositories
│   ├── models/        # SQLAlchemy models
│   ├── schemas/       # Pydantic schemas
│   ├── services/      # Business logic, Redis, Agent client
│   └── messaging/     # ZeroMQ client, schemas
├── agent/             # Agent service (simulated hypervisor)
├── tests/             # Unit, integration, contract tests
├── alembic/           # Database migrations
├── docker/            # Docker entrypoints
├── docs/              # Extended documentation
└── scripts/           # Operational scripts

📊 Observability

Logs: JSON structured, includes correlation_id for tracing.

Metrics: Prometheus endpoint at /api/v1/metrics.

Health: /health/live, /health/ready, /health/status.

🛡 Production Readiness
Stateless API layer can scale horizontally.

Circuit breaker prevents cascading failures.

Graceful shutdown ensures no orphaned background tasks.

Comprehensive test coverage with testcontainers.

For operational guidance, see docs/operations.md.

📄 License
MIT © Your Organization
