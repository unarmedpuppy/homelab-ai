from collections import deque

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widget import Widget
from textual.widgets import Label, Sparkline

from llm_tui.models import RequestMetric


WINDOW = 60


class MetricsPanel(Widget):
    """Live sparkline charts for tokens/sec and latency."""

    DEFAULT_CSS = """
    MetricsPanel {
        height: 8;
        layout: horizontal;
        margin: 1 0 0 0;
    }
    MetricsPanel .metric-box {
        width: 1fr;
        border: solid $surface-lighten-2;
        padding: 0 1;
        margin: 0 1 0 0;
    }
    MetricsPanel .metric-box:last-of-type {
        margin: 0;
    }
    MetricsPanel .metric-header {
        height: 1;
    }
    MetricsPanel .metric-title {
        text-style: bold;
        color: $text;
    }
    MetricsPanel .metric-value {
        color: #22c55e;
        text-style: bold;
    }
    MetricsPanel Sparkline {
        height: 4;
    }
    MetricsPanel .metric-stats {
        height: 1;
        color: $text-muted;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tps_data: deque[float] = deque(maxlen=WINDOW)
        self._latency_data: deque[float] = deque(maxlen=WINDOW)
        self._seen_ids: set[int] = set()

    def compose(self) -> ComposeResult:
        with Widget(classes="metric-box"):
            with Horizontal(classes="metric-header"):
                yield Label("Tokens/sec ", classes="metric-title")
                yield Label("--", id="tps-current", classes="metric-value")
            yield Sparkline([], id="tps-spark")
            yield Label("", id="tps-stats", classes="metric-stats")

        with Widget(classes="metric-box"):
            with Horizontal(classes="metric-header"):
                yield Label("Latency ", classes="metric-title")
                yield Label("--", id="lat-current", classes="metric-value")
            yield Sparkline([], id="lat-spark")
            yield Label("", id="lat-stats", classes="metric-stats")

    def update_metrics(self, metrics: list[RequestMetric]) -> None:
        new = [m for m in metrics if m.id not in self._seen_ids and m.success]
        for m in sorted(new, key=lambda x: x.id):
            self._seen_ids.add(m.id)
            self._tps_data.append(m.tokens_per_sec)
            self._latency_data.append(m.duration_ms)

        # Update tokens/sec sparkline
        tps_spark = self.query_one("#tps-spark", Sparkline)
        tps_current = self.query_one("#tps-current", Label)
        tps_stats = self.query_one("#tps-stats", Label)

        if self._tps_data:
            tps_spark.data = list(self._tps_data)
            tps_current.update(f"{self._tps_data[-1]:.1f}")
            avg = sum(self._tps_data) / len(self._tps_data)
            mn, mx = min(self._tps_data), max(self._tps_data)
            tps_stats.update(f"avg {avg:.1f}  min {mn:.1f}  max {mx:.1f}  ({len(self._tps_data)} samples)")
        else:
            tps_current.update("--")
            tps_stats.update("No data")

        # Update latency sparkline
        lat_spark = self.query_one("#lat-spark", Sparkline)
        lat_current = self.query_one("#lat-current", Label)
        lat_stats = self.query_one("#lat-stats", Label)

        if self._latency_data:
            lat_spark.data = list(self._latency_data)
            last_ms = self._latency_data[-1]
            lat_current.update(f"{last_ms:.0f}ms")
            avg = sum(self._latency_data) / len(self._latency_data)
            mn, mx = min(self._latency_data), max(self._latency_data)
            lat_stats.update(f"avg {avg:.0f}ms  min {mn:.0f}ms  max {mx:.0f}ms  ({len(self._latency_data)} samples)")
        else:
            lat_current.update("--")
            lat_stats.update("No data")
