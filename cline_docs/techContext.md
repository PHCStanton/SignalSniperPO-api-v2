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
