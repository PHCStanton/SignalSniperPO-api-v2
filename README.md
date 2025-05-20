# Self Bot v1.0 for Pocket Option Trading

A Telegram-based bot that monitors the BINARY TRADING CLUB channel for trading signals and executes trades on Pocket Option using websocket SSID authentication.

## Features

- **Signal Monitoring**: Monitors the BINARY TRADING CLUB Telegram channel for trading signals
- **Signal Parsing**: Parses the two-message format signals (Trading Pair + Timer/Direction/Expiry)
- **Trade Execution**: Executes trades on Pocket Option at the specified time
- **Database Logging**: Logs all signals and trades to a SQLite database
- **Test Mode**: Simulates trades without risking real money
- **Error Handling**: Comprehensive error handling and logging
- **Deployment Scripts**: Easy deployment to EC2 instance

## Requirements

- Python 3.7+
- Telegram API credentials (api_id and api_hash)
- Pocket Option account with SSID
- SQLite3

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/pocket-option-selfbot.git
   cd pocket-option-selfbot
   ```

2. Install dependencies:
   ```bash
   python install_dependencies.py
   ```

3. Configure the bot:
   - Create/edit `config/bot_config.json`
   - Create/edit `config/telegram_config.json`
   - Create/edit `config/pocket_option_config.json`

4. Obtain a fresh SSID from Pocket Option:
   - Follow the instructions in `extract_po_trade_ssid.md`
   - Update `config/pocket_option_config.json` with the fresh SSID

## Configuration Files

### bot_config.json
```json
{
    "timezone": "Africa/Johannesburg",
    "trade_amount": 10,
    "max_daily_trades": 20,
    "max_daily_loss": 100,
    "min_seconds_before_timer": 5,
    "stats_interval": 1800,
    "test_mode": true,
    "test_mode_win_rate": 0.6
}
```

### telegram_config.json
```json
{
    "api_id": 12345678,
    "api_hash": "your_api_hash_here",
    "session_name": "pocket_option_userbot",
    "channel_name": "BINARY TRADING CLUB",
    "channel_id": -1002412213735,
    "log_all_messages": true,
    "pair_match_window": 60,
    "first_message_regex": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
    "second_message_regex": {
        "timer": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
        "pair": "Currency pair (\\w+/\\w+)",
        "direction": "(HIGHER|LOWER)",
        "expiry": "Trade time: (\\d+) MIN"
    }
}
```

### pocket_option_config.json
```json
{
    "ssid": "your_ssid_here",
    "is_demo": true,
    "min_payout": 80,
    "preferred_assets": [
        "EURUSD",
        "GBPUSD",
        "USDJPY"
    ],
    "otc_preferred": true
}
```

## Usage

### Running the Bot

```bash
python self_bot.py
```

### Command-line Options

```bash
python self_bot.py --help
```

Available options:
- `--config`: Path to bot configuration file
- `--telegram-config`: Path to Telegram configuration file
- `--pocket-option-config`: Path to Pocket Option configuration file
- `--db`: Path to SQLite database file
- `--verbose`: Enable verbose output
- `--test-mode`: Run in test mode (simulated trades)

### Testing Signal Monitoring

```bash
python monitor_signals.py --duration 300 --verbose
```

### Testing Telegram Session

```bash
python check_telegram_session.py --verbose
```

### Simulating Test Signals

```bash
python simulate_test_signals.py --local-test --count 3 --interval 5
```

## Deployment to EC2

### Using Bash Script (Linux/macOS)

```bash
chmod +x deploy_selfbot.sh
./deploy_selfbot.sh
```

### Using PowerShell Script (Windows)

```powershell
.\deploy_selfbot.ps1
```

## Directory Structure

```
pocket-option-selfbot/
├── config/
│   ├── bot_config.json
│   ├── telegram_config.json
│   └── pocket_option_config.json
├── data/
│   └── trades.db
├── docs/
│   ├── Dev_Plan_Start.md
│   └── ...
├── PocketOptionAPI-v2/
│   └── ...
├── utils/
│   └── ...
├── self_bot.py
├── install_dependencies.py
├── deploy_selfbot.sh
├── deploy_selfbot.ps1
└── requirements.txt
```

## Troubleshooting

### SSID Issues

If you encounter issues with the SSID:
1. Obtain a fresh SSID from Pocket Option
2. Test the SSID using `test_ssid_direct.py`
3. Update `config/pocket_option_config.json`

### Telegram Authentication Issues

If you encounter issues with Telegram authentication:
1. Verify your API credentials
2. Check if the session file exists
3. Try running `check_telegram_session.py`

### Database Issues

If you encounter issues with the database:
1. Check if the database file exists
2. Verify the permissions
3. Try running `sqlite3 data/trades.db .tables` to check if the tables exist

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgements

- [Telethon](https://github.com/LonamiWebs/Telethon) for the Telegram client
- [PocketOptionAPI-v2](https://github.com/Mastaaa1987/PocketOptionAPI-v2) for the Pocket Option API
