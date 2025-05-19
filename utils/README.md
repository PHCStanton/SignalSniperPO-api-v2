# Pocket Option Trading Bot Utilities

This directory contains utility scripts for setting up, testing, and deploying the Pocket Option trading bot. These scripts are designed to help with various aspects of the bot's development and operation.

## Overview

The utilities in this directory are organized by their purpose:

1. **Setup and Testing**
   - `test_latency.py`: Tests latency to Pocket Option servers from different regions
   - `telegram_setup.py`: Sets up Telegram integration for monitoring the trading channel
   - `test_pocket_option_api.py`: Tests connection and authentication with Pocket Option API
   - `send_test_message.py`: Sends a test message to a Telegram channel to verify connectivity

2. **Deployment**
   - `deploy.sh`: Deploys the trading bot to an EC2 instance (Linux/macOS)
   - `deploy_to_ec2.ps1`: Deploys the trading bot to an EC2 instance (Windows)
   - `deploy_config.json`: Configuration file for deployment scripts

3. **Monitoring and Simulation**
   - `check_latency.py`: Continuously monitors latency to Pocket Option servers
   - `simulate_signals.py`: Simulates trading signals for testing the bot

## Setup and Testing Utilities

### test_latency.py

Tests latency to Pocket Option servers from different regions to identify the optimal region for deployment.

**Usage:**
```bash
python test_latency.py [-n NUM_TESTS] [-v]
```

**Options:**
- `-n, --num-tests`: Number of tests to run per region (default: 10)
- `-v, --verbose`: Enable verbose output

**Example:**
```bash
python test_latency.py -n 20 -v
```

### telegram_setup.py

Sets up Telegram integration for monitoring the "BINARY TRADING CLUB" channel for trading signals.

**Usage:**
```bash
python telegram_setup.py --api-id API_ID --api-hash API_HASH [--bot-token BOT_TOKEN] [--channel CHANNEL] [--monitor] [--duration DURATION] [--verbose]
```

**Options:**
- `--api-id`: Telegram API ID
- `--api-hash`: Telegram API hash
- `--bot-token`: Telegram bot token (if using a bot)
- `--session`: Session name (default: pocket_option_bot)
- `--config`: Configuration file path (default: telegram_config.json)
- `--channel`: Channel name or username to join
- `--monitor`: Run signal monitor
- `--duration`: Duration to run monitor in seconds (default: 300)
- `--verbose`: Enable verbose output

**Example:**
```bash
python telegram_setup.py --api-id 123456 --api-hash abcdef1234567890 --channel "BINARY TRADING CLUB" --monitor --duration 600
```

### test_pocket_option_api.py

Tests connection and authentication with Pocket Option API, retrieves basic account information, and tests basic trading functionality.

**Usage:**
```bash
python test_pocket_option_api.py --email EMAIL --password PASSWORD [--config CONFIG] [--verbose] [--test-trade]
```

**Options:**
- `--email`: Pocket Option account email
- `--password`: Pocket Option account password
- `--config`: Configuration file path (default: pocket_option_config.json)
- `--verbose`: Enable verbose output
- `--test-trade`: Test trading functionality

**Example:**
```bash
python test_pocket_option_api.py --email user@example.com --password mypassword --verbose
```

### send_test_message.py

Sends a test message to a Telegram channel or chat to verify connectivity.

**Usage:**
```bash
python send_test_message.py --api-id API_ID --api-hash API_HASH [--bot-token BOT_TOKEN] [--channel CHANNEL] [--message MESSAGE] [--no-delete] [--delete-delay DELAY] [--verbose]
```

**Options:**
- `--api-id`: Telegram API ID
- `--api-hash`: Telegram API hash
- `--bot-token`: Telegram bot token (if using a bot)
- `--session`: Session name (default: telegram_test)
- `--config`: Configuration file path
- `--channel`: Channel name, username, or ID
- `--message`: Message to send
- `--no-delete`: Do not delete the message after sending
- `--delete-delay`: Delay in seconds before deleting the message (default: 5)
- `--verbose`: Enable verbose output

**Example:**
```bash
python send_test_message.py --api-id 123456 --api-hash abcdef1234567890 --channel "BINARY TRADING CLUB" --message "Test message"
```

## Deployment Utilities

### deploy.sh

Deploys the Pocket Option trading bot to an EC2 instance from Linux or macOS.

**Usage:**
```bash
./deploy.sh [options]
```

**Options:**
- `-h, --host`: EC2 instance hostname or IP address
- `-u, --user`: SSH username (default: ec2-user)
- `-k, --key`: Path to SSH private key
- `-p, --path`: Remote deployment path (default: /home/ec2-user/pocket-option-bot)
- `-c, --config`: Path to configuration file (default: deploy_config.json)
- `-s, --setup-only`: Only set up the environment, don't deploy the bot
- `-r, --restart`: Restart the bot service if it's already running
- `-v, --verbose`: Enable verbose output
- `--help`: Display help message and exit

**Example:**
```bash
./deploy.sh -h ec2-example.eu-west-1.compute.amazonaws.com -k ~/.ssh/pocket-option-bot.pem -v
```

### deploy_to_ec2.ps1

Deploys the Pocket Option trading bot to an EC2 instance from Windows.

**Usage:**
```powershell
.\deploy_to_ec2.ps1 [options]
```

**Parameters:**
- `-Host`: EC2 instance hostname or IP address
- `-User`: SSH username (default: ec2-user)
- `-KeyFile`: Path to SSH private key (.pem file)
- `-RemotePath`: Remote deployment path (default: /home/ec2-user/pocket-option-bot)
- `-ConfigFile`: Path to configuration file (default: deploy_config.json)
- `-SetupOnly`: Only set up the environment, don't deploy the bot
- `-Restart`: Restart the bot service if it's already running
- `-Verbose`: Enable verbose output

