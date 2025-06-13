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

# Active Context

## What you're working on now

🎉 **PHASE 1 COMPLETED**: BinaryOptionsToolsV2 Foundation Setup (92.9% success rate)

I have successfully completed Phase 1 of the BinaryOptionsToolsV2 migration, establishing the foundation for migrating from PocketOptionAPI-v2 to the Rust-backed BinaryOptionsToolsV2 library. This represents a major step toward achieving 90% latency reduction and 600% throughput improvement in the HFT SignalSniper trading bot.

**Key Achievements:**
- ✅ BinaryOptionsToolsV2 library installed and tested (100% success rate)
- ✅ API compatibility verified with existing implementation (85.7% success rate)
- ✅ Migration adapter created for seamless transition
- ✅ Performance baseline established (current: $51,306.99 demo balance)
- ✅ Parameter mapping documented (4 changes needed for trade execution)
- ✅ Async API confirmed working perfectly

**Previous Work:** 59-second trade duration optimization feature remains implemented and functional.

## Recent changes

-   **59-Second Optimization Implementation**: Added comprehensive latency compensation feature
    -   Updated `config/bot_config.json` with new `trade_duration_optimization` section
    -   Modified `self_bot_v3_integrated.py` and `self_bot.py` with smart logic for 1-minute signals
    -   Created `59_SECOND_OPTIMIZATION_GUIDE.md` with comprehensive documentation
    -   Created `test_59_second_optimization.py` for verification (all tests passed)
-   **Configuration Enhancement**: Added configurable optimization settings:
    -   `enabled: true` - Master switch for the feature
    -   `use_59_second_trades: true` - Enables 59-second duration for 1-minute signals
    -   Selective application only to 1-minute signals, other durations work normally
-   **Performance Impact**: Provides 1-second safety buffer for consistent entry timing
-   **Verification**: All tests confirm correct implementation and expected behavior

## Next steps

-   Monitor the 59-second optimization in demo mode to verify real-world performance
-   Consider additional latency reduction strategies based on user feedback
-   Continue with any other optimization tasks or new feature requests
-   Maintain and update documentation as needed

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

# Tech Context

## Technologies used

-   **Programming Language**: Python 3
-   **Telegram Integration**: `telethon` library for connecting to Telegram as a user account.
-   **Pocket Option API**: A specific version of the Pocket Option API, `PocketOptionAPI-v2`, is used for trading operations.
-   **Timezone Handling**: `pytz` library for managing timezones, with UTC as the standard.
-   **Data Serialization**: `json` for storing and retrieving data from files.
-   **Asynchronous Programming**: `asyncio` for handling concurrent operations.
-   **Dependency Management**: `pip` with a `requirements.txt` file.
-   **Environment Variables**: `dotenv` for managing sensitive information like API keys.

## Development setup

-   **Operating System**: The bot is developed to run on a Linux environment, specifically an Ubuntu EC2 instance on AWS.
-   **Python Environment**: A virtual environment (`venv`) is used to manage project dependencies.
-   **Code Editor**: The development is being done in a modern code editor like VSCode, which provides features like integrated terminals and file management.
-   **Version Control**: `git` is used for version control, though the repository details are not specified in the provided context.

## Technical constraints

-   **WebSocket-Based Authentication**: The bot is constrained to using WebSocket-based SSIDs for Pocket Option authentication, as other methods are not reliable.
-   **SSID Expiry**: The SSIDs for Pocket Option have a limited lifespan (around 24 hours), which requires a mechanism for periodic updates.
-   **Telegram API Limits**: The bot must be mindful of Telegram's API rate limits to avoid being temporarily banned.
-   **Single-Threaded Event Loop**: `asyncio` operates on a single-threaded event loop, which means long-running synchronous tasks can block the entire application. This is mitigated by using `threading` for tasks like trade execution.

# Progress

## What works

-   **Telegram Connection**: The bot can successfully connect to Telegram using a user account and monitor the specified channel.
-   **Signal Parsing**: The bot is capable of parsing both single-message and two-message trading signals using regular expressions.
-   **Pocket Option Authentication**: The bot can authenticate with the Pocket Option API using a WebSocket-based SSID.
-   **Data Storage**: The system can store and retrieve data from JSON files, including signal history, trade history, and session data.
-   **Session Management**: The `SessionManager` can start, track, and end trading sessions.
-   **Basic Trade Execution**: The bot can execute trades in both test mode and real mode.
-   **Timezone Standardization**: All timezone-related operations have been standardized to UTC.
-   **59-Second Optimization**: Strategic latency compensation feature that reduces 1-minute trade durations to 59 seconds, providing a 1-second buffer for network delays and improving entry timing consistency.
-   **Comprehensive Latency Monitoring**: Full suite of latency monitoring tools for performance analysis and optimization.

## What's left to build

-   **Advanced Risk Management**: While basic risk management is in place, more advanced strategies (e.g., dynamic trade sizing, stop-loss) could be implemented.
-   **Automated SSID Refresh**: The process of refreshing the Pocket Option SSID is currently manual. A more automated solution is needed for long-term stability.
-   **Enhanced Error Handling**: While some error handling is in place, it could be made more robust to handle a wider range of potential issues (e.g., network disruptions, API errors).
-   **Strategy Analysis**: The bot currently logs data, but it does not yet have the capability to analyze this data to provide insights into trading strategies.
-   **Notifications**: A notification system (e.g., via Telegram or email) could be added to alert the user of important events, such as trade outcomes or critical errors.

## Progress status

The project is currently in a functional state, with the core features implemented and working. The recent focus has been on improving the robustness of the system by standardizing timezone handling. The next phase of development will likely focus on enhancing the bot's autonomy and adding more advanced features.
