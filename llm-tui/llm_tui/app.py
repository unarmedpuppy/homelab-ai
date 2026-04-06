from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import Header, Footer, Label

from llm_tui.config import Config
from llm_tui.api.gpu import poll_gpu_stats
from llm_tui.api.manager import ManagerClient
from llm_tui.models import ManagerStatus
from llm_tui.widgets.gpu_panel import GPUPanel
from llm_tui.widgets.model_panel import ModelPanel
from llm_tui.widgets.request_log import RequestLog
from llm_tui.widgets.metrics_panel import MetricsPanel
from llm_tui.widgets.model_picker import ModelPicker


class LlmTuiApp(App):
    """Terminal UI for managing local LLM infrastructure."""

    TITLE = "llm-tui"
    SUB_TITLE = "Local LLM Manager"

    CSS = """
    Screen {
        background: #0f172a;
    }
    #main-container {
        padding: 0 1;
    }
    Header {
        dock: top;
    }
    Footer {
        dock: bottom;
    }
    .conn-status {
        dock: top;
        height: 1;
        padding: 0 1;
        color: #6b7280;
        text-style: italic;
    }
    .conn-ok { color: #22c55e; text-style: bold; }
    .conn-err { color: #ef4444; text-style: bold; }
    """

    BINDINGS = [
        Binding("s", "swap", "Swap Model"),
        Binding("g", "gaming", "Gaming Mode"),
        Binding("x", "stop_all", "Stop All"),
        Binding("r", "reload", "Reload"),
        Binding("q", "quit", "Quit"),
    ]

    def __init__(self, config: Config | None = None, **kwargs):
        super().__init__(**kwargs)
        self.config = config or Config()
        self.client = ManagerClient(self.config)
        self._status: ManagerStatus | None = None
        self._router_connected = False

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main-container"):
            yield Label("Connecting to llm-manager...", id="conn-status", classes="conn-status")
            yield GPUPanel(gpu_count=2, id="gpu-panel")
            yield ModelPanel(id="model-panel")
            yield RequestLog(id="request-log")
            yield MetricsPanel(id="metrics-panel")
        yield Footer()

    def on_mount(self) -> None:
        self.set_interval(self.config.gpu_poll_interval, self._poll_gpu)
        self.set_interval(self.config.api_poll_interval, self._poll_manager)
        self.set_interval(self.config.metrics_poll_interval, self._poll_metrics)
        # Immediate first poll
        self.call_later(self._poll_gpu)
        self.call_later(self._poll_manager)
        self.call_later(self._poll_metrics)

    async def _poll_gpu(self) -> None:
        stats = await poll_gpu_stats()
        if stats:
            self.query_one("#gpu-panel", GPUPanel).update_stats(stats)

    async def _poll_manager(self) -> None:
        status = await self.client.get_status()
        self._status = status
        self.query_one("#model-panel", ModelPanel).update_status(status)

        conn_label = self.query_one("#conn-status", Label)
        if status:
            running = status.running_count
            model_name = status.running[0].id if status.running else "none"
            conn_label.update(
                f"Connected to {self.config.manager_url} | "
                f"Mode: {status.mode} | "
                f"Active: {model_name} | "
                f"Models: {running} running / {status.available} available"
            )
            conn_label.remove_class("conn-err")
            conn_label.add_class("conn-ok")
        else:
            conn_label.update(f"Disconnected from {self.config.manager_url}")
            conn_label.remove_class("conn-ok")
            conn_label.add_class("conn-err")

    async def _poll_metrics(self) -> None:
        metrics = await self.client.get_recent_metrics()
        connected = len(metrics) > 0 or self._router_connected
        self._router_connected = connected
        self.query_one("#request-log", RequestLog).update_metrics(metrics, connected)
        self.query_one("#metrics-panel", MetricsPanel).update_metrics(metrics)

    async def action_swap(self) -> None:
        cards = await self.client.get_model_cards()
        if not cards:
            self.notify("Cannot load model list", severity="error")
            return

        def on_dismiss(model_id: str | None) -> None:
            if model_id:
                self.notify(f"Swapping to {model_id}...", timeout=10)
                self.run_worker(self._do_swap(model_id))

        self.push_screen(ModelPicker(cards), callback=on_dismiss)

    async def _do_swap(self, model_id: str) -> None:
        result = await self.client.swap_model(model_id)
        if result:
            self.notify(f"Swapped to {model_id}", severity="information")
        else:
            self.notify(f"Swap to {model_id} failed", severity="error")

    async def action_gaming(self) -> None:
        if self._status is None:
            self.notify("Not connected", severity="error")
            return
        enable = not self._status.gaming_mode_active
        result = await self.client.toggle_gaming_mode(enable)
        if result:
            state = "ON" if enable else "OFF"
            self.notify(f"Gaming mode {state}")
        else:
            self.notify("Failed to toggle gaming mode", severity="error")

    async def action_stop_all(self) -> None:
        result = await self.client.stop_all()
        if result:
            stopped = result.get("stopped", [])
            self.notify(f"Stopped {len(stopped)} model(s)")
        else:
            self.notify("Failed to stop models", severity="error")

    async def action_reload(self) -> None:
        await self._poll_gpu()
        await self._poll_manager()
        await self._poll_metrics()
        self.notify("Refreshed")

    async def on_unmount(self) -> None:
        await self.client.close()
