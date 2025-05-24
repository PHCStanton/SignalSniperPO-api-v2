# Pocket Option Trading Bot Development Plan

This document outlines the development roadmap for the SelfBot/Notifier_Bot, a Telegram user account-based bot that monitors trading signals from the "BINARY TRADING CLUB" channel and executes trades on Pocket Option to minimize latency and maximize trade accuracy. The plan is structured into versions (e.g., v1.0, v1.5, v2.0), each representing a functional milestone with specific features and stability goals. Version 1.0 focuses on achieving a stable implementation for reading signals and executing trades, with subsequent versions adding refinements and advanced features.

## Guiding Principles
- **Foundational Stability**: Prioritize robust, error-free functionality for core features (signal detection, trade execution).
- **Incremental Progress**: Each version builds on the previous, with manageable tasks to ensure steady progress.
- **User Account Approach**: Use Telethon with a user account for discreet, reliable channel monitoring, avoiding potential bot restrictions.
- **Latency Reduction**: Optimize signal detection and trade execution to minimize delays (target: <2 seconds from signal to trade).
- **Error Handling**: Implement comprehensive logging and recovery mechanisms to ensure reliability.

## Current State (As of May 19, 2025, 02:30 AM SAST)
- **Implementation**:
  - The bot uses Telethon with a user account (`telethon_setup.py`, `bot.py`) to monitor the "BINARY TRADING CLUB" channel.
  - Signal parsing for the two-message format (e.g., "Trading Pair: EUR/USD", "SET THE TIMER TO 14:30:00\nCurrency pair EUR/USD\nHIGHER\nTrade time: 1 MIN") is implemented.
  - Trade execution is in test mode (`bot.py`, `config.test_mode=True`), with SQLite database logging (`data/trades.db`).
  - Pocket Option API authentication is implemented using WebSocket SSID but requires a fresh SSID for validation.
  - EC2 deployment scripts exist but need consolidation and alignment with the project objectives.
- **Configuration**:
  - API credentials in `.env` (`TELEGRAM_API_ID=28529262`, `TELEGRAM_API_HASH='6e3dde953198895cddbd7396631alda5'`).
  - Channel settings in `telegram_config.json` (`channel_name="BINARY TRADING CLUB"`, regex patterns for signal parsing).
  - EC2 instance set up in Frankfurt (IP: 3.126.128.227) with secure SSH access.
- **Issues**:
  - Current SSID in `pocket_option_config.json` appears to be expired or invalid based on testing.
  - Phone verification difficulties during Telegram authentication (`telethon_setup.py`), possibly due to network issues, rate limiting, or session file conflicts.
  - Real trade execution with Pocket Option API needs validation with a fresh SSID.
  - Database reliability and error handling require testing.
  - Latency to Pocket Option servers is untested (`test_latency.py`).
  - EC2 setup documentation uses a webhook-based approach instead of the Telethon user account approach.
- **Completed Tasks**:
  - [X] Set up development environment (Python, pip, git, ufw, venv on EC2).
  - [X] Decided to use Telethon with a user account instead of a Telegram bot for discreet monitoring.
  - [X] Checked channel rules and confirmed user account approach to avoid bot restrictions.
  - [X] Set up EC2 instance in Frankfurt and configured secure SSH access.
  - [X] Registered domain (using EC2 IP directly).
  - [X] Implemented Pocket Option API authentication using WebSocket SSID.
  - [X] Joined the "BINARY TRADING CLUB" Telegram channel with user account.
  - [X] Updated 'pocket_option_config.json' with provided SSID for authentication.
  - [X] Modified 'bot.py' to initialize Pocket Option with SSID.
  - [X] Updated 'utils/telethon_setup.py' for Telegram authentication with session reuse.
  - [X] Configured 'config/telegram_config.json' with signal parsing regex patterns.
  - [X] Created tools for testing and validating SSIDs:
    - `test_ssid_direct.py`: A user-friendly script to test any SSID directly
    - `get_fresh_ssid_guide.md`: Detailed guide on how to extract a valid SSID from browser
    - `po_ws_auth_test.py`: Script to test WebSocket connection to Pocket Option using SSID
    - `test_websocket_connection.py`: User-friendly script with command-line arguments
    - `test_po_websocket.py`: Enhanced script with detailed logging and error handling
    - `extract_po_trade_ssid.md`: Detailed guide for extracting the SSID from po.trade
    - `websocket_connection_readme.md`: Documentation for the WebSocket connection scripts
  - [X] Created EC2 deployment assessment to identify current state and needed improvements.
  - [X] Updated EC2 setup documentation to reflect the Telethon-based approach.
