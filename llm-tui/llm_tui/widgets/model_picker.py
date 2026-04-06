from textual.app import ComposeResult
from textual.containers import Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import DataTable, Label, Footer

from llm_tui.models import ModelCard


class ModelPicker(ModalScreen[str | None]):
    """Modal for selecting a model to swap to."""

    DEFAULT_CSS = """
    ModelPicker {
        align: center middle;
    }
    ModelPicker .picker-container {
        width: 90;
        max-height: 80%;
        border: solid $accent;
        background: $surface;
        padding: 1 2;
    }
    ModelPicker .picker-title {
        text-style: bold;
        color: $text;
        text-align: center;
        width: 100%;
        margin-bottom: 1;
    }
    ModelPicker .picker-hint {
        color: $text-muted;
        text-align: center;
        width: 100%;
    }
    ModelPicker DataTable {
        height: 1fr;
        max-height: 30;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("enter", "select", "Select"),
    ]

    def __init__(self, cards: list[ModelCard], **kwargs):
        super().__init__(**kwargs)
        self.cards = cards

    def compose(self) -> ComposeResult:
        with Vertical(classes="picker-container"):
            yield Label("Swap Model", classes="picker-title")
            yield DataTable(id="picker-table")
            yield Label("Enter: swap | Esc: cancel", classes="picker-hint")

    def on_mount(self) -> None:
        table = self.query_one("#picker-table", DataTable)
        table.add_columns("Model", "VRAM", "Runtime", "Quant", "Context", "Status", "Cached")
        table.cursor_type = "row"

        # Sort: running first, then cached, then rest. Filter to text models only.
        text_cards = [c for c in self.cards if c.type == "text"]
        text_cards.sort(key=lambda c: (
            0 if c.status == "running" else 1,
            0 if c.cached else 1,
            c.vram_gb,
        ))

        for card in text_cards:
            status = f"[green]RUNNING[/]" if card.status == "running" else card.status
            cached = f"[green]Yes ({card.cache_size_gb:.1f}GB)[/]" if card.cached else "[dim]No[/]"
            ctx = f"{(card.default_context or 0) // 1024}K" if card.default_context else "--"

            table.add_row(
                f"{card.name}",
                f"{card.vram_gb:.0f}GB",
                card.runtime,
                card.quantization or "--",
                ctx,
                status,
                cached,
                key=card.id,
            )

    def action_cancel(self) -> None:
        self.dismiss(None)

    def action_select(self) -> None:
        table = self.query_one("#picker-table", DataTable)
        if table.cursor_row is not None:
            row_keys = list(table.rows.keys())
            if 0 <= table.cursor_row < len(row_keys):
                self.dismiss(str(row_keys[table.cursor_row].value))
                return
        self.dismiss(None)
