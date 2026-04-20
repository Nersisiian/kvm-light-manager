# KVM Light Manager API Reference

**Version:** 2.0.0  
**Base URL:** http://localhost:8000/api/v1

All endpoints return JSON. Timestamps are in ISO 8601 format.

## Authentication

If KVM_API_KEY_ENABLED=true, include the API key in the header:

X-API-Key: your-secret-key

## Endpoints

### Virtual Machines

#### POST /vms

Create a new virtual machine. The operation is asynchronous – a 	ask_id is returned for tracking progress via WebSocket.

**Request Body:**

`json
{
  "name": "web-server-01",
  "cpu": 4,
  "ram": 8192,
  "base_image": "ubuntu-22.04-cloudimg"
}

FieldTypeConstraintsDescription
namestring1–255 charsVM display name
cpuinteger1–64Number of vCPUs
raminteger512–262144Memory in MB
base_imagestringoptionalBase image name (default: ubuntu-22.04-cloudimg)
Response: 202 Accepted
{
  "vm_id": "550e8400-e29b-41d4-a716-446655440000",
  "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "status": "provisioning"
}
GET /vms/{vm_id}/status
Retrieve current VM status and details.

Response: 200 OK
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "web-server-01",
  "status": "running",
  "cpu": 4,
  "ram": 8192,
  "host": "agent-01",
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
Possible status values: pending, provisioning, running, stopped, error, deleted.

DELETE /vms/{vm_id}
Delete a VM permanently. This also cleans up associated logs and disk images.

Response: 204 No Content

POST /vms/{vm_id}/power
Send a power action to the VM.

Request Body:
{
  "action": "start"
}
action must be one of: start, stop, reboot.

Response: 200 OK (returns updated VM object, same as GET status)

WebSocket
WS /ws/logs/{vm_id}
Stream real‑time provisioning logs for a VM.

Connection: WebSocket

Messages: JSON objects streamed as text:
{
  "timestamp": "2024-01-15T10:30:01Z",
  "task_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
  "level": "info",
  "message": "Cloning disk from ubuntu-22.04-cloudimg"
}
Health & Metrics
GET /health/live
Kubernetes liveness probe. Returns {"status":"ok"} if the process is alive.

GET /health/ready
Kubernetes readiness probe. Checks database, Redis, and agent connectivity.

Response:
{
  "status": "ok",
  "details": {
    "database": "ok",
    "redis": "ok",
    "agent": "ok"
  }
}
If any component is unhealthy, status becomes degraded and the failing component includes an error message.

GET /health/status
Extended status for monitoring dashboards. Includes database pool statistics and service version.

GET /metrics
Prometheus‑compatible metrics endpoint (if KVM_METRICS_ENABLED=true).

Error Responses
All error responses follow this structure:
{
  "detail": "Human readable error message",
  "error_code": "VM_NOT_FOUND",
  "extra": {}
}
Common HTTP status codes:

400 – Bad request (validation error)

401 – Unauthorized (invalid API key)

404 – Resource not found

500 – Internal server error

503 – Service unavailable (circuit breaker open, agent down)
Example Usage (curl)
# Create a VM
curl -X POST http://localhost:8000/api/v1/vms \
  -H "Content-Type: application/json" \
  -d '{"name":"my-vm","cpu":2,"ram":4096}'

# Check status
curl http://localhost:8000/api/v1/vms/550e8400-e29b-41d4-a716-446655440000/status

# Start VM
curl -X POST http://localhost:8000/api/v1/vms/550e8400-e29b-41d4-a716-446655440000/power \
  -H "Content-Type: application/json" \
  -d '{"action":"start"}'

# Stream logs (using websocat)
websocat ws://localhost:8000/api/v1/ws/logs/550e8400-e29b-41d4-a716-446655440000

# Delete VM
curl -X DELETE http://localhost:8000/api/v1/vms/550e8400-e29b-41d4-a716-446655440000
