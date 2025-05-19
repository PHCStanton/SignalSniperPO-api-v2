### THE CONTENTS OF THIS FILE MAY CHANGE AS IT IS MEANT FOR TIMELY UPDATES AND NOT FOR PERMANENT RECORDS.

**Subject: Focus on WebSocket SSID for Pocket Option and v1.0 Core Functionality**

Dear Coding Agent,

To ensure we deliver SelfBot v1.0 efficiently—capable of reading trading signals from the "BINARY TRADING CLUB" Telegram channel and executing trades on Pocket Option with minimal latency—we need to focus exclusively on the critical path. Our top priority is obtaining the Pocket Option session ID (SSID) via WebSocket messages, as po.trade’s authentication is **WebSocket-based, not cookie-based**. Attempting to extract the SSID from HTTP cookies (Application > Cookies) is not viable, as the platform does not store session data in traditional cookies. We must avoid wasting time on cookie-based methods or redundant test files and concentrate on integrating the SSID into the bot, ensuring Telegram API stability, and validating trade execution on our Ubuntu EC2 server (3.126.128.227). Let’s streamline efforts to achieve a stable v1.0 that executes trades reliably, with all components (Telegram, Pocket Option, database) working seamlessly.

### Why WebSocket is the Only Option
Pocket Option’s authentication relies on WebSocket messages, specifically the `42["auth",...]` message containing the SSID (e.g., `a:4:{s:10:"session_id";s:32:"bde3d74bbc70c9e768874d0e3ec00fb4";...}dbad27acafe64d44d2a0ee59fe9380e1`). This is due to:
- **WebSocket-Based Sessions**: The platform transmits session data via WebSocket, not HTTP cookies, to manage authentication securely.
- **No Cookie Storage**: HTTP cookies are either absent or HTTP-only and irrelevant for API authentication, as confirmed by attempts across multiple browsers.
- **reCAPTCHA Protection**: Traditional login flows (username/password) are blocked by reCAPTCHA, making SSID-based login via `pocketoptionapi` the only supported method.

We will manually capture the SSID from WebSocket messages in the browser (Network > WS > Messages), as this is the most reliable approach. Ignore any test files or documentation suggesting cookie extraction (e.g., Application > Cookies) to avoid misdirection. Our goal is to integrate this SSID into the bot, resolve Telegram phone verification, and validate trade execution for v1.0.

### v1.0 Objective and Scope
SelfBot v1.0 must:
- **Read Signals**: Monitor "BINARY TRADING CLUB" via Telethon (user account) and parse two-message signals (e.g., "Trading Pair: EUR/USD", "SET THE TIMER TO 14:30:00\nCurrency pair EUR/USD\nHIGHER\nTrade time: 1 MIN").
- **Execute Trades**: Execute trades on Pocket Option in test mode, with one validated real trade ($1) to confirm API integration.
- **Log Data**: Store signals and trades in `data/trades.db` (SQLite).
- **Run on Ubuntu EC2**: Operate reliably on the Frankfurt EC2 instance (3.126.128.227) with secure SSH and minimal latency.
- **Handle Errors**: Implement robust logging and reconnection logic for Telegram and Pocket Option.

We will not pursue advanced features (e.g., strategy analysis, multi-channel support) or alternative authentication methods until v1.0 is complete. Focus on thorough testing of these core components.

### Action Plan for v1.0

#### 1. Obtain and Integrate SSID (WebSocket-Based)
I will manually capture the SSID from WebSocket messages in the browser:
- **Steps**:
  - Log in to Pocket Option (real or demo) at `https://po.trade`.
  - Open DevTools (F12) > Network > WS, filter for WebSocket connections (e.g., `wss://.../ws`).
  - Locate the `42["auth",...]` message, e.g.:
    ```json
    42["auth",{"session":"a:4:{s:10:\"session_id\";s:32:\"bde3d74bbc70c9e768874d0e3ec00fb4\";s:10:\"ip_address\";s:12:\"169.0.228.13\";s:10:\"user_agent\";s:111:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1747546565;}dbad27acafe64d44d2a0ee59fe9380e1","isDemo":0,"uid":101002476,"platform":2}]
    ```
  - Copy the full `session` string as the SSID.
