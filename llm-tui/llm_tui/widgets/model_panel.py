from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Static, Label

from llm_tui.models import ManagerStatus


class ModelPanel(Widget):
    """Currently loaded model info panel."""

    DEFAULT_CSS = """
    ModelPanel {
        height: auto;
        border: solid $surface-lighten-2;
        padding: 0 1;
        margin: 1 0 0 0;
    }
    ModelPanel .panel-header {
        text-style: bold;
        color: $text;
    }
    ModelPanel .model-row {
        height: 1;
    }
    ModelPanel .label {
        width: 14;
        color: $text-muted;
    }
    ModelPanel .value {
        width: 1fr;
    }
    ModelPanel .status-running { color: #22c55e; text-style: bold; }
    ModelPanel .status-loading { color: #eab308; text-style: bold; }
    ModelPanel .status-stopped { color: #ef4444; text-style: bold; }
    ModelPanel .status-disconnected { color: #6b7280; text-style: italic; }
    ModelPanel .gaming-badge { color: #ef4444; text-style: bold; }
    ModelPanel .mode-badge { color: #3b82f6; }
    ModelPanel .slots-idle { color: #22c55e; }
    ModelPanel .slots-active { color: #eab308; text-style: bold; }
    ModelPanel .slots-full { color: #ef4444; text-style: bold; }
    """

    def compose(self) -> ComposeResult:
        yield Label("Model Status", classes="panel-header")
        with Horizontal(classes="model-row"):
            yield Label("Status", classes="label")
            yield Label("Connecting...", id="model-status", classes="value status-disconnected")
        with Horizontal(classes="model-row"):
            yield Label("Model", classes="label")
            yield Label("--", id="model-name", classes="value")
        with Horizontal(classes="model-row"):
            yield Label("Runtime", classes="label")
            yield Label("--", id="model-runtime", classes="value")
        with Horizontal(classes="model-row"):
            yield Label("VRAM / Context", classes="label")
            yield Label("--", id="model-details", classes="value")
        with Horizontal(classes="model-row"):
            yield Label("Slots", classes="label")
            yield Label("--", id="model-slots", classes="value")
        with Horizontal(classes="model-row"):
            yield Label("Mode", classes="label")
            yield Label("--", id="model-mode", classes="value")

    def update_status(self, status: ManagerStatus | None) -> None:
        status_label = self.query_one("#model-status", Label)
        name_label = self.query_one("#model-name", Label)
        runtime_label = self.query_one("#model-runtime", Label)
        details_label = self.query_one("#model-details", Label)
        slots_label = self.query_one("#model-slots", Label)
        mode_label = self.query_one("#model-mode", Label)

        if status is None:
            status_label.update("DISCONNECTED")
            status_label.remove_class("status-running", "status-loading", "status-stopped")
            status_label.add_class("status-disconnected")
            name_label.update("--")
            runtime_label.update("--")
            details_label.update("--")
            slots_label.update("--")
            mode_label.update("--")
            return

        # Mode info
        mode_parts = [status.mode.upper()]
        if status.gaming_mode_active:
            mode_parts.append("GAMING MODE")
        mode_label.update(" | ".join(mode_parts))
        mode_label.remove_class("gaming-badge", "mode-badge")
        mode_label.add_class("gaming-badge" if status.gaming_mode_active else "mode-badge")

        if status.running:
            model = status.running[0]
            status_label.update("RUNNING")
            status_label.remove_class("status-loading", "status-stopped", "status-disconnected")
            status_label.add_class("status-running")

            name_label.update(f"{model.name} ({model.id})")
            runtime_label.update(model.runtime.upper())

            idle_str = ""
            if model.idle_seconds is not None:
                m, s = divmod(model.idle_seconds, 60)
                h, m = divmod(m, 60)
                if h > 0:
                    idle_str = f" | idle {h}h{m}m"
                elif m > 0:
                    idle_str = f" | idle {m}m{s}s"
                else:
                    idle_str = f" | idle {s}s"

            details_label.update(f"{model.vram_gb:.0f} GB{idle_str}")

            # Slots: show active requests as filled slots
            active = status.active_requests
            max_slots = 3  # TP=2 dual GPU supports ~3 concurrent
            filled = min(active, max_slots)
            slot_str = f"{'●' * filled}{'○' * (max_slots - filled)} {active}/{max_slots}"
            slots_label.update(slot_str)
            slots_label.remove_class("slots-idle", "slots-active", "slots-full")
            if active == 0:
                slots_label.add_class("slots-idle")
            elif active >= max_slots:
                slots_label.add_class("slots-full")
            else:
                slots_label.add_class("slots-active")
        elif status.gaming_mode_active:
            status_label.update("GAMING MODE")
            status_label.remove_class("status-running", "status-loading", "status-disconnected")
            status_label.add_class("status-stopped")
            name_label.update("All models stopped")
            runtime_label.update("--")
            details_label.update("--")
            slots_label.update("--")
        else:
            status_label.update("NO MODEL LOADED")
            status_label.remove_class("status-running", "status-loading", "status-disconnected")
            status_label.add_class("status-stopped")
            name_label.update(f"Default: {status.default_model}" if status.default_model else "--")
            runtime_label.update("--")
            details_label.update(f"{status.available} models available")
            slots_label.update("--")