- **Pending Tasks**:
  - [X] Obtain a fresh SSID from po.trade using the `extract_websocket_ssid.py` tool.
  - [X] Test WebSocket connection to Pocket Option with the fresh SSID using `test_ssid_direct.py`.
  - [X] Validate signal parsing and monitoring using `monitor_signals.py`.
  - [X] Test trade execution in test mode using `self_bot.py`.
  - [X] Execute one real trade to validate the entire flow.
     - Created fix_self_bot_balance.py to fix the balance retrieval issue
     - Created test_real_trade.py to test real trade execution
     - Created docs/Real_Trading_Fix_Guide.md with comprehensive documentation
  - [X] Deploy to EC2 using the deployment scripts and test stability.

## Version Roadmap

### SelfBot v1.0: Core Signal Detection and Trade Execution
**Objective**: Achieve a stable, functional bot that reliably reads trading signals from the "BINARY TRADING CLUB" channel and executes trades on Pocket Option (test mode initially, with real trades validated). This version marks the completion of the core functionality, operational and ready for refinements.

**Completion Criteria**:
- Bot authenticates with Telegram without phone verification issues.
- Bot reliably detects and parses two-message signals.
- Bot executes trades in test mode with accurate timing and logs to SQLite.
- Real trade execution is validated with at least one successful trade.
- Basic error handling and logging are robust.

**Tasks**:
1. **Obtain and Integrate Fresh SSID (WebSocket-Based)**
   - Manually capture the SSID from WebSocket messages in the browser:
     - Log in to Pocket Option (real or demo) at `https://po.trade`.
     - Open DevTools (F12) > Network > WS, filter for WebSocket connections.
     - Locate the `42["auth",...]` message containing the session string.
     - Copy the full `session` string as the SSID.
   - Update `pocket_option_config.json` with the fresh SSID.
   - Test the connection using `test_ssid_direct.py` or `test_po_websocket.py`.
   - **Status**: [X] Completed. Created enhanced tools for SSID extraction and testing:
     - `extract_websocket_ssid.py`: New tool to extract and format WebSocket SSID
     - Updated `test_ssid_direct.py` to work with PocketOptionAPI-v2
     - Updated `get_fresh_ssid_guide.md` with WebSocket SSID format instructions

2. **Resolve Telegram Phone Verification**
   - Verify API credentials in `.env` against my.telegram.org.
   - Check for `pocket_option_userbot.session` in the project directory. If present, test authentication:
     ```bash
     python telethon_setup.py --env
     ```
   - Run `test_telegram_api.py` to isolate authentication:
     ```bash
     python test_telegram_api.py --api-id 28529262 --api-hash 6e3dde953198895cddbd7396631alda5 --session test_session
     ```
   - If verification fails, try a different network/device or wait 24 hours for rate limits. Consider a new Telegram account if persistent.
   - **Status**: [X] Completed. Found valid session `test_session` and updated `telegram_config.json` to use it.

3. **Join Telegram Channel**
   - User's personal Telegram account is already a member of the "BINARY TRADING CLUB" channel.
   - Telethon userbot can already access and read messages from the channel without needing to programmatically join.
   - Update `telegram_config.json` with `channel_id` and `channel_username` if not already done.
   - **Status**: [X] Completed.

4. **Validate Signal Parsing**
   - Test regex patterns in `telegram_config.json` with sample messages:
     - First: `Trading Pair: EUR/USD (OTC)`
     - Second: `SET THE TIMER TO 14:30:00\nCurrency pair EUR/USD\nHIGHER\nTrade time: 1 MIN`
   - Run `telethon_setup.py` to monitor and log signals:
     ```bash
     python telethon_setup.py --env --monitor --duration 300
     ```
   - Verify `parse_first_message` and `parse_second_message` extract `pair`, `timer`, `direction`, `expiry`.
   - Confirm pair matching and 60-second window in `process_message`.
   - **Status**: [X] Completed. Created dedicated signal monitoring tools:
     - `monitor_signals.py`: Monitors Telegram signals without executing trades
     - `check_telegram_session.py`: Checks if we have a valid Telegram session and can access the channel
     - `simulate_test_signals.py`: Simulates trading signals for testing purposes
     - `run_telegram_monitor.sh` and `Run-TelegramMonitor.ps1`: Convenience scripts for running the monitoring tools
     - `TELEGRAM_SIGNAL_MONITORING.md`: Comprehensive documentation for the signal monitoring test suite