**Example:**
```powershell
.\deploy_to_ec2.ps1 -Host ec2-example.eu-west-1.compute.amazonaws.com -KeyFile C:\Keys\pocket-option-bot.pem -Verbose
```

### deploy_config.json

Configuration file for deployment scripts. Contains settings for EC2 instance, Telegram API, Pocket Option API, and bot configuration.

**Example:**
```json
{
  "host": "ec2-example.eu-west-1.compute.amazonaws.com",
  "user": "ec2-user",
  "key": "~/.ssh/pocket-option-bot.pem",
  "remote_path": "/home/ec2-user/pocket-option-bot",
  
  "telegram_api_id": "123456",
  "telegram_api_hash": "abcdef1234567890",
  "telegram_bot_token": "",
  
  "pocket_option_email": "user@example.com",
  "pocket_option_password": "mypassword",
  
  "deployment": {
    "region": "eu-west-1",
    "instance_type": "t3.micro",
    "ami_id": "ami-0c55b159cbfafe1f0",
    "security_group": "pocket-option-bot-sg",
    "key_name": "pocket-option-bot"
  },
  
  "bot_config": {
    "trade_amount": 1,
    "max_daily_trades": 20,
    "max_daily_loss": 50,
    "test_mode": true,
    "log_level": "INFO",
    "timezone": "Africa/Johannesburg"
  }
}
```

## Monitoring and Simulation Utilities

### check_latency.py

Continuously monitors latency to Pocket Option servers and reports any issues.

**Usage:**
```bash
python check_latency.py [-i INTERVAL] [-d DURATION] [-w WARNING] [-c CRITICAL] [-t TIMEOUT] [-r REPORT] [-o OUTPUT] [-v]
```

**Options:**
- `-i, --interval`: Interval between latency checks in seconds (default: 60)
- `-d, --duration`: Duration to monitor in seconds (default: indefinite)
- `-w, --warning`: Warning threshold in milliseconds (default: 200)
- `-c, --critical`: Critical threshold in milliseconds (default: 500)
- `-t, --timeout`: Timeout threshold in milliseconds (default: 5000)
- `-r, --report`: Interval between summary reports in seconds (default: 3600)
- `-o, --output`: File to write latency data to
- `-v, --verbose`: Enable verbose output

**Example:**
```bash
python check_latency.py -i 30 -w 150 -c 400 -r 1800 -o latency_data.json -v
```

### simulate_signals.py

Simulates trading signals in the two-message format used by Simon in the "BINARY TRADING CLUB" channel.

**Usage:**
```bash
python simulate_signals.py [-a ASSETS] [--otc OTC_ASSETS] [-e EXPIRY] [-c COUNT] [-d DELAY] [-m MESSAGE_DELAY] [-o OUTPUT] [-v]
```

**Options:**
- `-a, --assets`: Assets to use for simulated signals
- `--otc`: Assets that can be marked as OTC
- `-e, --expiry`: Expiry times in minutes
- `-c, --count`: Number of signals to generate (default: 5)
- `-d, --delay`: Delay between signals in seconds (default: 60)
- `-m, --message-delay`: Delay between first and second message in seconds (default: 5)
- `-o, --output`: File to write signals to
- `-v, --verbose`: Enable verbose output

**Example:**
```bash
python simulate_signals.py -a EUR/USD GBP/USD -e 1 2 5 -c 10 -d 30 -o simulated_signals.json -v
```

## Environment Variables

Some scripts support loading configuration from environment variables:

- `TELEGRAM_API_ID`: Telegram API ID
- `TELEGRAM_API_HASH`: Telegram API hash
- `TELEGRAM_BOT_TOKEN`: Telegram bot token
- `POCKET_OPTION_EMAIL`: Pocket Option account email
- `POCKET_OPTION_PASSWORD`: Pocket Option account password

## Dependencies

These utilities require the following Python packages:

- `telethon`: For Telegram integration
- `websockets`: For WebSocket connections to Pocket Option API
- `asyncio`: For asynchronous programming
- `aiohttp`: For HTTP requests
- `python-dotenv`: For loading environment variables
- `pytz`: For timezone handling

You can install these dependencies using pip:

```bash
pip install telethon websockets asyncio aiohttp python-dotenv pytz
```

## Getting Started

1. Set up your development environment:
   ```bash
   python test_latency.py -v
   ```

2. Set up Telegram integration:
   ```bash
   python telegram_setup.py --api-id YOUR_API_ID --api-hash YOUR_API_HASH --channel "BINARY TRADING CLUB"
   ```

3. Test Pocket Option API connection:
   ```bash
   python test_pocket_option_api.py --email YOUR_EMAIL --password YOUR_PASSWORD
   ```

4. Simulate trading signals for testing:
   ```bash
   python simulate_signals.py -c 5 -d 30
   ```

5. Deploy the bot to an EC2 instance:
   ```bash
   # Linux/macOS
   ./deploy.sh -h YOUR_EC2_HOST -k YOUR_KEY_PATH
   
   # Windows
   .\deploy_to_ec2.ps1 -Host YOUR_EC2_HOST -KeyFile YOUR_KEY_PATH
   ```

6. Monitor latency to Pocket Option servers:
   ```bash
   python check_latency.py -i 30 -o latency_data.json
   ```

7. Verify Telegram channel connectivity:
   ```bash
   python send_test_message.py --api-id YOUR_API_ID --api-hash YOUR_API_HASH --channel "BINARY TRADING CLUB"
