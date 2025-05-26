# Modular SignalBot v1.5 Layout and Technical Report

This document provides a comprehensive overview and technical report for the Pocket Option Trading Bot project, addressing specific concerns and requirements for future development, particularly for version 1.5 of the Modular SignalBot. It covers database locking issues, key files for Telegram and WebSocket operations, core functionalities of the main bot script, and considerations for integrating a Text User Interface (TUI).

## 1. Database Locking Issue: Causes, Fixes, and Developer Advice

### Causes of Database Locking
The "database is locked" error encountered in the Telegram client initialization is related to the SQLite database used by the Telethon library to store session information. This error typically occurs due to the following reasons:

- **Concurrent Access**: SQLite databases are file-based and do not handle concurrent access well by default. If multiple processes or threads attempt to access or modify the session database simultaneously, a lock conflict arises. In this project, multiple instances of the bot or test scripts (like `test_telegram_api.py` and `self_bot.py`) might have been running concurrently, leading to this issue with the session file (e.g., `pocket_option_userbot.session`).
- **Improper Session Management**: If a previous process using the session file crashes or is terminated abruptly without releasing the lock, the database file can remain in a locked state, preventing subsequent access.
- **Threading Issues**: The bot uses threading for trade execution to avoid event loop conflicts in asyncio. However, if the SQLite connection is created in one thread and accessed in another without proper handling, it can cause locking issues, as SQLite connections are not thread-safe by default.
- **File System Permissions**: On some systems, file system permissions or restrictions can prevent proper access to the database file, leading to perceived locking issues.

### Fixes Implemented
The following steps were taken to resolve the immediate database locking issue with the Telegram session:
1. **Session Replacement**: The problematic session (`pocket_option_userbot`) was replaced with a new session (`test_session`) by deleting the old session file and recreating it using `test_telegram_api.py`. This ensured a fresh start without lingering locks.
2. **Configuration Update**: Updated the session name in both `self_bot.py` (as a fallback default) and `config/telegram_config.json` (primary configuration) to ensure consistent use of the new session.
3. **Single Process Execution**: Ensured that only one instance of the bot or related scripts accessing the Telegram session was running at a time during testing.

### Long-Term Solutions and Recommendations
For a robust solution to prevent future database locking issues, consider the following:
- **Use WAL Mode**: Enable Write-Ahead Logging (WAL) mode for SQLite by configuring Telethon to use it. WAL mode allows multiple readers and one writer to access the database simultaneously, reducing lock conflicts. This can be set via PRAGMA statements or library configuration if supported.
  ```sql
  PRAGMA journal_mode = WAL;
  ```
- **Session Isolation**: Ensure each bot instance or test script uses a unique session file to prevent conflicts. This can be managed by dynamically setting session names based on runtime parameters or environment variables.
- **Proper Process Management**: Implement a mechanism to ensure only one instance of the bot runs at a time, such as using a PID file or a lock file to prevent multiple launches.
- **Thread-Safe Database Access**: For the trade database (`trades.db`), ensure that SQLite connections are not shared across threads. Create a new connection per thread or use a connection pool with thread-local storage. Alternatively, consider using a thread-safe database like PostgreSQL for production environments.
- **Graceful Shutdown**: Implement proper shutdown handling to close database connections and release locks. This was partially addressed in `self_bot.py` with a signal handler to close the database connection on termination.
- **Retry Mechanism**: The current code already includes a retry mechanism for database operations (e.g., in `save_signal_to_db` and `save_trade_to_db`). Enhance this to handle lock exceptions with exponential backoff for robustness.

### Advice for Developers Taking Over
A developer inheriting this project should consider the following to manage database locking issues:
- **Understand SQLite Limitations**: Recognize that SQLite is not designed for high-concurrency environments. For scaling or production use, consider migrating session storage to a more robust database system if Telethon supports it, or isolate session files per instance.
- **Monitor Running Processes**: Be vigilant about multiple scripts or bot instances running simultaneously. Use tools like `ps` on Unix or Task Manager on Windows to check for lingering processes that might hold locks.
- **Test Environment Isolation**: When testing, ensure isolation by using separate session files or clearing old session data before starting new tests.
- **Backup Session Files**: Before making changes or running new instances, back up session files to avoid losing authentication data if a session becomes corrupted or locked.
- **Review Threading Model**: Examine the threading approach in `self_bot.py` for trade execution and database access. Ensure thread safety by not sharing SQLite connections across threads or by using appropriate locking mechanisms if necessary.
- **Documentation and Logging**: Maintain detailed logs of database operations and errors to trace locking issues. Enhance logging to include thread IDs and process IDs for debugging concurrency problems.