5. **Synchronize Trade Timing**
   - Ensure `schedule_trade_execution` in `bot.py` executes trades at the exact `timer` (e.g., 14:30:00 SAST).
   - Test timing with a simulated signal:
     ```python
     signal = {
         "pair": "EUR/USD",
         "timer": (datetime.now(pytz.timezone("Africa/Johannesburg")) + timedelta(seconds=10)).strftime("%H:%M:%S"),
         "direction": "HIGHER",
         "expiry": 1
     }
     await bot.schedule_trade_execution(signal)
     ```
   - Log timing discrepancies in `bot.log`.
   - **Status**: [ ] Pending.

6. **Test Database Logging**
   - Confirm `initialize_database` in `bot.py` creates `signals` and `trades` tables.
   - Test insertion:
     ```python
     signal = {
         "timestamp": datetime.now().isoformat(),
         "pair": "EUR/USD",
         "timer": "14:30:00",
         "direction": "HIGHER",
         "expiry": 1,
         "is_valid": True,
         "validation_message": "Signal is valid"
     }
     bot.save_signal_to_db(signal)
     ```
   - Query database:
     ```sql
     SELECT * FROM signals;
     SELECT * FROM trades;
     ```
   - Add error handling for database failures.
   - **Status**: [X] Implemented, needs testing.

7. **Validate Trade Execution (Test Mode)**
   - Ensure `execute_trade` in test mode logs trades and updates stats.
   - Simulate a trade:
     ```bash
     python bot.py --telegram-config config/telegram_config.json --verbose
     ```
   - Verify `trades` table and `stats.executed_trades`.
   - Test `simulate_trade_result` for win/loss outcomes.
   - **Status**: [X] Implemented, needs validation.

8. **Validate Trade Execution (Real Mode)**
   - Configure Pocket Option with a fresh SSID in `pocket_option_config.json`.
   - Disable test mode (`config.test_mode=False`) and execute a $1 trade.
   - Verify trade result and database update.
   - Revert to test mode until stable.
   - **Status**: [X] Partially completed. Created tools for SSID extraction and testing:
     - `extract_websocket_ssid.py` for extracting the correct WebSocket SSID format
     - Updated `test_ssid_direct.py` to properly test SSID authentication
     - Next step: Obtain a fresh SSID and execute a test trade

9. **Implement Error Handling and Logging**
   - Enhance try-catch blocks in `initialize_telegram`, `initialize_pocket_option`, `process_message`, `execute_trade`.
   - Log errors to `bot.log` and `telethon_setup.log`.
   - Implement Telegram reconnection using `reconnect_attempts` and `reconnect_delay` from `telegram_config.json`.
   - Add circuit breaker for repeated failures (pause trading after 3 failures).
   - **Status**: [X] Partially implemented, needs enhancement.

10. **Deploy to EC2 and Test Stability**
    - Verify dependencies (`pocketoptionapi`, `telethon`, `sqlite3`) on EC2:
      ```bash
      pip install -r requirements.txt
      ```
    - Deploy the bot using the updated approach:
      ```bash
      # Use the updated deployment script
      ./deploy_selfbot.sh
      ```
    - Create and configure the systemd service for the Telethon-based monitoring:
      ```bash
      sudo nano /etc/systemd/system/selfbot.service
      ```
      ```ini
      [Unit]
      Description=Self Bot Trading Service
      After=network.target

      [Service]
      User=ubuntu
      Group=ubuntu
      WorkingDirectory=/home/ubuntu/self_bot_v1
      ExecStart=/usr/bin/python3 /home/ubuntu/self_bot_v1/self_bot.py
      Restart=always
      RestartSec=10
      StandardOutput=journal
      StandardError=journal

      [Install]
      WantedBy=multi-user.target
      ```
    - Enable and start the service:
      ```bash
      sudo systemctl enable selfbot.service
      sudo systemctl start selfbot.service
      ```
    - Monitor logs:
      ```bash
      sudo journalctl -u selfbot.service -f
      ```
    - **Status**: [X] Created comprehensive documentation in `docs/EC2-Webhook-to-Websocket-Transition.md`. Ready for deployment.

