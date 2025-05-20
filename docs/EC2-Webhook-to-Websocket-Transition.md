# EC2 Deployment: Webhook to WebSocket Transition Guide

This document outlines the process for transitioning from the webhook-based approach to the WebSocket-based approach for the Self Bot v1.0 deployment on EC2. It provides step-by-step instructions for testing, deploying, and monitoring the bot on the EC2 instance.

## Overview

The Self Bot v1.0 implementation has evolved from a webhook-based approach to a WebSocket-based approach for both Telegram monitoring and Pocket Option trading. This transition offers several advantages:

1. **Lower Latency**: Direct WebSocket connections reduce signal-to-trade latency.
2. **Improved Reliability**: Eliminates webhook delivery issues and reduces points of failure.
3. **Enhanced Security**: No need to expose public endpoints for webhook callbacks.
4. **Simplified Architecture**: Direct connections to both Telegram and Pocket Option APIs.

## Prerequisites

Before proceeding with the deployment, ensure you have:

1. **EC2 Instance Access**: SSH access to the EC2 instance (IP: 3.126.128.227) using the private key.
2. **Valid Telegram Session**: A working Telegram session file that can access the "BINARY TRADING CLUB" channel.
3. **Fresh SSID**: A valid SSID from Pocket Option for WebSocket authentication.
4. **Updated Configuration Files**: `telegram_config.json`, `pocket_option_config.json`, and `bot_config.json`.

## Testing Process

Before deploying to EC2, it's recommended to test the components locally:

### 1. Test EC2 Connectivity

Use the `test_ssid_ec2.py` script to verify connectivity to the EC2 instance:

```bash
python test_ssid_ec2.py --ec2-host 3.126.128.227 --verbose
```

This script will:
- Test SSH connectivity to the EC2 instance
- Verify that the SSID can authenticate with Pocket Option's WebSocket API

### 2. Test Telegram Session

Verify that your Telegram session can access the "BINARY TRADING CLUB" channel:

```bash
python check_telegram_session.py --verbose
```

### 3. Test Signal Monitoring

Test the signal monitoring functionality without executing trades:

```bash
python monitor_signals.py --duration 300 --verbose
```

### 4. Test Signal Simulation

Simulate trading signals to test the bot's signal parsing:

```bash
python simulate_trading_signals.py --asset "EUR/USD" --direction "HIGHER" --expiry 5 --delay 30
```

## Deployment Process

Once testing is complete, follow these steps to deploy the bot to EC2:

### 1. Prepare Deployment Files

Ensure all necessary files are ready for deployment:

- Updated configuration files (`telegram_config.json`, `pocket_option_config.json`, `bot_config.json`)
- Valid Telegram session file
- Python scripts and dependencies

### 2. Deploy to EC2

Use the standardized deployment script:

```bash
# For Linux/macOS users
./deploy_selfbot.sh

# For Windows users
.\deploy_selfbot.ps1
```

The deployment script will:
- Copy all necessary files to the EC2 instance
- Install required dependencies
- Set up the systemd service for automatic startup
- Configure logging

### 3. Configure Systemd Service

The deployment script will create a systemd service for the bot. You can manually configure it if needed:

```bash
sudo nano /etc/systemd/system/selfbot.service
```

Use the following configuration:

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

### 4. Start and Enable the Service

```bash
sudo systemctl enable selfbot.service
sudo systemctl start selfbot.service
```

## Monitoring and Maintenance

### 1. Monitor Logs

Monitor the bot's logs to ensure it's functioning correctly:

```bash
sudo journalctl -u selfbot.service -f
```

### 2. Check Bot Status

Check the status of the bot service:

```bash
sudo systemctl status selfbot.service
```

### 3. Update SSID

The SSID typically expires after ~24 hours. To update it:

1. Obtain a fresh SSID following the instructions in `extract_po_trade_ssid.md`
2. Update `pocket_option_config.json` on the EC2 instance:
   ```bash
   nano /home/ubuntu/self_bot_v1/config/pocket_option_config.json
   ```
3. Restart the service:
   ```bash
   sudo systemctl restart selfbot.service
   ```

## Testing Options

For the initial deployment, you have several testing options:

1. **Manual Trade Testing**: Run the bot in test mode and manually execute trades to verify functionality.
2. **Simulated Signal Testing**: Use `simulate_trading_signals.py` to generate test signals and verify the bot's response.
3. **Automated Test Mode**: Run the bot in test mode with automated signal detection and trade execution, but without real money.
4. **Low-Amount Real Trading**: Execute real trades with minimal amounts (e.g., $1) to verify end-to-end functionality.

### Option 1: Manual Trade Testing

This approach allows you to manually test the trade execution functionality:

1. SSH into the EC2 instance:
   ```bash
   ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
   ```

2. Navigate to the bot directory:
   ```bash
   cd ~/self_bot_v1
   ```

3. Run the bot with manual trade execution:
   ```bash
   python3 self_bot.py --manual-trade --pair EUR/USD --direction HIGHER --expiry 5 --test-mode
   ```

### Option 2: Simulated Signal Testing

This approach tests the bot's ability to parse and respond to signals:

1. SSH into the EC2 instance:
   ```bash
   ssh -i EC2/whoami-in-Frankfurt.pem ubuntu@3.126.128.227
   ```

2. Navigate to the bot directory:
   ```bash
   cd ~/self_bot_v1
   ```

3. Run the signal simulation script:
   ```bash
   python3 simulate_trading_signals.py --asset "EUR/USD" --direction "HIGHER" --expiry 5 --delay 30
   ```

4. In another terminal, run the bot in test mode:
   ```bash
   python3 self_bot.py --test-mode --verbose
   ```

### Option 3: Automated Test Mode

This approach runs the bot in fully automated mode but with test trades:

1. Ensure `bot_config.json` has `"test_mode": true`
2. Deploy and start the bot service:
   ```bash
   sudo systemctl start selfbot.service
   ```
3. Monitor the logs:
   ```bash
   sudo journalctl -u selfbot.service -f
   ```

### Option 4: Low-Amount Real Trading

This approach tests the complete functionality with real trades:

1. Update `bot_config.json` with:
   ```json
   {
     "test_mode": false,
     "trade_amount": 1,
     "max_daily_trades": 3,
     "max_daily_loss": 3
   }
   ```
2. Deploy and start the bot service:
   ```bash
   sudo systemctl start selfbot.service
   ```
3. Monitor the logs and trade outcomes:
   ```bash
   sudo journalctl -u selfbot.service -f
   ```

## Troubleshooting

### Common Issues and Solutions

1. **WebSocket Connection Failures**
   - **Issue**: Bot fails to connect to Pocket Option WebSocket API
   - **Solution**: Verify SSID is valid and not expired; obtain a fresh SSID if needed

2. **Telegram Authentication Issues**
   - **Issue**: Bot cannot authenticate with Telegram or access the channel
   - **Solution**: Check session file validity; recreate session if needed

3. **Signal Parsing Errors**
   - **Issue**: Bot fails to correctly parse trading signals
   - **Solution**: Verify regex patterns in `telegram_config.json`; update if needed

4. **Trade Execution Failures**
   - **Issue**: Bot fails to execute trades
   - **Solution**: Check WebSocket connection; verify account balance; check trade parameters

5. **Service Startup Failures**
   - **Issue**: Systemd service fails to start
   - **Solution**: Check logs for errors; verify file paths and permissions

### Diagnostic Commands

```bash
# Check service status
sudo systemctl status selfbot.service

# View detailed logs
sudo journalctl -u selfbot.service -f

# Test WebSocket connection
python3 test_ssid_direct.py --ssid "your-ssid-here"

# Check Telegram session
python3 check_telegram_session.py --verbose

# Verify file permissions
ls -la ~/self_bot_v1
```

## Conclusion

The transition from webhook to WebSocket-based architecture offers significant improvements in latency, reliability, and security for the Self Bot v1.0. By following this guide, you can successfully deploy and test the bot on the EC2 instance, ensuring it functions correctly for both signal monitoring and trade execution.

Remember to regularly update the SSID and monitor the bot's performance to ensure continued operation. As you gain confidence in the bot's functionality, you can gradually increase trade amounts and move toward full automation.
