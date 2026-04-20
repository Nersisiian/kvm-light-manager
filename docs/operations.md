# Operations Manual

This document provides guidance for operating the KVM Light Manager service in production.

## Configuration

All configuration is done via environment variables prefixed with `KVM_`. See `.env.example` for a complete list. Critical variables:

| Variable | Description | Example |
|----------|-------------|---------|
| `KVM_POSTGRES_HOST` | PostgreSQL host | `postgres.prod.svc.cluster.local` |
| `KVM_REDIS_HOST` | Redis host | `redis.prod.svc.cluster.local` |
| `KVM_AGENT_ZMQ_ENDPOINT` | ZeroMQ agent endpoint | `tcp://agent-service:5555` |
| `KVM_LOG_JSON` | Enable JSON logging | `true` |
| `KVM_METRICS_ENABLED` | Enable Prometheus metrics | `true` |

For production, **never** use the default secrets; inject them via a secure method (Kubernetes Secrets, HashiCorp Vault, etc.).

## Running with Docker Compose

```bash
# Start all services
docker-compose up -d
```
# View logs
docker-compose logs -f api
docker-compose logs -f agent
`
# Scale agents (if using a proxy)
docker-compose up -d --scale agent=3
``
# Stop everything
```
docker-compose down
``````
Running on Kubernetes
``````
Sample deployment manifests are available in k8s/ (not included). Key points:

API is stateless; scale horizontally with a Deployment and a Service.

Agents should be deployed as a separate Deployment; use a headless service for ZeroMQ connections or a dedicated ZMQ proxy.

Use livenessProbe on /health/live and readinessProbe on /health/ready.

Mount secrets as environment variables.
``````
Monitoring
Prometheus Metrics
```````
Metrics are exposed at /api/v1/metrics. Import the provided Grafana dashboard (monitoring/grafana-dashboard.json) for a pre‑built view.

Key metrics:

http_requests_total – Request count by method, endpoint, and status.

http_request_duration_seconds – Latency histogram.

Database pool statistics via /health/status.
````````
Logging
````````
Structured JSON logs are written to stdout. Use a log aggregator (ELK, Loki) to collect and index them. The correlation_id field ties together logs from a single client request.
````````
Health Checks
````````
/health/live – Returns 200 if the process is running.

/health/ready – Returns 200 if all dependencies (DB, Redis, Agent) are reachable; otherwise 503.

/health/status – Detailed component status (useful for dashboards).
````````
Handling Agent Failures
`````````
The API uses a circuit breaker to prevent flooding a failing agent with requests. After KVM_CIRCUIT_BREAKER_FAILURE_THRESHOLD consecutive failures, the circuit opens. During this time, any request requiring the agent will immediately fail with a 503 Service Unavailable.

The circuit transitions to half‑open after KVM_CIRCUIT_BREAKER_RECOVERY_TIMEOUT seconds, allowing one test request. If it succeeds, the circuit closes; otherwise it reopens.

To recover:

Investigate agent logs.

Restart the agent pod/container.

The circuit will automatically test the connection and close if healthy.
`````````
Database Maintenance
`````````
Migrations: Run alembic upgrade head as part of deployment (the Docker entrypoint already does this).

Backups: Use standard PostgreSQL backup tools (pg_dump).

Connection Pool: Tune KVM_POSTGRES_POOL_SIZE and KVM_POSTGRES_MAX_OVERFLOW based on load.
``````````
Scaling the Agent Fleet
``````````
Currently, the API connects to a single ZeroMQ endpoint. To distribute requests among multiple agents, deploy a ZeroMQ proxy (e.g., zmq_proxy with a ROUTER‑DEALER bridge) or use a load‑balancing TCP proxy (like HAProxy) in front of the agents. The DEALER socket will then round‑robin requests to connected backends.
```````````
Troubleshooting
```````````
VM stuck in provisioning state
Check agent logs for errors.

Verify network connectivity between API and Agent.

Ensure Redis is running and accessible (logs are stored there).

Check database for VM record; if the agent failed, the status may remain provisioning. Manually update status or delete and recreate.
```````````
WebSocket connection drops immediately
```````````
Ensure the vm_id exists.

Check Redis Pub/Sub connection.

Look for WebSocket disconnected logs in API.
`````````````
Circuit breaker is open
````````````
Agent may be overloaded or crashed.

Check agent health: /health/ready on the agent's HTTP port (if exposed).

Restart agent(s).

Adjust failure threshold if the environment is unstable (not recommended).
`````````````
Performance Tuning
`````````````
Increase KVM_API_WORKERS to utilise more CPU cores.

Adjust PostgreSQL pool size to match expected concurrency.

For high provisioning rates, increase agent count and use a ZMQ proxy for load distribution.

Monitor Redis memory usage (logs are kept for 1000 entries per VM; purge old VMs regularly).
``````````````
Security Hardening
``````````````
Enable API key authentication (KVM_API_KEY_ENABLED=true) and generate strong keys.

Run containers as non‑root users (already configured in Dockerfiles).

Use network policies to restrict traffic between services.

For production ZeroMQ communication, consider enabling CURVE security (ZMQ's built‑in encryption and authentication).