- **Your Task**:
  - Update `pocket_option_config.json` with the SSID I provide:
    ```json
    {
      "ssid": "a:4:{s:10:\"session_id\";s:32:\"bde3d74bbc70c9e768874d0e3ec00fb4\";s:10:\"ip_address\";s:12:\"169.0.228.13\";s:10:\"user_agent\";s:111:\"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36\";s:13:\"last_activity\";i:1747546565;}dbad27acafe64d44d2a0ee59fe9380e1",
      "is_demo": true
    }
    ```
  - Modify `bot.py` to initialize Pocket Option with the SSID:
    ```python
    from pocketoptionapi.stable_api import PocketOption

    async def initialize_pocket_option(self):
        try:
            ssid = self.config.get("pocket_option", {}).get("ssid")
            if not ssid:
                logger.error("No SSID provided in configuration")
                return False
            self.account = PocketOption(ssid=ssid)
            check, message = await self.account.connect()
            if check:
                logger.info("Pocket Option connected successfully")
                is_demo = self.config.get("pocket_option", {}).get("is_demo", False)
                await self.account.change_balance("PRACTICE" if is_demo else "REAL")
                logger.info(f"Balance: {await self.account.get_balance()}")
                return True
            else:
                logger.error(f"Pocket Option connection failed: {message}")
                return False
        except Exception as e:
            logger.error(f"Pocket Option initialization failed: {str(e)}")
            return False
    ```
  - Test the connection on the EC2 instance:
    ```bash
    python bot.py --telegram-config config/telegram_config.json --verbose
    ```
  - Verify logs (`bot.log`) for successful connection and balance retrieval.
  - **Test**: Execute a demo trade ($1, EUR/USD, 60 seconds) to confirm SSID validity.

#### 2. Resolve Telegram Phone Verification
The Telegram authentication issue (phone verification in `telethon_setup.py`) is blocking channel access. We must resolve this to monitor signals.

- **Your Task**:
  - Update `telethon_setup.py` to prioritize session reuse and handle verification errors:
    ```python
    async def initialize(self) -> None:
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()
            if await self.client.is_user_authorized():
                logger.info("Authenticated using existing session")
                return True
            logger.info("Starting phone verification...")
            phone = input("Enter phone number (e.g., +27123456789): ")
            await self.client.send_code_request(phone)
            code = input("Enter the code received: ")
            await self.client.sign_in(phone, code)
            logger.info("Successfully signed in")
            return True
        except Exception as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
    ```
  - Test authentication on the EC2 instance:
    ```bash
    python telethon_setup.py --env
    ```
  - Check for `pocket_option_userbot.session`. If present, authentication should skip verification.
  - If verification fails, try a different network or wait 24 hours for rate limits. I can provide a new phone number if needed.
  - Join the "BINARY TRADING CLUB" channel:
    ```bash
    python telethon_setup.py --env --channel "BINARY TRADING CLUB"
    ```
  - Update `telegram_config.json` with `channel_id` and `channel_username` after joining.
  - **Test**: Monitor for 5 minutes to log signals:
    ```bash
    python telethon_setup.py --env --monitor --duration 300
    ```

#### 3. Validate Signal Parsing
Signal parsing is implemented but needs thorough testing to ensure reliability.

- **Your Task**:
  - Test regex patterns in `telegram_config.json` with sample messages:
    ```json
    {
      "channel_name": "BINARY TRADING CLUB",
      "first_message_regex": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
      "second_message_regex": {
        "timer": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
        "pair": "Currency pair (\\w+/\\w+)",
        "direction": "(HIGHER|LOWER)",
        "expiry": "Trade time: (\\d+) MIN"
      },
      "pair_match_window": 60
    }
    ```
  - Run `telethon_setup.py` to process signals:
    ```bash
    python telethon_setup.py --env --monitor --duration 300
    ```
  - Verify `parse_first_message` and `parse_second_message` extract `pair`, `timer`, `direction`, `expiry`, and match pairs within 60 seconds.
  - Log parsed signals to `bot.log` and `data/trades.db`.
  - **Test**: Simulate signals using `simulate_signals.py` (updated for two-message format) and confirm database entries:
    ```sql
    SELECT * FROM signals;
    ```

#### 4. Synchronize and Test Trade Execution
Trade execution must occur at the exact `timer` (e.g., 14:30:00 SAST) in test mode, with one real trade validated.

- **Your Task**:
  - Ensure `schedule_trade_execution` in `bot.py` aligns with `timer` in SAST:
    ```python
    async def schedule_trade_execution(self, signal):
        try:
            timer = datetime.strptime(signal["timer"], "%H:%M:%S").replace(
                tzinfo=pytz.timezone("Africa/Johannesburg")
            )
            now = datetime.now(pytz.timezone("Africa/Johannesburg"))
            delay = (timer - now).total_seconds()
            if delay < 5:
                logger.warning("Signal too late, skipping trade")
                return
            await asyncio.sleep(max(0, delay))
            trade_result = await self.execute_trade(signal)
            self.save_trade_to_db(signal, trade_result)
            logger.info(f"Trade executed: {signal['pair']} {signal['direction']}")
        except Exception as e:
            logger.error(f"Trade execution failed: {str(e)}")
    ```
  - Test in test mode:
    ```bash
    python bot.py --telegram-config config/telegram_config.json --verbose
    ```
  - Simulate a trade:
    ```python
    signal = {
        "pair": "EUR/USD",
        "timer": (datetime.now(pytz.timezone("Africa/Johannesburg")) + timedelta(seconds=10)).strftime("%H:%M:%S"),
        "direction": "HIGHER",
        "expiry": 1
    }
    await bot.schedule_trade_execution(signal)
    ```
  - Verify `trades` table and stats (`stats.executed_trades`).
  - For real trade validation:
    - Set `config.test_mode=False` and `is_demo=False` in `pocket_option_config.json`.
    - Execute one $1 trade using the SSID.
    - Revert to test mode.
  - **Test**: Confirm trade timing (<2 seconds latency) and database logging:
    ```sql
    SELECT * FROM trades;
    ```

