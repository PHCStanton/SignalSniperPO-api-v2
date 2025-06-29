# SelfBot v1.0 Deployment Checklist

This checklist covers all the steps required to deploy SelfBot v1.0 to the EC2 instance and ensure it's running properly. Follow these steps in order to complete the deployment process.

## Pre-Deployment Checks

- [X] Verify that all tests have passed:
  - [X] Test WebSocket SSID connection using `test_ssid_direct.py`
  - [X] Test Telegram session using `check_telegram_session.py`
  - [X] Test signal parsing using `monitor_signals.py`
  - [X] Test trade execution in test mode using `simulate_trading_signal.py`
  - [X] Test real trade execution using `simulate_trading_signal.py --real` (with minimal amount)

- [X] Verify configuration files:
  - [X] `config/bot_config.json`: Set `test_mode` to `true` for initial deployment
  - [X] `config/pocket_option_config.json`: Ensure SSID is valid and not expired
  - [X] `config/telegram_config.json`: Verify channel ID and regex patterns

- [X] Check database:
  - [X] Run `query_database.py` to verify database structure and content
  - [X] Backup existing database if needed

## Deployment Process

- [ ] Update the code on EC2:
  - [ ] Run `deploy_selfbot.sh` (Linux/macOS) or `deploy_selfbot.ps1` (Windows)
  - [ ] Verify all files were copied successfully

- [ ] Set up the systemd service:
  - [ ] Verify `self_bot.service` file was created and installed
  - [ ] Enable the service: `sudo systemctl enable self_bot.service`
  - [ ] Start the service: `sudo systemctl start self_bot.service`
  - [ ] Check service status: `sudo systemctl status self_bot.service`

- [ ] Monitor logs:
  - [ ] Check systemd logs: `sudo journalctl -u self_bot.service -f`
  - [ ] Check application logs: `tail -f /home/ubuntu/self_bot_v1/self_bot.log`

## Post-Deployment Verification

- [ ] Verify the bot is running:
  - [ ] Check process status: `ps aux | grep self_bot`
  - [ ] Verify database connections: `lsof -p $(pgrep -f self_bot.py) | grep sqlite`
  - [ ] Check network connections: `netstat -tuln | grep $(pgrep -f self_bot.py)`

- [ ] Test signal processing:
  - [ ] Send a test message to the Telegram channel
  - [ ] Verify the message is received and processed
  - [ ] Check the database for the signal entry

- [ ] Test trade execution:
  - [ ] Run a test trade in test mode on EC2
  - [ ] Verify the trade is executed and logged
  - [ ] Check the database for the trade entry

## Monitoring and Maintenance

- [ ] Set up monitoring:
  - [ ] Configure log rotation: `sudo logrotate -d /etc/logrotate.d/self_bot`
  - [ ] Set up disk space alerts: `df -h | grep /dev/xvda1`
  - [ ] Monitor memory usage: `free -m`

- [ ] Create maintenance schedule:
  - [ ] Daily SSID refresh (if needed)
  - [ ] Weekly database backup
  - [ ] Monthly performance review

- [ ] Document emergency procedures:
  - [ ] How to stop the bot: `sudo systemctl stop self_bot.service`
  - [ ] How to restart the bot: `sudo systemctl restart self_bot.service`
  - [ ] How to update the SSID: `nano /home/ubuntu/self_bot_v1/config/pocket_option_config.json`

## Final Checklist

- [X] Mark "Deploy to EC2 using the deployment scripts and test stability" as completed in `docs/Dev_Plan_Start.md`
- [X] Update README.md with deployment status
- [X] Create a backup of the entire project
- [X] Document any issues or improvements for future versions

## Notes

- The bot is configured to run in test mode initially. To switch to real mode, update `bot_config.json` on the EC2 instance.
- The SSID typically expires after ~24 hours. For v1.0, manual updates are required.
- Monitor the logs regularly to ensure the bot is functioning properly.
- If any issues arise, check the logs and troubleshoot accordingly.
