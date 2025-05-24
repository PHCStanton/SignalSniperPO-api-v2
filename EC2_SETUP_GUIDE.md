# EC2 Setup Guide for Self Bot v1.0

This guide provides step-by-step instructions for setting up and running the Self Bot v1.0 on your EC2 instance. The included setup script automates most of the process, but this guide provides additional context and troubleshooting tips.

## Prerequisites

- An EC2 instance running Ubuntu (preferably Ubuntu 20.04 or newer)
- SSH access to the EC2 instance
- The Self Bot v1.0 code deployed to the instance (already done with `deploy_selfbot.ps1`)
- A valid SSID from Pocket Option (see [Obtaining a Valid SSID](#obtaining-a-valid-ssid))
- A Telegram account that is a member of the BINARY TRADING CLUB channel

## Quick Setup

1. **Make the setup script executable**:
   ```bash
   chmod +x setup_ec2_bot_v1.sh
   ```

2. **Run the setup script**:
   ```bash
   ./setup_ec2_bot_v1.sh
   ```

3. **Follow the on-screen instructions** to complete the setup.

## What the Setup Script Does

The `setup_ec2_bot_v1.sh` script automates the following tasks:

1. Installs system dependencies (Python, pip, venv, sqlite3)
2. Creates and configures a Python virtual environment
3. Installs Python dependencies from requirements.txt
4. Checks for and creates configuration files if needed
5. Creates and installs a systemd service for automatic startup
6. Verifies the SQLite installation
7. Provides next steps for testing and running the bot

## Manual Setup (If the Script Fails)

If the setup script fails, you can perform the steps manually:

### 1. Install System Dependencies

```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-venv sqlite3 libsqlite3-dev
```

### 2. Set Up Python Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Python Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Check Configuration Files

Ensure these files exist and are properly configured:
- `config/telegram_config.json`
- `config/pocket_option_config.json`
- `.env`

### 5. Create and Install Systemd Service

```bash
sudo nano /etc/systemd/system/selfbot.service
```

Add the following content:
```ini
[Unit]
Description=Self Bot Trading Service
After=network.target

[Service]
User=ubuntu
Group=ubuntu
WorkingDirectory=/home/ubuntu/self_bot_v1
ExecStart=/home/ubuntu/self_bot_v1/venv/bin/python /home/ubuntu/self_bot_v1/bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/self_bot_v1/.env

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable selfbot.service
```

## Testing the Bot

Before starting the service, it's recommended to test each component:

### 1. Test Telegram Authentication

```bash
source venv/bin/activate
python check_telegram_session.py --verbose
```

If successful, you should see:
```
✅ Session pocket_option_userbot is valid
Logged in as: Your Name (@your_username)
✅ Can access channel: BINARY TRADING CLUB
```

### 2. Test Pocket Option SSID

```bash
source venv/bin/activate
python test_ssid_direct.py
```

If successful, you should see:
```
✅ Connected to Pocket Option API
✅ SSID is valid
Balance: 1000.00 USD
```

### 3. Test Signal Monitoring

```bash
source venv/bin/activate
python monitor_signals.py --duration 300 --verbose
```

This will monitor the channel for 5 minutes and log any detected signals.

## Running the Bot

Once testing is complete, you can start the bot service:

```bash
sudo systemctl start selfbot.service
```

Check the status:
```bash
sudo systemctl status selfbot.service
```

View the logs:
```bash
sudo journalctl -u selfbot.service -f
```

## Obtaining a Valid SSID

The Self Bot requires a valid SSID from Pocket Option's WebSocket API for authentication:

1. Log in to Pocket Option (real or demo) at `https://po.trade`
2. Open DevTools (F12) > Network > WS, filter for WebSocket connections
3. Locate the `42["auth",...]` message containing the session string
4. Copy the full `session` string as the SSID
5. Update `config/pocket_option_config.json` with the SSID

Note: SSIDs typically expire after ~24 hours, so you may need to update it regularly.

## Troubleshooting

### SQLite3 Installation Issues

If you encounter issues with SQLite3:

```bash
# Install SQLite3 system package
sudo apt-get install -y sqlite3 libsqlite3-dev

# Verify SQLite3 is working in Python
python -c "import sqlite3; print(sqlite3.sqlite_version)"
```

### Telegram Authentication Issues

If you encounter phone verification issues:

- Ensure the API ID and hash are correct in `.env` and `config/telegram_config.json`
- Try using a different network or wait 24 hours for rate limits to reset
- Check if the session file (`pocket_option_userbot.session`) is present and valid

### Pocket Option API Issues

If the SSID is invalid:

- Obtain a fresh SSID following the steps in [Obtaining a Valid SSID](#obtaining-a-valid-ssid)
- Verify WebSocket connection using `test_ssid_direct.py` or `test_po_websocket.py`
- Check if your IP (EC2 instance) is blocked by Pocket Option

### Service Issues

If the systemd service fails to start:

- Check logs: `sudo journalctl -u selfbot.service -f`
- Verify permissions on files and directories
- Ensure the virtual environment is correctly specified in the service file

## Notes

- **WebSocket SSID Only**: Pocket Option's authentication relies on WebSocket messages, not HTTP cookies
- **Demo Mode**: Use `is_demo=true` in config for testing to avoid financial risk
- **EC2 IP**: Ensure the SSID's `ip_address` matches the EC2 instance or update dynamically
- **Log Files**: Check `bot.log` and `telethon_setup.log` for debugging information
