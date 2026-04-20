"""
Contract tests for Agent communication protocol.

These tests ensure that the API contract between the API Gateway and Agent service
remains stable. They verify request/response serialization, error handling,
and expected behavior for each action.
"""

import json
import uuid
from typing import Any, Dict

import pytest
from pydantic import ValidationError

from app.messaging.schemas import AgentRequest, AgentResponse, ProvisionRequest
from agent.handlers import handle_request
from agent.simulator import LibvirtSimulator


class TestAgentContract:
    """Test suite for Agent message contract."""

    # ------------------------------------------------------------------
    # Request serialization / deserialization
    # ------------------------------------------------------------------

    def test_agent_request_serialization(self) -> None:
        """AgentRequest should serialize to JSON bytes correctly."""
        request = AgentRequest(
            action="provision",
            payload={"vm_id": str(uuid.uuid4()), "name": "test", "cpu": 2, "ram": 2048},
            request_id="abc-123",
        )
        json_bytes = request.to_json()
        assert isinstance(json_bytes, bytes)
        # Verify it can be parsed back
        data = json.loads(json_bytes.decode())
        assert data["action"] == "provision"
        assert data["request_id"] == "abc-123"
        assert data["payload"]["cpu"] == 2

    def test_agent_request_deserialization(self) -> None:
        """Bytes should be correctly deserialized into AgentRequest."""
        payload = {
            "action": "start",
            "payload": {"vm_id": str(uuid.uuid4())},
            "request_id": "req-456",
        }
        json_bytes = json.dumps(payload).encode()
        request = AgentRequest.model_validate_json(json_bytes.decode())
        assert request.action == "start"
        assert request.request_id == "req-456"
        assert request.payload["vm_id"] is not None

    def test_agent_request_missing_required_field(self) -> None:
        """Missing required fields should raise ValidationError."""
        invalid_data = {"payload": {}}  # missing 'action'
        json_bytes = json.dumps(invalid_data).encode()
        with pytest.raises(ValidationError):
            AgentRequest.model_validate_json(json_bytes.decode())

    # ------------------------------------------------------------------
    # Response serialization / deserialization
    # ------------------------------------------------------------------

    def test_agent_response_success_serialization(self) -> None:
        """Success response should serialize to JSON and back."""
        response = AgentResponse(
            request_id="req-789",
            status="success",
            data={"host": "agent-01", "vm_id": str(uuid.uuid4())},
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "success"
        assert parsed["data"]["host"] == "agent-01"

        # Round-trip
        reconstructed = AgentResponse.model_validate_json(json_str)
        assert reconstructed.status == "success"
        assert reconstructed.data is not None

    def test_agent_response_error_serialization(self) -> None:
        """Error response should include error field."""
        response = AgentResponse(
            request_id="req-error",
            status="error",
            error="Something went wrong",
        )
        json_str = response.model_dump_json()
        parsed = json.loads(json_str)
        assert parsed["status"] == "error"
        assert parsed["error"] == "Something went wrong"
        assert parsed["data"] is None

    # ------------------------------------------------------------------
    # Contract: action "ping"
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_ping_action_contract(self) -> None:
        """Ping action should return success with host information."""
        request = AgentRequest(action="ping", payload={}, request_id="ping-001")
        response = await handle_request(request.to_json())
        assert response.status == "success"
        assert response.data is not None
        assert "host" in response.data
        assert response.error is None

    # ------------------------------------------------------------------
    # Contract: action "provision"
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_provision_action_success_contract(self, monkeypatch) -> None:
        """Provision action should accept expected payload and return host."""
        vm_id = uuid.uuid4()
        request = AgentRequest(
            action="provision",
            payload={
                "vm_id": str(vm_id),
                "name": "test-vm",
                "cpu": 4,
                "ram": 8192,
                "base_image": "ubuntu-22.04-cloudimg",
            },
            request_id="prov-001",
        )

        # Mock simulator to avoid real blocking calls
        async def mock_create_vm(*args, **kwargs):
            return "mock-agent-host"

        monkeypatch.setattr(LibvirtSimulator, "create_vm", mock_create_vm)

        response = await handle_request(request.to_json())
        assert response.status == "success"
        assert response.data is not None
        assert response.data.get("vm_id") == str(vm_id)
        assert response.data.get("host") == "mock-agent-host"

    @pytest.mark.asyncio
    async def test_provision_action_missing_fields_contract(self) -> None:
        """Provision with missing required fields should return error."""
        request = AgentRequest(
            action="provision",
            payload={
                "name": "test-vm",
                "cpu": 4,
                # missing ram and vm_id
            },
            request_id="prov-002",
        )
        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "Missing required fields" in response.error

    @pytest.mark.asyncio
    async def test_provision_action_simulated_failure_contract(self, monkeypatch) -> None:
        """When simulator raises exception, response should be error."""
        vm_id = uuid.uuid4()
        request = AgentRequest(
            action="provision",
            payload={
                "vm_id": str(vm_id),
                "name": "test-vm",
                "cpu": 2,
                "ram": 2048,
            },
            request_id="prov-003",
        )

        async def mock_create_vm_error(*args, **kwargs):
            raise RuntimeError("Simulated disk failure")

        monkeypatch.setattr(LibvirtSimulator, "create_vm", mock_create_vm_error)

        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "Simulated disk failure" in response.error

    # ------------------------------------------------------------------
    # Contract: power actions (start/stop/reboot)
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    @pytest.mark.parametrize("action", ["start", "stop", "reboot"])
    async def test_power_actions_success_contract(self, action: str, monkeypatch) -> None:
        """Power actions should accept vm_id and return success."""
        vm_id = uuid.uuid4()
        # Pre-populate simulator with VM
        monkeypatch.setattr(
            LibvirtSimulator,
            "_vms",
            {vm_id: {"name": "test", "state": "defined"}},
            raising=False,
        )

        request = AgentRequest(
            action=action,
            payload={"vm_id": str(vm_id)},
            request_id=f"power-{action}-001",
        )

        async def mock_power_action(*args, **kwargs):
            return None

        monkeypatch.setattr(LibvirtSimulator, "power_action", mock_power_action)

        response = await handle_request(request.to_json())
        assert response.status == "success"
        assert response.data is not None
        assert response.data.get("vm_id") == str(vm_id)
        assert response.data.get("action") == action

    @pytest.mark.asyncio
    async def test_power_action_missing_vm_id_contract(self) -> None:
        """Power action without vm_id should return error."""
        request = AgentRequest(
            action="start",
            payload={},
            request_id="power-002",
        )
        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "Missing vm_id" in response.error

    @pytest.mark.asyncio
    async def test_power_action_vm_not_found_contract(self, monkeypatch) -> None:
        """Power action for non-existent VM should return error."""
        request = AgentRequest(
            action="start",
            payload={"vm_id": str(uuid.uuid4())},
            request_id="power-003",
        )
        # Simulator has no VMs by default
        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "not found" in response.error.lower()

    # ------------------------------------------------------------------
    # Contract: action "delete"
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_delete_action_success_contract(self, monkeypatch) -> None:
        """Delete action should succeed when VM exists."""
        vm_id = uuid.uuid4()
        monkeypatch.setattr(
            LibvirtSimulator,
            "_vms",
            {vm_id: {"name": "test"}},
            raising=False,
        )

        async def mock_delete_vm(*args, **kwargs):
            return None

        monkeypatch.setattr(LibvirtSimulator, "delete_vm", mock_delete_vm)

        request = AgentRequest(
            action="delete",
            payload={"vm_id": str(vm_id)},
            request_id="delete-001",
        )
        response = await handle_request(request.to_json())
        assert response.status == "success"
        assert response.data.get("vm_id") == str(vm_id)

    @pytest.mark.asyncio
    async def test_delete_action_missing_vm_id_contract(self) -> None:
        """Delete without vm_id should return error."""
        request = AgentRequest(
            action="delete",
            payload={},
            request_id="delete-002",
        )
        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "Missing vm_id" in response.error

    # ------------------------------------------------------------------
    # Contract: unknown action
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_unknown_action_contract(self) -> None:
        """Unknown action should return error with appropriate message."""
        request = AgentRequest(
            action="unknown_action",
            payload={},
            request_id="unknown-001",
        )
        response = await handle_request(request.to_json())
        assert response.status == "error"
        assert "Unknown action" in response.error

    # ------------------------------------------------------------------
    # Contract: malformed JSON
    # ------------------------------------------------------------------

    @pytest.mark.asyncio
    async def test_malformed_json_contract(self) -> None:
        """Malformed JSON bytes should result in error response."""
        malformed_bytes = b'{"action": "ping", "payload": {}'  # missing closing brace
        response = await handle_request(malformed_bytes)
        assert response.status == "error"
        assert response.request_id == "unknown"
        assert "Invalid request" in response.error