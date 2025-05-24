# src/tui.py
import asyncio
from textual.app import App, ComposeResult
from textual.containers import Container
from textual.widgets import Header, Footer, Input, Button, Static, Log
from textual.binding import Binding
from datetime import datetime
import json

class TradingBotTUI(App):
    CSS = """
    Screen {
        align: center middle;
    }

    #main-container {
        width: 80%;
        height: 80%;
        border: solid green;
        padding: 1;
    }

    #status-container {
        height: 30%;
        border: solid blue;
        margin: 1;
    }

    #control-container {
        height: 20%;
        margin: 1;
    }

    .input-label {
        width: 100%;
        content-align: center middle;
        padding: 1;
    }

    Button {
        width: 20;
        margin: 1;
    }

    Log {
        height: 40%;
        border: solid red;
        margin: 1;
    }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh_ssid", "Refresh SSID"),
        Binding("t", "toggle_trading", "Toggle Trading"),
    ]

    def __init__(self):
        super().__init__()
        self.trading_active = False
        self.connection_status = "Disconnected"
        self.last_price = None
        self.account_balance = 0.0

    def compose(self) -> ComposeResult:
        yield Header()
        yield Container(
            Container(
                Static("Connection Status: ", classes="input-label"),
                Static(id="connection-status"),
                Static("Account Balance: ", classes="input-label"),
                Static(id="account-balance"),
                Static("Last Price: ", classes="input-label"),
                Static(id="last-price"),
                id="status-container"
            ),
            Container(
                Static("SSID:", classes="input-label"),
                Input(placeholder="Enter SSID here", id="ssid-input"),
                Button("Connect", id="connect-btn"),
                Button("Start Trading", id="trading-btn"),
                id="control-container"
            ),
            Log(id="trading-log"),
            id="main-container"
        )
        yield Footer()

    def on_mount(self) -> None:
        """Called when app is mounted."""
        self.update_status()

    def update_status(self) -> None:
        """Update status displays."""
        self.query_one("#connection-status").update(f"Status: {self.connection_status}")
        self.query_one("#account-balance").update(f"Balance: ${self.account_balance:.2f}")
        self.query_one("#last-price").update(
            f"Last Price: {self.last_price if self.last_price else 'N/A'}"
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "connect-btn":
            ssid = self.query_one("#ssid-input").value
            if ssid:
                self.connect_websocket(ssid)
        elif event.button.id == "trading-btn":
            self.toggle_trading()

    def connect_websocket(self, ssid: str) -> None:
        """Connect to WebSocket with provided SSID."""
        self.connection_status = "Connecting..."
        self.update_status()
        # Connection logic will be handled by main.py
        self.post_message({"type": "connect", "ssid": ssid})

    def toggle_trading(self) -> None:
        """Toggle trading status."""
        self.trading_active = not self.trading_active
        btn_text = "Stop Trading" if self.trading_active else "Start Trading"
        self.query_one("#trading-btn").label = btn_text
        status = "Active" if self.trading_active else "Stopped"
        self.add_log_message(f"Trading {status}")

    def add_log_message(self, message: str) -> None:
        """Add message to trading log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.query_one("#trading-log").write(f"[{timestamp}] {message}")

    def action_refresh_ssid(self) -> None:
        """Refresh SSID action."""
        self.add_log_message("Refreshing SSID...")
        self.post_message({"type": "refresh_ssid"})

    def action_toggle_trading(self) -> None:
        """Toggle trading action."""
        self.toggle_trading()

    def update_price(self, price: float) -> None:
        """Update last price display."""
        self.last_price = price
        self.update_status()

    def update_balance(self, balance: float) -> None:
        """Update account balance display."""
        self.account_balance = balance
        self.update_status()

    def update_connection_status(self, status: str) -> None:
        """Update connection status."""
        self.connection_status = status
        self.update_status()