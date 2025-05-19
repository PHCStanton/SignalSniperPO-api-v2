# EC2 Instance Setup for Self Bot v1.0

This document provides instructions for setting up the Self Bot v1.0 on an Amazon EC2 instance. The bot monitors Telegram signals from BINARY TRADING CLUB (channel_id: -1002412213735) using a Telethon-based user account approach and executes trades on Pocket Option via WebSocket SSID authentication.

## Part 1: SSH Key Configuration

📝 **Note on SSH Key:**
- **Permissions (Client-Side):** Before connecting, ensure your `.pem` key file has the correct permissions.
  - **Linux or macOS:**
    ```bash
    chmod 400 /path/to/your-key.pem
    ```
  - **Windows (using PowerShell):**
    SSH on Windows is very particular about private key permissions. The key file must not be accessible by other users or groups. You may need to run PowerShell as an **Administrator** for these commands to fully succeed.
    Replace `your-key.pem` with the actual path to your key file (e.g., `EC2/whoami-in-Frankfurt.pem`).
    ```powershell
    # 1. Reset permissions to a clean state
    icacls.exe your-key.pem /reset /T /C /Q

    # 2. Remove inheritance
    icacls.exe your-key.pem /inheritance:r /T /C /Q

    # 3. Grant your current user Full Control
    icacls.exe your-key.pem /grant:r "$($env:USERNAME):(F)" /T /C /Q

    # 4. Remove common problematic groups
    icacls.exe your-key.pem /remove "Authenticated Users" "BUILTIN\Users" "Everyone" /T /C /Q
    ```
    After running these commands, try your SSH connection again.

## Part 2: SSH into EC2 Instance

✅ Command:
```bash
ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
```

## Part 3: AWS Security Group Configuration

⚠️ **Important:** Besides UFW (host firewall), your EC2 instance is protected by AWS Security Groups (network firewall). Ensure your Security Group allows inbound traffic for:
- **SSH (TCP port 22):** From your IP address for secure access.
- **Outbound traffic:** Allow all outbound traffic for the bot to connect to Telegram and Pocket Option API.

## Part 4: Server Preparation

✅ Update & Install essentials:
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y python3 python3-pip git ufw python3-venv
```

💡 **Python Virtual Environment Setup**
```bash
# Create project directory
mkdir -p ~/selfbot
cd ~/selfbot

# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# All pip install commands should be run with venv activated
```

## Part 5: Self Bot Installation

*Ensure your virtual environment (`venv`) is activated*

✅ Install Python libraries:
```bash
pip install telethon websockets asyncio aiohttp python-dotenv pytz
```

✅ Clone the repository (if available) or transfer files:
```bash
# Option 1: Clone from repository
git clone [your-repository-url] .

# Option 2: Transfer files using SCP (from your local machine)
# Run this command on your local machine, not on the EC2 instance
scp -i EC2/whoami-in-Frankfurt.pem -r ./pocketoptionapi ./bot.py ./config ubuntu@3.126.128.227:~/selfbot/
```

## Part 6: Configuration

✅ Create/Update environment file:
```bash
nano .env
```

Add the following content:
```
TELEGRAM_API_ID=28529262
TELEGRAM_API_HASH=6e3dde953198895cddbd7396631a1da5
```

✅ Update Telegram configuration:
```bash
mkdir -p config
nano config/telegram_config.json
```

Add the following content:
```json
{
  "channel_name": "BINARY TRADING CLUB",
  "channel_id": -1002412213735,
  "signal_parser": {
    "first_message_pattern": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
    "second_message_timer_pattern": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
    "second_message_pair_pattern": "Currency pair (\\w+/\\w+)",
    "second_message_direction_pattern": "(HIGHER|LOWER)",
    "second_message_expiry_pattern": "Trade time: (\\d+) MIN",
    "max_time_between_messages": 60
  },
  "monitoring": {
    "enabled": true,
    "log_all_messages": false
  }
}
```

✅ Configure Pocket Option API:
```bash
nano config/pocket_option_config.json
```

Add the following content (replace SSID with a valid one):
```json
{
  "ssid": "YOUR_ACTUAL_SSID_HERE",
  "is_demo": true,
  "api": {
    "websocket_url": "wss://po.trade/socket.io/?EIO=3&transport=websocket",
    "connection_timeout": 30,
    "ping_interval": 30
  },
  "trading": {
    "default_asset": "EUR/USD",
    "default_amount": 1,
    "default_expiry": 60,
    "test_mode": true
  }
}
```

## Part 7: Obtaining a Valid SSID for Pocket Option

The Self Bot requires a valid SSID from Pocket Option's WebSocket API for authentication. Follow these steps to obtain it:

1. Log in to Pocket Option (real or demo) at `https://po.trade`.
2. Open DevTools (F12) > Network > WS, filter for WebSocket connections.
3. Locate the `42["auth",...]` message containing the session string.
4. Copy the full `session` string as the SSID.
5. Update `pocket_option_config.json` with the SSID.

