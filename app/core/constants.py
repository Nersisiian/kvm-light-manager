from enum import Enum


class VMStatus(str, Enum):
    PENDING = "pending"
    PROVISIONING = "provisioning"
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    DELETED = "deleted"


class PowerAction(str, Enum):
    START = "start"
    STOP = "stop"
    REBOOT = "reboot"