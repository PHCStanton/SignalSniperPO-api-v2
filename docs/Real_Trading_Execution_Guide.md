# Real Trading Execution Guide

This guide provides step-by-step instructions for executing the SelfBot v1.0 for real trading with the BINARY TRADING CLUB Telegram channel.

## Pre-Execution Checklist

1. **Verify SSID Validity**
   - SSIDs typically expire after ~24 hours
   - Run `test_ssid_direct.py` to verify the SSID is still valid
   - If expired, obtain a fresh SSID and update `config/pocket_option_config.json`

2. **Verify Telegram Session**
   - Run `check_telegram_session.py` to verify the Telegram session is still valid
   - Ensure the bot can access the BINARY TRADING CLUB channel

3. **Verify Configuration**
   - Ensure `config/bot_config.json` has `"test_mode": false`
   - Verify `"trade_amount"` is set to the desired amount (currently $1)
   - Check risk management parameters are appropriate

## Execution Steps

1. **Start the Bot**
   ```
   python self_bot.py --verbose
   ```

2. **Verify Successful Startup**
   - Check that the bot connects to Telegram successfully
   - Check that the bot connects to Pocket Option API successfully
   - Verify the account balance is displayed
   - Confirm the bot is monitoring the correct channel

3. **Monitor Operation**
   - Keep the terminal open to monitor for signals and trades
   - The bot will log all messages from the channel
   - When a valid signal is detected, it will execute a trade
   - Trade results will be logged in the terminal and database

## Post-Execution Verification

1. **Check Database**
   ```
   python query_database.py
   ```
   - Verify signals were detected and recorded
   - Verify trades were executed and results recorded

2. **Check Statistics**
   - The bot displays statistics every 30 minutes
   - Check win rate, total profit, and other metrics

## Emergency Procedures

1. **Stop the Bot**
   - Press Ctrl+C in the terminal to stop the bot
   - Or close the terminal window

2. **Reset Configuration**
   - To switch back to test mode, edit `config/bot_config.json` and set `"test_mode": true`

## Notes for 22:00 SAST Execution

1. **Start the Bot at 21:45 SAST**
   - This gives you time to verify everything is working before the trading session
   - The BINARY TRADING CLUB often starts sessions around 22:00

2. **Refresh SSID if Needed**
   - If you've been running tests during the day, the SSID might expire
   - Get a fresh SSID before starting the bot

3. **Monitor Initial Signals**
   - Pay close attention to the first few signals and trades
   - Verify they are executed correctly with the $1 amount

4. **Keep Backup Funds**
   - Ensure you have sufficient funds in your Pocket Option account
   - The bot is configured to stop if it reaches the maximum daily loss