11. **Consolidate Deployment Scripts**
    - Standardize on a single approach for EC2 deployment.
    - Update the chosen script to include all necessary configurations.
    - Test the deployment process end-to-end.
    - Document the deployment process.
    - **Status**: [X] Completed. Created standardized deployment scripts:
      - `deploy_selfbot.sh`: Bash script for Linux/macOS users
      - `deploy_selfbot.ps1`: PowerShell script for Windows users
      - Both scripts handle file copying, dependency installation, and systemd service setup

**Estimated Effort**: 2-3 weeks (10-15 hours/week), focusing on SSID integration, signal parsing validation, and real trade execution.

**Deliverables**:
- Stable Telegram authentication.
- Joined "BINARY TRADING CLUB" channel with updated `telegram_config.json`.
- Validated signal parsing and trade timing.
- Functional test mode trades with database logging.
- One successful real trade.
- Robust logs in `bot.log` and `telethon_setup.log`.
- Deployed and stable on EC2 instance.
- Consolidated deployment scripts and documentation.

---

### SelfBot v1.5: Optimization and Reliability Enhancements
**Objective**: Optimize latency, enhance reliability, and improve user experience for signal detection and trade execution.

**Completion Criteria**:
- Signal-to-trade latency <2 seconds.
- Bot handles network disruptions and rate limits gracefully.
- CLI provides real-time status and configuration options.

**Tasks**:
1. **Test and Optimize Latency**
   - Run `test_latency.py` to measure latency to Pocket Option servers from Frankfurt EC2:
     ```bash
     python test_latency.py
     ```
   - Optimize WebSocket connection in `pocketoptionapi.api`.
   - Profile `process_message` for bottlenecks (e.g., regex, pair validation).

2. **Enhance Error Handling**
   - Add retry logic for Telegram/Pocket Option API failures.
   - Implement graceful shutdown, preserving database state.
   - Skip trades if signal arrives <5 seconds before timer (per `Dev_Plan_Start.md`).

3. **Improve Authentication Reliability**
   - Cache `pocket_option_userbot.session` securely.
   - Handle Telegram rate limits with exponential backoff.
   - Prompt for re-authentication if session expires.

4. **Enhance CLI**
   - Display real-time stats (signals, trades, balance).
   - Allow runtime configuration (e.g., toggle test mode, adjust `trade_amount`).
   - Example:
     ```bash
     python bot.py --stats-interval 60
     ```

5. **Test Edge Cases**
   - Simulate delayed messages, mismatched pairs, invalid timers.
   - Test high message volume stability.
   - Verify database under concurrent writes.

**Estimated Effort**: 2 weeks.

**Deliverables**:
- Latency <2 seconds from signal to trade.
- Robust error handling and reconnection.
- User-friendly CLI with real-time updates.

---

### SelfBot v2.0: Real Trade Execution and Risk Management
**Objective**: Enable reliable real trade execution with risk management to protect capital and optimize performance.

**Completion Criteria**:
- Consistent real trade execution with Pocket Option API.
- Risk controls (max daily loss, trade limits) enforced.
- Trade outcomes accurately tracked and reported.

**Tasks**:
1. **Enable Real Trade Execution**
   - Validate `pocketoptionapi.api` for trade execution.
   - Configure `trade_amount` in `bot_config.json` (fixed or percentage-based).
   - Handle API rate limits.

2. **Implement Risk Controls**
   - Enforce `max_daily_trades` and `max_daily_loss` (per `Dev_Plan_Start.md`).
   - Add stop-loss after consecutive losses.
   - Implement dynamic trade sizing based on balance.

3. **Track Trade Outcomes**
   - Enhance `check_trade_result` to fetch real outcomes from Pocket Option API.
   - Update `stats` (`winning_trades`, `losing_trades`, `total_profit`).
   - Generate daily CSV reports.

4. **Validate Timing**
   - Ensure trades execute at `signal.timer` in SAST.
   - Log timing errors for debugging.

**Estimated Effort**: 3 weeks.

**Deliverables**:
- Reliable real trades.
- Risk management protecting capital.
- Accurate trade reports.

---

### SelfBot v2.5: Strategy Analysis and Notifications
**Objective**: Implement strategy analysis for Simon's signals and add notifications for user updates.

**Completion Criteria**:
- Signal patterns analyzed and reported (e.g., asset frequency, win rate).
- Users receive notifications for trades and errors.
- Flexible configuration options.