Note: SSIDs typically expire after ~24 hours. For v1.0, manual updates are acceptable.

## Part 8: Setting Up Telegram Session

The bot uses Telethon with a user account to monitor the BINARY TRADING CLUB channel:

1. **Authenticate with Telegram:**
   ```bash
   python utils/telethon_setup.py --env
   ```
   If prompted, enter your phone number and verification code.

2. **Test Channel Access:**
   ```bash
   python utils/telethon_setup.py --env --channel "BINARY TRADING CLUB"
   ```

3. **Test Signal Monitoring:**
   ```bash
   python monitor_signals.py --duration 300 --verbose
   ```

## Part 9: Making the Bot Persistent with `systemd`

✅ Create a systemd service file:
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
WorkingDirectory=/home/ubuntu/selfbot
ExecStart=/home/ubuntu/selfbot/venv/bin/python /home/ubuntu/selfbot/bot.py
Restart=always
RestartSec=10
EnvironmentFile=/home/ubuntu/selfbot/.env

[Install]
WantedBy=multi-user.target
```

✅ Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable selfbot.service
sudo systemctl start selfbot.service
```

✅ Check service status:
```bash
sudo systemctl status selfbot.service
```

✅ View logs:
```bash
sudo journalctl -u selfbot.service -f
```

## Part 10: UFW Firewall Configuration

✅ Configure UFW:
```bash
sudo ufw allow 22/tcp    # SSH (restrict to your IP in Security Group)
sudo ufw enable          # Enable the firewall (will prompt for confirmation)
```

✅ Check UFW Status:
```bash
sudo ufw status verbose
```

## Part 11: Testing the Complete Setup

1. **Verify Telegram Authentication:**
   ```bash
   python check_telegram_session.py --verbose
   ```

2. **Test SSID Validity:**
   ```bash
   python test_ssid_direct.py
   ```

3. **Monitor for Signals:**
   ```bash
   python monitor_signals.py --duration 300 --verbose
   ```

4. **Test a Demo Trade:**
   After confirming your SSID is valid, run:
   ```bash
   python bot.py --test-trade
   ```

5. **Check the Bot Service:**
   ```bash
   sudo systemctl status selfbot.service
   ```

## Troubleshooting

### Telegram Authentication Issues
- If you encounter phone verification issues, ensure the API ID and hash are correct.
- Try using a different network or wait 24 hours for rate limits to reset.
- Check if the session file (`pocket_option_userbot.session`) is present and valid.

### Pocket Option API Issues
- If the SSID is invalid, obtain a fresh one following the steps in Part 7.
- Verify WebSocket connection using `test_ssid_direct.py` or `test_po_websocket.py`.
- Check if your IP (EC2 instance) is blocked by Pocket Option.

### Service Issues
- Check logs: `sudo journalctl -u selfbot.service -f`
- Verify permissions on files and directories.
- Ensure the virtual environment is correctly specified in the service file.

## Notes
- **WebSocket SSID Only**: Pocket Option's authentication relies on WebSocket messages, not HTTP cookies.
- **Demo Mode**: Use `is_demo=true` in config for testing to avoid financial risk.
- **EC2 IP**: Ensure the SSID's `ip_address` matches the EC2 instance (3.126.128.227) or update dynamically.
- **Log Files**: Check `bot.log` and `telethon_setup.log` for debugging information.