## 2. Files Responsible for Telegram Operations
The following files are directly involved in Telegram operations for signal monitoring and interaction:
- **`self_bot.py`**: The primary bot script that initializes the Telegram client using Telethon, monitors specified channels for trading signals, and processes incoming messages for trade execution. It handles session authentication and event registration for new messages.
- **`config/telegram_config.json`**: Configuration file storing Telegram API credentials (API ID, API Hash), session name, target channel details, and regex patterns for signal parsing.
- **`test_telegram_api.py`**: A utility script for testing Telegram API credentials and creating or verifying sessions. Used to authenticate and generate new session files.
- **`check_telegram_session.py`**: A script to check the status of Telegram sessions, helping to identify if a session is valid or locked.
- **`utils/telegram_setup.py`** and **`utils/telethon_setup.py`**: Utility scripts in the `utils` directory for setting up Telegram sessions or configurations, often used for initial setup or troubleshooting.
- **`test_telegram_access.py`**: Likely used for testing Telegram access or specific API functionalities related to channel access or message retrieval.
- **`verify_channel.py`**: A script to verify access to specific Telegram channels, ensuring the bot can monitor the intended signal sources.

These files collectively manage the connection to Telegram, session handling, and signal parsing logic critical to the bot's operation.

## 3. Files Responsible for SSID WebSocket Connection
The project uses a non-conventional approach for SSID-based WebSocket connection to Pocket Option, differing from the typical SSID cookie method. Below are the key files and implementation details:

### Key Files
- **`PocketOptionAPI-v2/pocketoptionapi/stable_api.py`**: Contains the `PocketOption` class which handles the WebSocket connection to Pocket Option using an SSID for authentication. This is the core API interface for trading operations.
- **`PocketOptionAPI-v2/pocketoptionapi/global_value.py`**: Stores global configuration values and state for the Pocket Option API, potentially including WebSocket connection parameters or SSID-related variables.
- **`config/pocket_option_config.json`**: Configuration file storing the SSID value used for WebSocket authentication, along with other settings like demo mode status.
- **`self_bot.py`**: Integrates with the Pocket Option API to initialize the client with the SSID from the configuration, manages connection, and executes trades via WebSocket calls.
- **`extract_websocket_ssid.py`**, **`get_pocket_option_ssid.py`**, **`extract_pocket_option_ssid.py`**: Utility scripts for obtaining or refreshing the SSID, likely through automated browser interactions or API calls, ensuring the bot has a valid SSID for WebSocket authentication.
- **`test_po_websocket.py`**, **`test_websocket_connection.py`**: Test scripts to verify WebSocket connectivity to Pocket Option using the SSID method, useful for debugging connection issues.
- **`websocket_connection_readme.md`**, **`extract_po_trade_ssid.md`**, **`WEBSOCKET_FIXES_SUMMARY.md`**: Documentation files providing insights into the WebSocket implementation, SSID extraction process, and any fixes or workarounds applied.

### Implementation Management
Unlike the conventional SSID cookie method where the SSID is passed as a cookie in HTTP requests, this project uses the SSID directly within WebSocket connection parameters or headers for authentication. Here's how it's managed:
- **SSID as Authentication Token**: The SSID is treated as a token passed during the WebSocket handshake or within initial connection messages to authenticate the client with Pocket Option's servers. This is evident in `stable_api.py` where the `PocketOption` class constructor accepts an SSID parameter.
- **Direct WebSocket Connection**: The API establishes a direct WebSocket connection (`wss://api-eu.po.market/socket.io/`) using libraries like `websocket-client` or similar, with SSID embedded in the connection request or subsequent messages, as seen in debug logs from `self_bot.py`.
- **Custom API Wrapper**: The `PocketOptionAPI-v2` directory contains a custom implementation that diverges from standard libraries, tailored to handle SSID-based WebSocket authentication, bypassing traditional HTTP cookie mechanisms.
- **SSID Refresh Mechanism**: Utility scripts like `extract_websocket_ssid.py` suggest an automated process to fetch or update the SSID, possibly through browser automation (e.g., Selenium) to log in and extract the SSID from a successful session, ensuring the bot always has a valid token.

### Considerations for Developers
When implementing or maintaining this SSID WebSocket connection, developers must keep the following in mind:
- **SSID Validity and Expiry**: SSIDs can expire or become invalidated. Implement a robust mechanism to detect connection failures due to invalid SSIDs and automatically refresh them using scripts like `extract_pocket_option_ssid.py`. Monitor API responses for authentication errors.
- **WebSocket Protocol Details**: Understand the specific WebSocket protocol used by Pocket Option (e.g., Socket.IO as seen in logs). Ensure the client correctly handles connection upgrades, heartbeats, and reconnection logic to maintain a stable link.
- **Security of SSID**: Treat the SSID as sensitive data akin to a password. Store it securely in configuration files or environment variables, and avoid logging it in plaintext. Ensure scripts that extract SSIDs do not expose them in logs or temporary files.
- **Non-Standard Implementation**: Since this deviates from the cookie-based approach, rely on the custom `PocketOptionAPI-v2` library rather than generic Pocket Option APIs. Study its internals (`stable_api.py`) to understand how SSID is integrated into WebSocket messages.
- **Connection Stability**: WebSocket connections can drop due to network issues or server-side policies. Implement reconnection logic with exponential backoff and ensure the bot can recover gracefully, re-authenticating with the SSID if needed.
- **API Updates**: Pocket Option may update their WebSocket endpoint or authentication mechanism. Monitor for changes and be prepared to adapt the API wrapper or SSID extraction process. Keep documentation like `WEBSOCKET_FIXES_SUMMARY.md` updated with any workarounds.

