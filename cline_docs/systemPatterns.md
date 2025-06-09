# System Patterns

## How the system is built

The system is built as a Python-based application that runs on a remote EC2 server. It consists of several key components that work together to achieve the goal of automated trading.

-   **Telegram Client**: A `telethon` user account is used to connect to Telegram and monitor a specific channel for trading signals. This approach is chosen for its discretion and ability to avoid bot detection.
-   **Signal Parsing**: The bot uses regular expressions to parse incoming messages and identify valid trading signals. It can handle both single-message and two-message signal formats.
-   **Pocket Option Integration**: The bot interacts with the Pocket Option platform using the `PocketOptionAPI-v2`. Authentication is handled via a WebSocket-based SSID, which is a more reliable method than traditional cookie-based sessions.
-   **Data Storage**: The system uses JSON files for data storage instead of a SQLite database to avoid locking issues. This includes storing signal history, trade history, and session data.
-   **Session Management**: A `SessionManager` class is used to track trading sessions, including start/end times, balances, and trade statistics. This follows a singleton pattern to ensure a single, consistent session is maintained.
-   **Configuration**: The bot's behavior is controlled by several JSON configuration files, including `bot_config.json`, `telegram_config.json`, and `pocket_option_config.json`.

## Key technical decisions

-   **User Account over Bot Account**: A Telegram user account is used for monitoring to avoid potential restrictions and to operate more discreetly.
-   **WebSocket SSID Authentication**: This method was chosen for Pocket Option authentication because it is more stable and reliable than cookie-based methods, which are often protected by reCAPTCHA.
-   **JSON for Data Storage**: To prevent database locking issues that can occur with SQLite in a multi-threaded environment, the system uses simple JSON files for data persistence.
-   **Asynchronous Operations**: The bot is built on `asyncio` to handle network operations (like receiving Telegram messages and interacting with the Pocket Option API) efficiently.
-   **UTC as Standard Timezone**: All timezone-related operations are standardized to UTC to prevent any confusion or errors that could arise from using local timezones.

## Architecture patterns

-   **Event-Driven Architecture**: The bot operates on an event-driven model, where it reacts to new messages in the Telegram channel.
-   **Singleton Pattern**: The `SessionManager` is implemented as a singleton to ensure that there is only one active trading session at any given time.
-   **Modular Design**: The system is broken down into several modules, each with a specific responsibility (e.g., `SignalMonitor`, `AmountCalculator`, `JSONStorageManager`), which makes the codebase easier to maintain and extend.