#### 5. Ensure EC2 Stability
The Ubuntu EC2 instance (3.126.128.227) must run the bot reliably.

- **Your Task**:
  - Verify dependencies (`pocketoptionapi`, `telethon`, `sqlite3`) on EC2:
    ```bash
    pip install -r requirements.txt
    ```
  - Deploy the bot using `deploy.sh`:
    ```bash
    ./deploy.sh
    ```
  - Set up automatic startup (e.g., `systemd` service):
    ```bash
    sudo nano /etc/systemd/system/selfbot.service
    ```
    ```ini
    [Unit]
    Description=SelfBot Trading Service
    After=network.target

    [Service]
    User=ubuntu
    WorkingDirectory=/home/ubuntu/selfbot
    ExecStart=/home/ubuntu/selfbot/venv/bin/python bot.py --telegram-config config/telegram_config.json
    Restart=always

    [Install]
    WantedBy=multi-user.target
    ```
    ```bash
    sudo systemctl enable selfbot.service
    sudo systemctl start selfbot.service
    ```
  - Monitor logs:
    ```bash
    tail -f bot.log
    ```
  - **Test**: Run the bot for 1 hour on EC2, monitoring signals and test trades.

#### 6. Enhance Error Handling
Robust error handling is critical for v1.0 stability.

- **Your Task**:
  - Add try-catch blocks in `initialize_telegram`, `initialize_pocket_option`, `process_message`, `execute_trade`.
  - Implement reconnection logic:
    ```python
    async def reconnect_telegram(self):
        for attempt in range(self.config.get("reconnect_attempts", 3)):
            try:
                await self.client.connect()
                if await self.client.is_user_authorized():
                    logger.info("Reconnected to Telegram")
                    return True
                await asyncio.sleep(self.config.get("reconnect_delay", 60))
            except Exception as e:
                logger.error(f"Reconnection attempt {attempt + 1} failed: {str(e)}")
        logger.error("Failed to reconnect to Telegram")
        return False
    ```
  - Add circuit breaker for repeated failures (pause after 3 failures).
  - Log all errors to `bot.log` and `telethon_setup.log`.
  - **Test**: Simulate network disruptions (e.g., disconnect EC2 network) and verify reconnection.

### Testing Strategy
To ensure v1.0 reliability:
- **Unit Tests**: Test signal parsing with `simulate_signals.py`.
- **Integration Tests**: Verify Telegram → Pocket Option → database flow.
- **System Test**: Run the bot on EC2 for 1 hour, processing live signals and executing test trades.
- **Latency Test**: Confirm trade execution within 2 seconds of `timer`.
- **Error Test**: Simulate API failures and verify recovery.

Use only `test_telegram_api.py` for Telegram authentication and `simulate_signals.py` for signal parsing. Ignore other test files to avoid distraction.

### Immediate Tasks
1. **Integrate SSID**:
   - Await my provided SSID and update `pocket_option_config.json`.
   - Test Pocket Option connection and demo trade.
2. **Fix Telegram Authentication**:
   - Update `telethon_setup.py` and join the channel.
   - Test signal monitoring for 5 minutes.
3. **Validate Core Flow**:
   - Test signal parsing, trade execution (test mode), and database logging on EC2.
   - Perform one real $1 trade.
4. **Deploy and Monitor**:
   - Deploy to EC2 with `systemd` service.
   - Monitor logs for 1 hour.

### Notes
- **No Cookie-Based Methods**: Do not explore HTTP cookies or alternative authentication. WebSocket SSID is the only path.
- **SSID Expiry**: I’ll provide a fresh SSID daily, as they expire ~24 hours. For v1.0, manual updates are fine.
- **Demo Mode**: Use `is_demo=True` for testing to avoid financial risk.
- **EC2 IP**: Ensure the SSID’s `ip_address` matches the EC2 instance (3.126.128.227) or update dynamically.
- **Logs**: Share `bot.log` or `telethon_setup.log` for any errors.

Let’s focus solely on these tasks to deliver v1.0. No diversions to strategy analysis, multi-platform support, or cookie-based tests. Please confirm receipt and start on the Telegram authentication and SSID integration tasks. I’ll provide the SSID soon.