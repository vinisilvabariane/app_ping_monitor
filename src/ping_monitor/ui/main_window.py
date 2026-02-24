import queue
import threading
import time
import tkinter as tk
from datetime import datetime
from tkinter import messagebox, simpledialog, ttk

from ping_monitor.config import EmailConfig
from ping_monitor.models import DeviceState
from ping_monitor.services.emailer import EmailAlertService
from ping_monitor.services.pinger import PingService

APP_VERSION = "4.1"
PING_INTERVAL_SECONDS = 1.5


class MainWindow:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title(f"Ping Monitor v{APP_VERSION}")
        self.root.geometry("1040x680")
        self.root.minsize(900, 560)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

        self.devices: dict[str, DeviceState] = {}
        self.queue: queue.Queue = queue.Queue()
        self.stop_event = threading.Event()
        self.monitor_thread: threading.Thread | None = None
        self.monitoring = False

        self.ping_service = PingService(timeout_seconds=1.0)
        self.email_config = EmailConfig()
        self.email_service = EmailAlertService(self.email_config)

        self.status_var = tk.StringVar(value="Stopped")
        self.count_var = tk.StringVar(value="0 device(s)")
        self.email_var = tk.StringVar(value=self._email_status_text())

        self._build_ui()
        self._poll_queue()

    def _build_ui(self) -> None:
        style = ttk.Style(self.root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Treeview", rowheight=28)
        style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

        top_bar = ttk.Frame(self.root, padding=(12, 10))
        top_bar.pack(fill="x")

        ttk.Button(top_bar, text="Add Device", command=self.add_device).pack(side="left", padx=(0, 8))
        ttk.Button(top_bar, text="Remove Selected", command=self.remove_selected).pack(side="left", padx=(0, 8))
        ttk.Separator(top_bar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(top_bar, text="Start", command=self.start_monitoring).pack(side="left", padx=(0, 8))
        ttk.Button(top_bar, text="Stop", command=self.stop_monitoring).pack(side="left", padx=(0, 8))
        ttk.Separator(top_bar, orient="vertical").pack(side="left", fill="y", padx=8)
        ttk.Button(top_bar, text="Refresh Email Config", command=self.reload_email_config).pack(side="left")

        table_frame = ttk.Frame(self.root, padding=(12, 0, 12, 8))
        table_frame.pack(fill="both", expand=True)

        columns = ("host", "status", "latency", "changed")
        self.table = ttk.Treeview(table_frame, columns=columns, show="headings", height=18)
        self.table.heading("host", text="Host/IP")
        self.table.heading("status", text="Status")
        self.table.heading("latency", text="Latency (ms)")
        self.table.heading("changed", text="Last Change")
        self.table.column("host", width=360, anchor="w")
        self.table.column("status", width=150, anchor="center")
        self.table.column("latency", width=120, anchor="center")
        self.table.column("changed", width=190, anchor="center")
        self.table.tag_configure("UP", foreground="#0b7a20")
        self.table.tag_configure("DOWN", foreground="#c62828")
        self.table.tag_configure("UNKNOWN", foreground="#555555")

        y_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.table.yview)
        self.table.configure(yscrollcommand=y_scroll.set)
        self.table.pack(side="left", fill="both", expand=True)
        y_scroll.pack(side="right", fill="y")

        log_frame = ttk.LabelFrame(self.root, text="Event Log", padding=(10, 6))
        log_frame.pack(fill="both", padx=12, pady=(0, 12))
        self.log = tk.Text(log_frame, height=8, wrap="word", state="disabled", font=("Consolas", 9))
        self.log.pack(fill="both", expand=True)

        status_bar = ttk.Frame(self.root, padding=(12, 0, 12, 10))
        status_bar.pack(fill="x")
        ttk.Label(status_bar, text="Monitor:").pack(side="left")
        ttk.Label(status_bar, textvariable=self.status_var).pack(side="left", padx=(6, 16))
        ttk.Label(status_bar, textvariable=self.count_var).pack(side="left", padx=(0, 16))
        ttk.Label(status_bar, textvariable=self.email_var).pack(side="left")
        ttk.Label(status_bar, text=f"Version {APP_VERSION}").pack(side="right")

    def add_device(self) -> None:
        raw = simpledialog.askstring("Add devices", "Enter hosts/IPs separated by comma or space:")
        if not raw:
            return

        added = 0
        for host in [item.strip() for item in raw.replace(",", " ").split()]:
            if not host or host in self.devices:
                continue
            self.devices[host] = DeviceState(host=host)
            self.table.insert("", "end", iid=host, values=(host, "UNKNOWN", "-", "-"), tags=("UNKNOWN",))
            added += 1

        self._refresh_counters()
        if added:
            self._append_log(f"Added {added} device(s).")

    def remove_selected(self) -> None:
        selection = self.table.selection()
        if not selection:
            return

        for iid in selection:
            host = str(iid)
            self.devices.pop(host, None)
            self.table.delete(iid)

        self._refresh_counters()
        self._append_log(f"Removed {len(selection)} device(s).")

    def start_monitoring(self) -> None:
        if self.monitoring:
            return
        if not self.devices:
            messagebox.showwarning("No devices", "Add at least one host/IP before starting monitor.")
            return

        self.stop_event.clear()
        self.monitor_thread = threading.Thread(target=self._monitor_loop, name="ping-monitor", daemon=True)
        self.monitor_thread.start()
        self.monitoring = True
        self.status_var.set("Running")
        self._append_log("Monitoring started.")

    def stop_monitoring(self) -> None:
        if not self.monitoring:
            return

        self.stop_event.set()
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=2.0)
        self.monitoring = False
        self.status_var.set("Stopped")
        self._append_log("Monitoring stopped.")

    def reload_email_config(self) -> None:
        self.email_config = EmailConfig()
        self.email_service = EmailAlertService(self.email_config)
        self.email_var.set(self._email_status_text())
        self._append_log("Reloaded email config from environment variables.")

    def _monitor_loop(self) -> None:
        while not self.stop_event.is_set():
            offline_transition: list[str] = []
            snapshot: list[DeviceState] = []
            for host, state in list(self.devices.items()):
                result = self.ping_service.ping_ms(host)
                new_status = "UP" if result is not None else "DOWN"
                latency = f"{result:.2f}" if result is not None else "-"

                if new_status != state.status:
                    state.changed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    if new_status == "DOWN" and not state.down_notified:
                        offline_transition.append(host)
                        state.down_notified = True
                    elif new_status == "UP":
                        state.down_notified = False

                state.status = new_status
                state.latency_ms = latency
                snapshot.append(DeviceState(**state.__dict__))

            self.queue.put({"type": "snapshot", "data": snapshot})
            if offline_transition:
                self.queue.put({"type": "log", "data": f"Offline detected: {', '.join(offline_transition)}"})
                _, log_message = self.email_service.send_offline_alert(offline_transition)
                self.queue.put({"type": "log", "data": log_message})

            time.sleep(PING_INTERVAL_SECONDS)

    def _poll_queue(self) -> None:
        try:
            while True:
                item = self.queue.get_nowait()
                if item["type"] == "snapshot":
                    self._apply_snapshot(item["data"])
                elif item["type"] == "log":
                    self._append_log(item["data"])
        except queue.Empty:
            pass
        finally:
            self.root.after(200, self._poll_queue)

    def _apply_snapshot(self, snapshot: list[DeviceState]) -> None:
        for state in snapshot:
            if state.host not in self.devices:
                continue
            self.table.item(
                state.host,
                values=(state.host, state.status, state.latency_ms, state.changed_at),
                tags=(state.status,),
            )

    def _append_log(self, message: str) -> None:
        now = datetime.now().strftime("%H:%M:%S")
        self.log.configure(state="normal")
        self.log.insert("end", f"[{now}] {message}\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _refresh_counters(self) -> None:
        self.count_var.set(f"{len(self.devices)} device(s)")

    def _email_status_text(self) -> str:
        return "Email: configured" if self.email_config.enabled() else "Email: not configured"

    def on_close(self) -> None:
        self.stop_monitoring()
        self.root.destroy()
