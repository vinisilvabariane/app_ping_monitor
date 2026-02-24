import platform
import re
import socket
import subprocess
from typing import Optional


try:
    import ping3
except Exception:
    ping3 = None


class PingService:
    def __init__(self, timeout_seconds: float = 1.0):
        self.timeout_seconds = timeout_seconds

    def ping_ms(self, host: str) -> Optional[float]:
        resolved = self._resolve(host)
        if not resolved:
            return None

        if ping3 is not None:
            try:
                result = ping3.ping(resolved, timeout=self.timeout_seconds)
                if result is None:
                    return None
                return result * 1000
            except Exception:
                pass

        return self._ping_via_system_command(resolved)

    def _resolve(self, host: str) -> Optional[str]:
        try:
            return socket.gethostbyname(host)
        except Exception:
            return None

    def _ping_via_system_command(self, host: str) -> Optional[float]:
        timeout_ms = max(int(self.timeout_seconds * 1000), 100)
        if platform.system().lower().startswith("win"):
            cmd = ["ping", "-n", "1", "-w", str(timeout_ms), host]
        else:
            timeout_s = max(int(self.timeout_seconds), 1)
            cmd = ["ping", "-c", "1", "-W", str(timeout_s), host]

        try:
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=self.timeout_seconds + 2)
            if proc.returncode != 0:
                return None
            output = proc.stdout
            match = re.search(r"time[=<]\s*(\d+(?:[\.,]\d+)?)\s*ms", output, re.IGNORECASE)
            if not match:
                return None
            return float(match.group(1).replace(",", "."))
        except Exception:
            return None
