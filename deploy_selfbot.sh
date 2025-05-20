#!/bin/bash
# deploy_selfbot.sh - Deploy Self Bot v1.0 to EC2 instance
#
# This script deploys the Self Bot v1.0 to an EC2 instance.
# It copies all necessary files, installs dependencies, and sets up
# the systemd service for automatic startup.

# Configuration
EC2_KEY="EC2/whoami-in-Frankfurt.pem"
EC2_USER="ubuntu"
EC2_HOST="3.126.128.227"
REMOTE_DIR="/home/ubuntu/self_bot_v1"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
print_header() {
    echo -e "\n${BLUE}=========================================================================${NC}"
    echo -e "${BLUE} $1${NC}"
    echo -e "${BLUE}=========================================================================${NC}"
}

# Check if key file exists
if [ ! -f "$EC2_KEY" ]; then
    echo -e "${RED}Error: EC2 key file not found: $EC2_KEY${NC}"
    exit 1
fi

# Fix permissions on key file
chmod 400 "$EC2_KEY"

# Check SSH connection
print_header "Checking SSH connection to EC2 instance"
ssh -i "$EC2_KEY" -o StrictHostKeyChecking=no "$EC2_USER@$EC2_HOST" "echo -e '${GREEN}SSH connection successful${NC}'" || {
    echo -e "${RED}Error: Failed to connect to EC2 instance${NC}"
    exit 1
}

# Create remote directory
print_header "Creating remote directory"
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR"
echo -e "${GREEN}Remote directory created: $REMOTE_DIR${NC}"

# Copy files to EC2 instance
print_header "Copying files to EC2 instance"
# Create a list of files to copy
FILES_TO_COPY=(
    "self_bot.py"
    "requirements.txt"
    "install_dependencies.py"
    "config/bot_config.json"
    "config/telegram_config.json"
    "config/pocket_option_config.json"
)

# Create directories on remote
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "mkdir -p $REMOTE_DIR/config"

# Copy each file
for file in "${FILES_TO_COPY[@]}"; do
    echo -e "${YELLOW}Copying $file...${NC}"
    scp -i "$EC2_KEY" "$file" "$EC2_USER@$EC2_HOST:$REMOTE_DIR/$file" || {
        echo -e "${RED}Error: Failed to copy $file${NC}"
        exit 1
    }
done

# Copy PocketOptionAPI-v2 directory
print_header "Copying PocketOptionAPI-v2 directory"
scp -i "$EC2_KEY" -r "PocketOptionAPI-v2" "$EC2_USER@$EC2_HOST:$REMOTE_DIR/" || {
    echo -e "${RED}Error: Failed to copy PocketOptionAPI-v2 directory${NC}"
    exit 1
}
echo -e "${GREEN}PocketOptionAPI-v2 directory copied successfully${NC}"

# Install dependencies on EC2 instance
print_header "Installing dependencies on EC2 instance"
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "cd $REMOTE_DIR && python3 install_dependencies.py" || {
    echo -e "${RED}Error: Failed to install dependencies${NC}"
    exit 1
}

# Create systemd service file
print_header "Creating systemd service file"
SERVICE_FILE="self_bot.service"
cat > "$SERVICE_FILE" << EOF
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
EOF

# Copy service file to EC2 instance
scp -i "$EC2_KEY" "$SERVICE_FILE" "$EC2_USER@$EC2_HOST:/tmp/$SERVICE_FILE" || {
    echo -e "${RED}Error: Failed to copy service file${NC}"
    exit 1
}

# Install service file
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "sudo mv /tmp/$SERVICE_FILE /etc/systemd/system/$SERVICE_FILE && sudo systemctl daemon-reload" || {
    echo -e "${RED}Error: Failed to install service file${NC}"
    exit 1
}
echo -e "${GREEN}Systemd service file created and installed${NC}"

# Clean up local service file
rm "$SERVICE_FILE"

# Create run script
print_header "Creating run script"
RUN_SCRIPT="run_self_bot.sh"
cat > "$RUN_SCRIPT" << EOF
#!/bin/bash
# run_self_bot.sh - Run Self Bot v1.0
cd $REMOTE_DIR
python3 self_bot.py \$@
EOF

# Copy run script to EC2 instance
scp -i "$EC2_KEY" "$RUN_SCRIPT" "$EC2_USER@$EC2_HOST:$REMOTE_DIR/$RUN_SCRIPT" || {
    echo -e "${RED}Error: Failed to copy run script${NC}"
    exit 1
}

# Make run script executable
ssh -i "$EC2_KEY" "$EC2_USER@$EC2_HOST" "chmod +x $REMOTE_DIR/$RUN_SCRIPT" || {
    echo -e "${RED}Error: Failed to make run script executable${NC}"
    exit 1
}
echo -e "${GREEN}Run script created and made executable${NC}"

# Clean up local run script
rm "$RUN_SCRIPT"

# Print instructions
print_header "Deployment completed successfully"
echo -e "${GREEN}Self Bot v1.0 has been deployed to the EC2 instance.${NC}"
echo -e "${YELLOW}To start the bot manually:${NC}"
echo -e "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo -e "  cd $REMOTE_DIR"
echo -e "  ./run_self_bot.sh"
echo -e ""
echo -e "${YELLOW}To start the bot as a service:${NC}"
echo -e "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo -e "  sudo systemctl start $SERVICE_FILE"
echo -e ""
echo -e "${YELLOW}To enable the bot to start automatically on boot:${NC}"
echo -e "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo -e "  sudo systemctl enable $SERVICE_FILE"
echo -e ""
echo -e "${YELLOW}To check the bot's status:${NC}"
echo -e "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo -e "  sudo systemctl status $SERVICE_FILE"
echo -e ""
echo -e "${YELLOW}To view the bot's logs:${NC}"
echo -e "  ssh -i $EC2_KEY $EC2_USER@$EC2_HOST"
echo -e "  sudo journalctl -u $SERVICE_FILE -f"
