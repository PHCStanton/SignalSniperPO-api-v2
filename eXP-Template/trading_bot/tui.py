# trading_bot/tui.py
import os
import logging
from datetime import datetime
from typing import Optional, Dict, Any, Callable
import threading
import time

logger = logging.getLogger(__name__)

class TradingBotTUI:
    def __init__(self):
        self.on_message: Optional[Callable] = None
        self.trading_active = False
        self.connection_status = "Disconnected"
        self.last_price = None
        self.account_balance = 0.0
        self.log_messages = []
        self.running = True
        self.display_thread = None

    def clear_screen(self):
        """Clear the terminal screen."""
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_status(self):
        """Display status information."""
        status_color = '\033[92m' if self.connection_status == "Connected" else '\033[91m'  # Green or Red
        trading_status = '\033[92mActive' if self.trading_active else '\033[91mInactive'
        reset_color = '\033[0m'

        print(f"\n{'='*50}")
        print(f"Status: {status_color}{self.connection_status}{reset_color}")
        print(f"Balance: ${self.account_balance:.2f}")
        print(f"Last Price: {self.last_price if self.last_price else 'N/A'}")
        print(f"Trading: {trading_status}{reset_color}")
        print(f"{'='*50}\n")

    def display_log(self):
        """Display trading log messages."""
        print("Trading Log:")
        print('-'*50)
        for message in self.log_messages[-10:]:  # Show last 10 messages
            print(message)
        print('-'*50)

    def display_menu(self):
        """Display available commands."""
        print("\nCommands:")
        print("1. Connect with SSID")
        print("2. Toggle Trading")
        print("3. Refresh SSID")
        print("4. Quit")
        print("\nEnter command number: ", end='', flush=True)

    def update_display(self):
        """Continuously update the display."""
        while self.running:
            self.clear_screen()
            self.display_status()
            self.display_log()
            self.display_menu()
            time.sleep(1)

    def handle_input(self):
        """Handle user input."""
        while self.running:
            try:
                choice = input()
                if choice == '1':
                    ssid = input("Enter SSID: ")
                    if ssid and self.on_message:
                        self.on_message({"type": "connect", "ssid": ssid})
                elif choice == '2' and self.on_message:
                    self.on_message({"type": "toggle_trading"})
                elif choice == '3' and self.on_message:
                    self.on_message({"type": "refresh_ssid"})
                elif choice == '4':
                    self.running = False
                    break
            except EOFError:
                break
            except KeyboardInterrupt:
                break

    def run(self):
        """Run the TUI main loop."""
        try:
            # Start display thread
            self.display_thread = threading.Thread(target=self.update_display)
            self.display_thread.daemon = True
            self.display_thread.start()

            # Handle input in main thread
            self.handle_input()
        except Exception as e:
            logger.error(f"TUI error: {str(e)}")
            raise
        finally:
            self.running = False
            if self.display_thread:
                self.display_thread.join()

    def update_connection_status(self, status: str):
        """Update connection status."""
        self.connection_status = status

    def update_price(self, price: float):
        """Update last price display."""
        self.last_price = price

    def update_balance(self, balance: float):
        """Update account balance display."""
        self.account_balance = balance

    def add_log_message(self, message: str):
        """Add message to trading log."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_messages.append(f"[{timestamp}] {message}")