# deploy_selfbot.ps1 - Deploy Self Bot v1.0 to EC2 instance
#
# This PowerShell script deploys the Self Bot v1.0 to an EC2 instance.
# It copies all necessary files, installs dependencies, and sets up
# the systemd service for automatic startup.

# Configuration
$EC2_KEY = "EC2\whoami-in-Frankfurt.pem"
$EC2_USER = "ubuntu"
$EC2_HOST = "3.126.128.227"
$REMOTE_DIR = "/home/ubuntu/self_bot_v1"

# Function to print header
function Print-Header {
    param (
        [string]$Message
    )
    Write-Host "`n===============================================================================" -ForegroundColor Blue
    Write-Host " $Message" -ForegroundColor Blue
    Write-Host "===============================================================================" -ForegroundColor Blue
}

# Check if key file exists
if (-not (Test-Path $EC2_KEY)) {
    Write-Host "Error: EC2 key file not found: $EC2_KEY" -ForegroundColor Red
    exit 1
}

# Check SSH connection
Print-Header "Checking SSH connection to EC2 instance"
try {
    ssh -i $EC2_KEY -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "echo 'SSH connection successful'" 
    Write-Host "SSH connection successful" -ForegroundColor Green
}
catch {
    Write-Host "Error: Failed to connect to EC2 instance" -ForegroundColor Red
    exit 1
}

# Create remote directory
Print-Header "Creating remote directory"
ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR"
Write-Host "Remote directory created: $REMOTE_DIR" -ForegroundColor Green

# Copy files to EC2 instance
Print-Header "Copying files to EC2 instance"
# Create a list of files to copy
$FILES_TO_COPY = @(
    "self_bot.py",
    "requirements.txt",
    "install_dependencies.py",
    "config/bot_config.json",
    "config/telegram_config.json",
    "config/pocket_option_config.json"
)

# Create directories on remote
ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR/config"

# Copy each file
foreach ($file in $FILES_TO_COPY) {
    Write-Host "Copying $file..." -ForegroundColor Yellow
    try {
        scp -i $EC2_KEY $file "$EC2_USER@$EC2_HOST`:$REMOTE_DIR/$file"
    }
    catch {
        Write-Host "Error: Failed to copy $file" -ForegroundColor Red
        exit 1
    }
}

# Copy PocketOptionAPI-v2 directory
Print-Header "Copying PocketOptionAPI-v2 directory"
try {
    scp -i $EC2_KEY -r "PocketOptionAPI-v2" "$EC2_USER@$EC2_HOST`:$REMOTE_DIR/"
    Write-Host "PocketOptionAPI-v2 directory copied successfully" -ForegroundColor Green
}
catch {
    Write-Host "Error: Failed to copy PocketOptionAPI-v2 directory" -ForegroundColor Red
    exit 1
}

# Install dependencies on EC2 instance
Print-Header "Installing dependencies on EC2 instance"
try {
    ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" "cd $REMOTE_DIR && python3 install_dependencies.py"
}
catch {
    Write-Host "Error: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Create systemd service file
Print-Header "Creating systemd service file"
$SERVICE_FILE = "self_bot.service"
$SERVICE_CONTENT = @"
[Unit]
Description=Self Bot v1.0 for Pocket Option Trading
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$REMOTE_DIR
ExecStart=/usr/bin/python3 $REMOTE_DIR/self_bot.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
"@

# Write service file to local temp file
$SERVICE_CONTENT | Out-File -FilePath $SERVICE_FILE -Encoding utf8

# Copy service file to EC2 instance
try {
    scp -i $EC2_KEY $SERVICE_FILE "$EC2_USER@$EC2_HOST`:/tmp/$SERVICE_FILE"
}
catch {
    Write-Host "Error: Failed to copy service file" -ForegroundColor Red
    exit 1
}

# Install service file
try {
    ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" "sudo mv /tmp/$SERVICE_FILE /etc/systemd/system/$SERVICE_FILE && sudo systemctl daemon-reload"
    Write-Host "Systemd service file created and installed" -ForegroundColor Green
}
catch {
    Write-Host "Error: Failed to install service file" -ForegroundColor Red
    exit 1
}

# Clean up local service file
Remove-Item $SERVICE_FILE

# Create run script
Print-Header "Creating run script"
$RUN_SCRIPT = "run_self_bot.sh"
$RUN_SCRIPT_CONTENT = @"
#!/bin/bash
# run_self_bot.sh - Run Self Bot v1.0
cd $REMOTE_DIR
python3 self_bot.py \$@
"@

# Write run script to local temp file
$RUN_SCRIPT_CONTENT | Out-File -FilePath $RUN_SCRIPT -Encoding utf8

# Copy run script to EC2 instance
try {
    scp -i $EC2_KEY $RUN_SCRIPT "$EC2_USER@$EC2_HOST`:$REMOTE_DIR/$RUN_SCRIPT"
}
catch {
    Write-Host "Error: Failed to copy run script" -ForegroundColor Red
    exit 1
}

# Make run script executable
try {
    ssh -i $EC2_KEY "$EC2_USER@$EC2_HOST" "chmod +x $REMOTE_DIR/$RUN_SCRIPT"
    Write-Host "Run script created and made executable" -ForegroundColor Green
}
catch {
    Write-Host "Error: Failed to make run script executable" -ForegroundColor Red
    exit 1
}

# Clean up local run script
Remove-Item $RUN_SCRIPT

# Print instructions
Print-Header "Deployment completed successfully"
Write-Host "Self Bot v1.0 has been deployed to the EC2 instance." -ForegroundColor Green
Write-Host "`nTo start the bot manually:" -ForegroundColor Yellow
Write-Host "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
Write-Host "  cd $REMOTE_DIR"
Write-Host "  ./run_self_bot.sh"
Write-Host ""
Write-Host "To start the bot as a service:" -ForegroundColor Yellow
Write-Host "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
Write-Host "  sudo systemctl start $SERVICE_FILE"
Write-Host ""
Write-Host "To enable the bot to start automatically on boot:" -ForegroundColor Yellow
Write-Host "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
Write-Host "  sudo systemctl enable $SERVICE_FILE"
Write-Host ""
Write-Host "To check the bot's status:" -ForegroundColor Yellow
Write-Host "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
Write-Host "  sudo systemctl status $SERVICE_FILE"
Write-Host ""
Write-Host "To view the bot's logs:" -ForegroundColor Yellow
Write-Host "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
Write-Host "  sudo journalctl -u $SERVICE_FILE -f"
