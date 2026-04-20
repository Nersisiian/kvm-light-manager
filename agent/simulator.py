import asyncio
import logging
import os
import random
import time
import uuid
from typing import Dict

logger = logging.getLogger(__name__)


class LibvirtSimulator:
    def __init__(self):
        self._vms: Dict[uuid.UUID, Dict] = {}
        self._host_id = os.environ.get("HOSTNAME", "agent-01")
        self._error_rate = float(os.environ.get("SIM_ERROR_RATE", "0.05"))

    async def create_vm(
        self,
        vm_id: uuid.UUID,
        name: str,
        cpu: int,
        ram: int,
        base_image: str,
    ) -> str:
        logger.info(f"Creating VM {vm_id} ({name}) with {cpu} CPUs, {ram} MB RAM")
        if random.random() < self._error_rate:
            raise RuntimeError("Simulated disk I/O error during cloning")

        await asyncio.to_thread(self._blocking_clone_disk, base_image, vm_id)
        await asyncio.to_thread(self._blocking_define_vm, vm_id, cpu, ram)
        self._vms[vm_id] = {
            "name": name,
            "cpu": cpu,
            "ram": ram,
            "base_image": base_image,
            "state": "defined",
        }
        return self._host_id

    def _blocking_clone_disk(self, base_image: str, vm_id: uuid.UUID):
        logger.debug(f"Cloning disk from {base_image} for VM {vm_id}")
        time.sleep(random.uniform(1.5, 3.0))

    def _blocking_define_vm(self, vm_id: uuid.UUID, cpu: int, ram: int):
        logger.debug(f"Defining VM {vm_id}")
        time.sleep(random.uniform(0.5, 1.5))

    async def power_action(self, vm_id: uuid.UUID, action: str):
        if vm_id not in self._vms:
            raise ValueError(f"VM {vm_id} not found")

        if random.random() < self._error_rate:
            raise RuntimeError(f"Simulated failure: VM {vm_id} unresponsive")

        logger.info(f"Power action {action} on VM {vm_id}")
        if action == "start":
            await asyncio.to_thread(self._blocking_start_vm, vm_id)
            self._vms[vm_id]["state"] = "running"
        elif action == "stop":
            await asyncio.to_thread(self._blocking_stop_vm, vm_id)
            self._vms[vm_id]["state"] = "stopped"
        elif action == "reboot":
            await asyncio.to_thread(self._blocking_reboot_vm, vm_id)
            self._vms[vm_id]["state"] = "running"

    def _blocking_start_vm(self, vm_id: uuid.UUID):
        time.sleep(1)

    def _blocking_stop_vm(self, vm_id: uuid.UUID):
        time.sleep(1)

    def _blocking_reboot_vm(self, vm_id: uuid.UUID):
        time.sleep(2)

    async def delete_vm(self, vm_id: uuid.UUID):
        if vm_id not in self._vms:
            raise ValueError(f"VM {vm_id} not found")

        if random.random() < self._error_rate:
            raise RuntimeError(f"Simulated failure: could not delete VM {vm_id}")

        logger.info(f"Deleting VM {vm_id}")
        await asyncio.to_thread(self._blocking_delete_vm, vm_id)
        del self._vms[vm_id]

    def _blocking_delete_vm(self, vm_id: uuid.UUID):
        time.sleep(random.uniform(1.0, 2.0))