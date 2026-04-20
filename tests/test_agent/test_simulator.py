import uuid
import asyncio

import pytest

from agent.simulator import LibvirtSimulator


@pytest.mark.asyncio
async def test_simulator_create_vm():
    sim = LibvirtSimulator()
    vm_id = uuid.uuid4()
    host = await sim.create_vm(vm_id, "test", 1, 1024, "base.qcow2")
    assert host.startswith("agent-")
    assert vm_id in sim._vms


@pytest.mark.asyncio
async def test_simulator_power_actions():
    sim = LibvirtSimulator()
    vm_id = uuid.uuid4()
    await sim.create_vm(vm_id, "test", 1, 1024, "base.qcow2")
    await sim.power_action(vm_id, "start")
    assert sim._vms[vm_id]["state"] == "running"
    await sim.power_action(vm_id, "stop")
    assert sim._vms[vm_id]["state"] == "stopped"