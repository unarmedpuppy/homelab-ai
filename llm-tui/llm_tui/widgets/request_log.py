from textual.app import ComposeResult
from textual.widget import Widget
from textual.widgets import DataTable, Label

from llm_tui.models import RequestMetric


MAX_ROWS = 200


class RequestLog(Widget):
    """Scrolling log of recent inference requests."""

    DEFAULT_CSS = """
    RequestLog {
        height: 1fr;
        border: solid $surface-lighten-2;
        margin: 1 0 0 0;
    }
    RequestLog .log-header {
        text-style: bold;
        color: $text;
        padding: 0 1;
    }
    RequestLog DataTable {
        height: 1fr;
    }
    RequestLog .empty-msg {
        color: $text-muted;
        text-style: italic;
        padding: 1 2;
    }
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._seen_ids: set[int] = set()
        self._router_connected = False

    def compose(self) -> ComposeResult:
        yield Label("Request Log", classes="log-header")
        yield DataTable(id="request-table")

    def on_mount(self) -> None:
        table = self.query_one("#request-table", DataTable)
        table.add_columns(
            "Time",
            "Model",
            "In",
            "Out",
            "Latency",
            "Tok/s",
            "User",
        )
        table.cursor_type = "none"
        table.zebra_stripes = True

    def update_metrics(
        self, metrics: list[RequestMetric], connected: bool = True
    ) -> None:
        self._router_connected = connected
        table = self.query_one("#request-table", DataTable)

        if not connected:
            return

        new_metrics = [m for m in metrics if m.id not in self._seen_ids]
        if not new_metrics:
            return

        for m in sorted(new_metrics, key=lambda x: x.id):
            self._seen_ids.add(m.id)

            # Format time
            ts = m.timestamp
            if "T" in ts:
                ts = ts.split("T")[1][:8]
            elif " " in ts:
                ts = ts.split(" ")[1][:8]

            # Format latency
            if m.duration_ms > 5000:
                lat = f"[red]{m.duration_ms}ms[/]"
            elif m.duration_ms > 1000:
                lat = f"[yellow]{m.duration_ms}ms[/]"
            else:
                lat = f"[green]{m.duration_ms}ms[/]"

            # Format tok/s
            tps = m.tokens_per_sec
            if tps > 0:
                if tps >= 20:
                    tps_str = f"[green]{tps:.1f}[/]"
                elif tps >= 10:
                    tps_str = f"[yellow]{tps:.1f}[/]"
                else:
                    tps_str = f"[red]{tps:.1f}[/]"
            else:
                tps_str = "--"

            # Status indicator in model name
            model = m.model_used or m.model_requested
            if not m.success:
                model = f"[red]{model}[/]"

            table.add_row(
                ts,
                model,
                str(m.prompt_tokens),
                str(m.completion_tokens),
                lat,
                tps_str,
                m.display_user[:12] if m.display_user != "unknown" else "--",
            )

        # Trim old rows
        while table.row_count > MAX_ROWS:
            first_key = next(iter(table.rows))
            table.remove_row(first_key)

        # Auto-scroll to bottom
        table.scroll_end(animate=False)
