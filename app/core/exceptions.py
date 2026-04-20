class KVMError(Exception):
    pass


class AgentUnavailableError(KVMError):
    pass


class AgentTimeoutError(KVMError):
    pass


class VMNotFoundError(KVMError):
    pass


class VMOperationError(KVMError):
    pass


class CircuitBreakerOpenError(KVMError):
    pass