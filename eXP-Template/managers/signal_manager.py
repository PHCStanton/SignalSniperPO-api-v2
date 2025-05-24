"""Signal management for trading system.

This module provides the SignalManager class for receiving and processing
trading signals from Telegram channels.
"""
import asyncio
from telethon import TelegramClient, events
from typing import Optional
from models.signal import Signal


class SignalManager:
    """Class for managing Telegram signal reception and processing.

    This class handles connecting to Telegram, listening for signals,
    and processing them into standardized Signal objects.

    Attributes:
        config: Configuration object
        telegram_client: Telegram client instance  
        signal_queue: Queue for processed signals
        signal_patterns: Patterns for parsing signals
        running: Whether the manager is currently running
    """

    def __init__(self, config):
        """Initialize SignalManager with configuration.

        Args:
            config: Configuration object containing Telegram credentials
        """
        self.config = config
        self.telegram_client = None
        self.signal_queue = asyncio.Queue()
        self.signal_patterns = self.config.get_config("signal_patterns")
        self.running = False

    async def start_listening(self):
        """Start listening for signals from Telegram channel.
        
        Connects to Telegram and sets up message handler for the configured channel.
        """
        self.running = True
        api_id = self.config.get_config("telegram_api_id")
        api_hash = self.config.get_config("telegram_api_hash")
        channel_id = self.config.get_config("telegram_channel_id")

        self.telegram_client = TelegramClient('bot_session', api_id, api_hash)
        await self.telegram_client.start()

        @self.telegram_client.on(events.NewMessage(chats=channel_id))
        async def handle_new_message(event):
            if self.running:
                signal = await self.process_signal(event.message.text)
                if signal:
                    await self.signal_queue.put(signal)

        await self.telegram_client.run_until_disconnected()

    async def stop_listening(self):
        """Stop listening for signals and disconnect from Telegram."""
        self.running = False
        if self.telegram_client:
            await self.telegram_client.disconnect()

    async def process_signal(self, message_text: str) -> Optional[Signal]:
        """Process a message into a Signal object.

        Args:
            message_text: Raw message text from Telegram

        Returns:
            Optional[Signal]: Processed signal or None if message doesn't match patterns
        """
        for pattern_info in self.signal_patterns.values():
            import re
            match = re.match(pattern_info["pattern"], message_text)
            if match:
                data = match.groupdict()
                return Signal(
                    timestamp=asyncio.get_event_loop().time(),
                    symbol=data["symbol"],
                    direction=data["direction"],
                    expiry=int(data["expiry"]),
                    confidence=1.0,
                    source="telegram"
                )
        return None

    async def get_next_signal(self) -> Signal:
        """Get next available signal from the queue.

        Returns:
            Signal: Next available signal
        """
        return await self.signal_queue.get()