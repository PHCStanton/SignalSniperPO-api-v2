#!/bin/bash
# update_ec2_ssid.sh - Script to update the SSID on the EC2 instance

# Configuration
EC2_KEY="EC2/whoami-in-Frankfurt.pem"
EC2_USER="ubuntu"
EC2_HOST="3.126.128.227"
REMOTE_CONFIG_PATH="/home/ubuntu/selfbot/config/pocket_option_config.json"
LOCAL_CONFIG_PATH="config/pocket_option_config.json"
TEMP_CONFIG_PATH="temp_ec2_config.json"

