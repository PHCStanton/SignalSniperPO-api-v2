# EC2 Deployment for Self Bot v1.0

This README provides an overview of the EC2 deployment process for the Self Bot v1.0, which monitors the BINARY TRADING CLUB Telegram channel for trading signals and executes trades on Pocket Option.

## Quick Links

- [Setup Guide](EC2_SETUP_GUIDE.md) - Detailed setup instructions
- [EC2 Instance Activation](docs/EC2-Instance-to-bot-activate.md) - Original activation guide
- [SSH Connection Guide](docs/EC2_SSH_Connection_Guide.md) - Troubleshooting SSH connections
- [Dev Plan](docs/Dev_Plan_Start.md) - Development plan and roadmap

## Scripts and Tools

| Script | Description |
|--------|-------------|
| `setup_ec2_bot_v1.sh` | Main setup script for EC2 instance |
| `update_ssid.sh` | Script to update the Pocket Option SSID |
| `fix_ssh_key_permissions.ps1` | PowerShell script to fix SSH key permissions |
| `check_ec2_directory.ps1` | PowerShell script to check EC2 directory |
| `deploy_selfbot.ps1` | PowerShell script to deploy the bot to EC2 |
| `deploy_selfbot.sh` | Bash script to deploy the bot to EC2 |

## Setup Process

1. **Fix SSH Key Permissions** (on your local machine):
   ```powershell
   .\fix_ssh_key_permissions.ps1
   ```

2. **Connect to EC2 Instance**:
   ```bash
   ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
   ```

3. **Run Setup Script** (on EC2 instance):
   ```bash
   chmod +x setup_ec2_bot_v1.sh
   ./setup_ec2_bot_v1.sh
   ```

4. **Update SSID** (when needed):
   ```bash
   chmod +x update_ssid.sh
   ./update_ssid.sh -r "your-new-ssid-here"
   ```

## Configuration Files

| File | Description |
|------|-------------|
| `config/telegram_config.json` | Telegram API credentials and channel settings |
| `config/pocket_option_config.json` | Pocket Option SSID and trading settings |
| `.env` | Environment variables for Telegram API |

## Testing the Bot

1. **Test Telegram Authentication**:
   ```bash
   source venv/bin/activate
   python check_telegram_session.py --verbose
   ```

2. **Test Pocket Option SSID**:
   ```bash
   source venv/bin/activate
   python test_ssid_direct.py
   ```

3. **Monitor for Signals**:
   ```bash
   source venv/bin/activate
   python monitor_signals.py --duration 300 --verbose
   ```

## Running the Bot

1. **Start the Service**:
   ```bash
   sudo systemctl start selfbot.service
   ```

2. **Check Status**:
   ```bash
   sudo systemctl status selfbot.service
   ```

3. **View Logs**:
   ```bash
   sudo journalctl -u selfbot.service -f
   ```

## Maintenance Tasks

### Updating the SSID

The Pocket Option SSID expires after approximately 24 hours. To update it:

1. Obtain a new SSID from Pocket Option (see [EC2_SETUP_GUIDE.md](EC2_SETUP_GUIDE.md#obtaining-a-valid-ssid))
2. Run the update script:
   ```bash
   ./update_ssid.sh -r "your-new-ssid-here"
   ```

### Restarting the Bot

If you need to restart the bot:

```bash
sudo systemctl restart selfbot.service
```

### Checking Logs

To check the bot logs:

```bash
sudo journalctl -u selfbot.service -f
```

## Troubleshooting

See the [EC2_SETUP_GUIDE.md](EC2_SETUP_GUIDE.md#troubleshooting) for detailed troubleshooting steps.

## Notes

- The bot uses a WebSocket SSID for Pocket Option authentication, not cookies
- The SSID expires after approximately 24 hours and needs to be updated
- The bot monitors the BINARY TRADING CLUB Telegram channel (ID: -1002412213735)
- The EC2 instance is located in Frankfurt (IP: 3.126.128.227)
