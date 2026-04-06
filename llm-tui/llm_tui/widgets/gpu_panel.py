from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Static, ProgressBar, Label

from llm_tui.models import GPUStats


class GPUCard(Widget):
    """Single GPU status card."""

    DEFAULT_CSS = """
    GPUCard {
        width: 1fr;
        height: auto;
        border: solid $surface-lighten-2;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    GPUCard:last-of-type {
        margin: 0;
    }
    GPUCard .gpu-header {
        text-style: bold;
        color: $text;
        margin-bottom: 0;
    }
    GPUCard .gpu-row {
        height: 1;
    }
    GPUCard .gpu-label {
        width: 12;
        color: $text-muted;
    }
    GPUCard .gpu-value {
        width: 1fr;
    }
    GPUCard .temp-ok { color: #22c55e; }
    GPUCard .temp-warm { color: #eab308; }
    GPUCard .temp-hot { color: #ef4444; }
    GPUCard .util-low { color: $text-muted; }
    GPUCard .util-mid { color: #eab308; }
    GPUCard .util-high { color: #22c55e; }
    GPUCard ProgressBar {
        margin: 0;
        padding: 0;
    }
    GPUCard ProgressBar Bar {
        width: 1fr;
    }
    GPUCard .vram-text {
        color: $text;
    }
    """

    gpu_index: reactive[int] = reactive(0)
    stats: reactive[GPUStats | None] = reactive(None)

    def __init__(self, gpu_index: int, **kwargs):
        super().__init__(**kwargs)
        self.gpu_index = gpu_index

    def compose(self) -> ComposeResult:
        yield Label(f"GPU {self.gpu_index}", classes="gpu-header", id=f"gpu-name-{self.gpu_index}")
        with Horizontal(classes="gpu-row"):
            yield Label("Temp", classes="gpu-label")
            yield Label("--", id=f"gpu-temp-{self.gpu_index}", classes="gpu-value")
        with Horizontal(classes="gpu-row"):
            yield Label("Power", classes="gpu-label")
            yield Label("--", id=f"gpu-power-{self.gpu_index}", classes="gpu-value")
        with Horizontal(classes="gpu-row"):
            yield Label("Util", classes="gpu-label")
            yield Label("--", id=f"gpu-util-{self.gpu_index}", classes="gpu-value")
        with Horizontal(classes="gpu-row"):
            yield Label("VRAM", classes="gpu-label")
            yield Label("--", id=f"gpu-vram-text-{self.gpu_index}", classes="gpu-value vram-text")
        yield ProgressBar(total=100, show_eta=False, show_percentage=False, id=f"gpu-vram-bar-{self.gpu_index}")

    def update_stats(self, stats: GPUStats) -> None:
        self.stats = stats
        # Name
        name_label = self.query_one(f"#gpu-name-{self.gpu_index}", Label)
        name_label.update(f"GPU {stats.index}: {stats.name}")

        # Temperature
        temp_label = self.query_one(f"#gpu-temp-{self.gpu_index}", Label)
        temp_label.update(f"{stats.temp_c}°C")
        temp_label.remove_class("temp-ok", "temp-warm", "temp-hot")
        if stats.temp_c < 70:
            temp_label.add_class("temp-ok")
        elif stats.temp_c < 85:
            temp_label.add_class("temp-warm")
        else:
            temp_label.add_class("temp-hot")

        # Power
        power_label = self.query_one(f"#gpu-power-{self.gpu_index}", Label)
        power_label.update(f"{stats.power_draw_w:.0f}W / {stats.power_limit_w:.0f}W")

        # Utilization
        util_label = self.query_one(f"#gpu-util-{self.gpu_index}", Label)
        util_label.update(f"{stats.utilization_pct}%")
        util_label.remove_class("util-low", "util-mid", "util-high")
        if stats.utilization_pct < 10:
            util_label.add_class("util-low")
        elif stats.utilization_pct < 50:
            util_label.add_class("util-mid")
        else:
            util_label.add_class("util-high")

        # VRAM
        used_gb = stats.vram_used_mb / 1024
        total_gb = stats.vram_total_mb / 1024
        free_gb = stats.vram_free_mb / 1024
        vram_text = self.query_one(f"#gpu-vram-text-{self.gpu_index}", Label)
        vram_text.update(f"{used_gb:.1f} / {total_gb:.1f} GB ({free_gb:.1f} GB free)")

        vram_bar = self.query_one(f"#gpu-vram-bar-{self.gpu_index}", ProgressBar)
        vram_bar.update(progress=stats.vram_pct)


class GPUPanel(Widget):
    """Dual GPU panel showing both cards side by side."""

    DEFAULT_CSS = """
    GPUPanel {
        height: auto;
        layout: horizontal;
        padding: 0;
    }
    """

    def __init__(self, gpu_count: int = 2, **kwargs):
        super().__init__(**kwargs)
        self.gpu_count = gpu_count

    def compose(self) -> ComposeResult:
        for i in range(self.gpu_count):
            yield GPUCard(gpu_index=i, id=f"gpu-card-{i}")

    def update_stats(self, gpu_stats: list[GPUStats]) -> None:
        for stats in gpu_stats:
            try:
                card = self.query_one(f"#gpu-card-{stats.index}", GPUCard)
                card.update_stats(stats)
            except Exception:
                pass
