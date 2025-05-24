# Tonight's Trading Session Preparation (22:00 SAST)

This document provides a step-by-step guide to prepare for tonight's trading session at 22:00 SAST with the SelfBot v1.0.

## Preparation Timeline

| Time (SAST) | Action |
|-------------|--------|
| 21:30 | Refresh SSID if needed |
| 21:35 | Verify configuration |
| 21:40 | Test connections |
| 21:45 | Start the bot |
| 22:00 | Trading session begins |

## Step 1: Refresh SSID (21:30 SAST)

SSIDs typically expire after ~24 hours. If you've been testing throughout the day, you'll need to refresh your SSID before the trading session.

1. Get a fresh SSID from Pocket Option:
   - Log in to your Pocket Option account
   - Open browser developer tools (F12)
   - Go to Network tab
   - Filter for "websocket"
   - Look for the SSID in the connection message

2. Update your configuration:
   ```
   python refresh_ssid.py
   ```
   - Enter the new SSID when prompted
   - Confirm the update

3. Verify the SSID is valid:
   ```
   python test_ssid_direct.py
   ```
   - Enter the SSID when prompted
   - Choose 'n' for demo account to use real account
   - Verify successful connection

## Step 2: Verify Configuration (21:35 SAST)

1. Check bot configuration:
   ```
   python restart_bot.py
   ```
   - When asked if you want to stop the bot, choose 'n'
   - When asked if you want to update configuration, choose 'y'
   - Verify test mode is disabled
   - Set trade amount to $1
   - When asked to start the bot, choose 'n'

2. Manually verify configuration files if needed:
   - `config/bot_config.json`: Ensure `"test_mode": false` and `"trade_amount": 1`
   - `config/pocket_option_config.json`: Ensure SSID is fresh and `"is_demo": false`
   - `config/telegram_config.json`: Verify channel ID is correct

## Step 3: Test Connections (21:40 SAST)

1. Test Telegram connection:
   ```
   python check_telegram_session.py
   ```
   - Verify successful connection to Telegram
   - Verify access to the BINARY TRADING CLUB channel

2. Test Pocket Option connection:
   ```
   python test_ssid_direct.py
   ```
   - Enter your SSID
   - Choose 'n' for demo account
   - Verify successful connection

## Step 4: Start the Bot (21:45 SAST)

1. Start the bot:
   ```
   python self_bot.py --verbose
   ```

2. Verify successful startup:
   - Check for successful connection to Telegram
   - Check for successful connection to Pocket Option
   - Verify the bot is monitoring the correct channel

## Step 5: Monitor the Trading Session (22:00 SAST)

1. Keep the terminal open to monitor for signals and trades
2. The bot will log all messages from the channel
3. When a valid signal is detected, it will execute a trade
4. Trade results will be logged in the terminal and database

## Emergency Procedures

If you need to stop the bot for any reason:

1. Press Ctrl+C in the terminal to stop the bot
2. Or use the restart utility:
   ```
   python restart_bot.py
   ```
   - Choose 'y' when asked if you want to stop the bot

## Post-Session Analysis

After the trading session:

1. Check the database for results:
   ```
   python query_database.py
   ```

2. Review the logs for any issues:
   ```
   cat self_bot.log
   ```

3. Update the configuration if needed for the next session:
   ```
   python restart_bot.py
   ```

## Tools Created for Tonight's Session

1. **refresh_ssid.py**: Utility to refresh the SSID in the configuration file
2. **restart_bot.py**: Utility to stop and restart the bot with updated configuration
3. **docs/Real_Trading_Execution_Guide.md**: Comprehensive guide for real trading execution

Good luck with tonight's trading session!
