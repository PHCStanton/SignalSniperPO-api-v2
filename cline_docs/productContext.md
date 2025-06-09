# Product Context

## Why this project exists

This project exists to create a highly responsive and automated trading bot that can execute trades on the Pocket Option platform with minimal latency. The primary goal is to capitalize on trading signals provided in a specific Telegram channel, "BINARY TRADING CLUB," by automating the process of signal detection, parsing, and trade execution.

## What problems it solves

The bot solves the following problems:

1.  **Latency in Manual Trading**: Manual execution of trades based on signals is prone to delays, which can lead to missed opportunities or poor entry points. The bot aims to reduce this latency to under 2 seconds.
2.  **Human Error**: Manual trading is susceptible to errors in interpreting signals or executing trades. The bot automates this process to ensure accuracy.
3.  **24/7 Monitoring**: The bot can monitor the Telegram channel for signals around the clock, something that is not feasible for a human trader.
4.  **Discreet Monitoring**: By using a Telegram user account (userbot) instead of a bot account, it can monitor the channel without being easily detected or restricted.

## How it should work

The bot operates as follows:

1.  **Connects to Telegram**: It uses a Telethon-based user account to connect to Telegram and monitor the "BINARY TRADING CLUB" channel.
2.  **Parses Signals**: It listens for new messages and parses them to identify trading signals, which are typically sent in a two-message format.
3.  **Authenticates with Pocket Option**: It uses a WebSocket-based SSID for authentication with the Pocket Option API, as traditional login methods are not viable.
4.  **Executes Trades**: Upon receiving a valid signal, it calculates the appropriate trade parameters (pair, direction, expiry) and executes the trade on the Pocket Option platform.
5.  **Logs and Tracks**: It logs all signals, trades, and outcomes to JSON files for analysis and maintains session statistics.
6.  **Risk Management**: It incorporates basic risk management features, such as setting a maximum number of daily trades and a maximum daily loss.
