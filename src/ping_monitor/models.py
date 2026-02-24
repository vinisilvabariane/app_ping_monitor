from dataclasses import dataclass


@dataclass
class DeviceState:
    host: str
    status: str = "UNKNOWN"
    latency_ms: str = "-"
    changed_at: str = "-"
    down_notified: bool = False
