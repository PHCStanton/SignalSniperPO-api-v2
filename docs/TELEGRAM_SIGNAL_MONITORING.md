# Telegram Signal Monitoring Test Suite

This set of scripts allows you to test the Telegram signal monitoring functionality for the Pocket Option trading bot. The focus is on verifying that the bot can correctly detect and parse trading signals from the BINARY TRADING CLUB channel without executing any trades on the Pocket Option platform.

## Overview

The test suite consists of the following scripts:

1. `check_telegram_session.py` - Checks if you have a valid Telegram session and can access the BINARY TRADING CLUB channel
2. `monitor_signals.py` - Monitors the BINARY TRADING CLUB channel for trading signals without executing trades
3. `simulate_test_signals.py` - Simulates trading signals for testing purposes

## Prerequisites

- Python 3.7 or higher
- Telethon library (`pip install telethon`)
- pytz library (`pip install pytz`)
- python-dotenv library (`pip install python-dotenv`)
- A Telegram account that is a member of the BINARY TRADING CLUB channel
- Telegram API credentials (API ID and API hash)

## Setup

1. Ensure your Telegram API credentials are properly configured in `config/telegram_config.json`:

```json
{
  "api_id": 28529262,
  "api_hash": "6e3dde953198895cddbd7396631a1da5",
  "session_name": "pocket_option_userbot",
  "channel_name": "BINARY TRADING CLUB",
  "channel_id": -1002412213735,
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

2. Alternatively, you can set the API credentials in a `.env` file:

```
TELEGRAM_API_ID=28529262
TELEGRAM_API_HASH=6e3dde953198895cddbd7396631a1da5
```

3. Make sure you have a valid Telegram session file. If not, you can create one using the `test_telegram_api.py` script:

```bash
python test_telegram_api.py
```

## Running the Test Suite

### Option 1: Using the Convenience Scripts

#### On Windows:

Run the PowerShell script:

```powershell
.\Run-TelegramMonitor.ps1 -Verbose
```

To run for a specific duration (e.g., 30 minutes):

```powershell
.\Run-TelegramMonitor.ps1 -Duration 1800 -Verbose
```

#### On Linux/macOS:

First, make the script executable:

```bash
chmod +x run_telegram_monitor.sh
```

Then run it:

```bash
./run_telegram_monitor.sh --verbose
```

To run for a specific duration (e.g., 30 minutes):

```bash
./run_telegram_monitor.sh --duration 1800 --verbose
```

### Option 2: Running Scripts Individually

#### Step 1: Check Telegram Session

First, check if you have a valid Telegram session and can access the BINARY TRADING CLUB channel:

```bash
python check_telegram_session.py
```

If successful, you should see:

```
✅ Session pocket_option_userbot is valid
Logged in as: Your Name (@your_username)

✅ Can access channel: BINARY TRADING CLUB

Ready to monitor signals!
```

If not, follow the instructions provided by the script to create a new session or fix the channel access issue.

## Step 2: Monitor Signals

Once you have a valid session and can access the channel, you can start monitoring for signals:

```bash
python monitor_signals.py --verbose
```

This will connect to the BINARY TRADING CLUB channel and monitor for trading signals. The script will parse the signals in the two-message format:

1. First message: `Trading Pair: EUR/USD`
2. Second message: 
```
SET THE TIMER TO 14:30:00
Currency pair EUR/USD
HIGHER
Trade time: 1 MIN
```

The script will log all detected signals and print statistics periodically.

To run the monitor for a specific duration (e.g., 30 minutes):

```bash
python monitor_signals.py --duration 1800
```

## Step 3: Simulate Signals (Optional)

If you want to test the signal parsing functionality without waiting for actual signals from the BINARY TRADING CLUB channel, you can simulate signals:

### Option 1: Send simulated signals to a test channel

Create a test channel in Telegram and get its channel ID. Then run:

```bash
python simulate_test_signals.py --channel-id YOUR_TEST_CHANNEL_ID --count 3 --interval 30
```

This will send 3 simulated signals to your test channel with a 30-second interval between them.

### Option 2: Simulate signals locally

```bash
python simulate_test_signals.py --local-test --count 3 --interval 5
```

This will simulate 3 signals locally without sending them to Telegram, with a 5-second interval between them.

## Troubleshooting

### Session Issues

If you're having issues with your Telegram session, try:

1. Checking all available sessions:

```bash
python test_sessions.py
```

2. Creating a new session:

```bash
python test_telegram_api.py --session new_session_name
```

3. Using a different session:

```bash
python monitor_signals.py --telegram-config config/telegram_config.json --session another_session
```

### Channel Access Issues

If you can't access the BINARY TRADING CLUB channel:

1. Make sure your Telegram account is a member of the channel
2. Check if the channel ID in `telegram_config.json` is correct
3. Try accessing the channel by name instead of ID

### Signal Parsing Issues

If signals are not being detected correctly:

1. Check the regex patterns in `telegram_config.json`
2. Enable verbose logging to see all messages: `python monitor_signals.py --verbose`
3. Test with simulated signals to verify the parsing logic

## Important Notes

- This test suite only monitors signals and does not execute any trades on the Pocket Option platform
- The session file contains your Telegram authentication credentials, so keep it secure
- The BINARY TRADING CLUB channel broadcasts signals at specific times, so make sure to run the monitor during those times
- The monitor script will continue running until you stop it with Ctrl+C, or until the specified duration is reached

## Next Steps

Once you've verified that the signal monitoring functionality works correctly, you can proceed to integrate it with the Pocket Option trading functionality in the main bot.