## 4. Core Functionalities of self_bot.py
`self_bot.py` is the central script for the trading bot, encapsulating the following core functionalities:
- **Initialization of Clients**: Sets up both Telegram (`TelegramClient` from Telethon) and Pocket Option (`PocketOption` from custom API) clients using configurations from JSON files, handling authentication and connection.
- **Signal Monitoring**: Listens to specified Telegram channels for trading signals using event handlers, processing incoming messages in real-time.
- **Signal Parsing**: Implements logic to parse trading signals from Telegram messages using regex patterns. Supports both single-message and two-part message formats to extract trading pair, direction (HIGHER/LOWER), expiry time, and timer settings.
- **Signal Validation**: Validates parsed signals based on criteria like sufficient account balance, maximum daily trades, and loss limits before execution.
- **Trade Execution**: Executes trades on Pocket Option via WebSocket API calls, supporting real trading mode with actual funds or test mode for simulation. Uses threading to avoid asyncio event loop conflicts during trade execution.
- **Database Management**: Manages an SQLite database (`trades.db`) to log signals and trades, including timestamps, asset details, outcomes, and profit/loss data for historical analysis.
- **Trade Result Checking**: Periodically checks the outcome of executed trades (win/loss/draw) using the Pocket Option API, updates statistics, and logs results to the database.
- **Statistics Tracking**: Maintains runtime statistics on total signals, valid signals, executed trades, wins, losses, and profit, providing insights into bot performance.
- **Configuration and Logging**: Loads settings from configuration files, supports verbose logging for debugging, and handles graceful shutdown with signal handling to close database connections.

## 5. Essential Considerations for TUI Integration
Integrating a Text User Interface (TUI) into the bot can enhance user interaction and monitoring capabilities. The following are essential functionalities and considerations for a TUI:

### Core TUI Functionalities
- **Real-Time Monitoring Dashboard**: Display live updates of Telegram signals, trade executions, and results. Include key stats like total trades, win/loss ratio, and current profit/loss.
- **Bot Control Panel**: Provide controls to start/stop the bot, switch between real and demo trading modes, and adjust trade parameters (e.g., trade amount, max daily trades) without editing configuration files.
- **Configuration Editor**: Allow users to view and modify configuration settings (e.g., Telegram channel, trade limits) directly in the TUI, with validation to prevent invalid inputs.
- **Trade History View**: Show a scrollable log of past signals and trades with details like timestamp, asset, direction, outcome, and profit/loss for analysis.
- **Account Status**: Display current Pocket Option account balance, connection status for both Telegram and Pocket Option, and any error states or warnings.
- **Signal Preview**: Show incoming Telegram messages or parsed signals before trade execution, with an option for manual confirmation if desired.
- **Logging Console**: Integrate a view of recent logs or errors for debugging without needing to check external log files.

### Implementation Considerations
- **Library Choice**: Use a Python TUI library like `urwid`, ` textual`, or `rich` for creating interactive interfaces in the terminal. `rich` is particularly suitable for modern, colorful layouts and tables.
- **Non-Blocking Design**: Ensure the TUI operates in a non-blocking manner to avoid interfering with the asyncio event loop used by Telethon for Telegram monitoring. Run the TUI in a separate thread or integrate it with asyncio if the library supports it.
- **Data Synchronization**: Implement safe data sharing between the bot's core logic and TUI for real-time updates. Use thread-safe queues or asyncio events to pass data like new signals or trade results to the UI.
- **User Input Handling**: Design intuitive key bindings or menu systems for navigation and control. Ensure input handling doesn't conflict with the bot's background operations.
- **Responsive Layout**: Create a responsive design that adapts to different terminal sizes, ensuring readability on various screen resolutions.
- **Performance Impact**: Minimize the performance overhead of the TUI by limiting refresh rates or updates to essential information only, preserving CPU resources for trade execution and signal processing.
- **Error Handling**: Display user-friendly error messages or alerts in the TUI for issues like connection loss, invalid configurations, or trade failures, with options to retry or adjust settings.
- **Integration Points**: Hook the TUI into `self_bot.py` at key points like initialization, signal detection, trade execution, and shutdown. Ensure the TUI can access or subscribe to the bot's stats and status updates.
- **Security**: Avoid displaying sensitive information like SSID or API credentials in the TUI. Mask or hide such data to prevent accidental exposure.

By focusing on these aspects, a TUI can significantly improve the usability and monitoring capabilities of the bot, making it more accessible for users and developers alike during trading sessions.

---

This report addresses the key concerns and requirements for the Modular SignalBot v1.5, providing a foundation for further development and maintenance. For additional details or specific code changes, refer to the respective files and documentation within the project repository.