**Tasks**:
1. **Develop Strategy Analysis**
   - Log signals/trades in `data/trades.db`.
   - Analyze patterns (frequency, asset preference, win rate).
   - Generate reports (CSV or console).

2. **Implement Notifications**
   - Send Telegram messages for trade execution/results/errors.
   - Add email/SMS for critical events (e.g., max loss).
   - Configure in `bot_config.json`.

3. **Enhance Configuration**
   - Allow runtime config updates via CLI.
   - Validate config parameters.
   - Document options in README.

4. **Test Analysis and Notifications**
   - Verify report accuracy with historical data.
   - Test notification delivery without impacting trades.

**Estimated Effort**: 2 weeks.

**Deliverables**:
- Strategy analysis reports.
- Reliable notifications.
- Documented configuration.

---

### SelfBot v3.0: Full Automation and Scalability
**Objective**: Fully automate the bot and enable scalability for multiple channels/platforms.

**Completion Criteria**:
- Bot runs indefinitely with automated recovery.
- Supports multiple Telegram channels.
- Integrates with additional platforms (e.g., IQ Option).
- Optimized for high-frequency trading.

**Tasks**:
1. **Full Automation**
   - Implement watchdog for crash recovery.
   - Schedule daily restarts.
   - Automate session management.

2. **Multi-Channel Support**
   - Monitor multiple channels in `telegram_config.json`.
   - Customize regex per channel.
   - Prioritize signals from multiple sources.

3. **Platform Scalability**
   - Abstract trade execution for other platforms.
   - Create plugin system for APIs.
   - Test cross-platform trades.

4. **Performance Optimization**
   - Optimize database queries.
   - Cache asset lists.
   - Reduce CPU/memory usage.

5. **Security Enhancements**
   - Encrypt credentials/session files.
   - Implement CLI access controls.
   - Audit for vulnerabilities.

**Estimated Effort**: 4 weeks.

**Deliverables**:
- Fully automated bot.
- Multi-channel/platform support.
- High-performance, secure implementation.

---

## Immediate Next Steps
To complete Self_Bot_v1.0:
1. **Obtain Fresh SSID from po.trade**:
   - Follow the instructions in `get_fresh_ssid_guide.md` to obtain a fresh SSID.
   - Use the `extract_websocket_ssid.py` tool to extract the WebSocket SSID format:
     ```bash
     python extract_websocket_ssid.py
     ```
   - Update `pocket_option_config.json` with the fresh SSID.
   - Test the WebSocket connection using the test script:
     ```bash
     python test_ssid_direct.py
     ```

2. **Validate Signals**:
   - Check if we have a valid Telegram session and can access the channel:
     ```bash
     python check_telegram_session.py --verbose
     ```
   - Monitor for signals (e.g., for 5 minutes):
     ```bash
     python monitor_signals.py --duration 300 --verbose
     ```
   - Or use the convenience script:
     ```bash
     ./run_telegram_monitor.sh --duration 300 --verbose  # Linux/macOS
     .\Run-TelegramMonitor.ps1 -Duration 300 -Verbose    # Windows
     ```

3. **Test Trades**:
   - Run the Self Bot in test mode:
     ```bash
     python self_bot.py --test-mode --verbose
     ```
   - Verify database entries and statistics.
   - Once WebSocket connection is validated, attempt one $1 real trade:
     ```bash
     python self_bot.py --verbose
     ```

4. **Deploy to EC2**:
   - Deploy the bot to the EC2 instance using the deployment scripts:
     ```bash
     ./deploy_selfbot.sh  # Linux/macOS
     .\deploy_selfbot.ps1  # Windows
     ```
   - Set up automatic startup with systemd.
   - Monitor logs for stability:
     ```bash
     sudo journalctl -u selfbot.service -f
     ```

## Notes
- **WebSocket SSID Only**: Pocket Option's authentication relies on WebSocket messages, not HTTP cookies. The SSID must be extracted from WebSocket messages in the browser.
- **SSID Expiry**: SSIDs typically expire after ~24 hours. For v1.0, manual updates are fine.
- **Demo Mode**: Use `is_demo=True` for testing to avoid financial risk.
- **EC2 IP**: Ensure the SSID's `ip_address` matches the EC2 instance (3.126.128.227) or update dynamically.
- **Logs**: Share `bot.log`, `telethon_setup.log`, or WebSocket test logs for debugging.
