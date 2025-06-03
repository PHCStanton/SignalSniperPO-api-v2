#!/bin/bash
# update_ssid.sh - Script to update the Pocket Option SSID in the configuration file
# Run this script on your EC2 instance in the self_bot_v1 directory

# Default values
CONFIG_FILE="config/pocket_option_config.json"
RESTART_SERVICE=false
TEST_CONNECTION=true

# Function to display usage information
usage() {
    echo "Usage: $0 [options] <ssid>"
    echo "Options:"
    echo "  -c, --config <file>     Specify the config file (default: $CONFIG_FILE)"
    echo "  -r, --restart           Restart the selfbot service after updating"
    echo "  -n, --no-test           Skip testing the connection"
    echo "  -h, --help              Display this help message"
    echo ""
    echo "Example:"
    echo "  $0 \"a:4:{s:10:\\\"session_id\\\";s:32:\\\"bde3d74bbc70c9e768874d0e3ec00fb4\\\";...}\""
    exit 1
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -r|--restart)
            RESTART_SERVICE=true
            shift
            ;;
        -n|--no-test)
            TEST_CONNECTION=false
            shift
            ;;
        -h|--help)
            usage
            ;;
        *)
            SSID="$1"
            shift
            ;;
    esac
done

# Check if SSID is provided
if [ -z "$SSID" ]; then
    echo "Error: No SSID provided."
    usage
fi

# Check if config file exists
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found: $CONFIG_FILE"
    echo "Creating a new config file..."
    mkdir -p $(dirname "$CONFIG_FILE")
    cat > "$CONFIG_FILE" << EOL
{
  "ssid": "$SSID",
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
EOL
    echo "Created new config file: $CONFIG_FILE"
else
    # Update the SSID in the config file
    echo "Updating SSID in $CONFIG_FILE..."
    
    # Check if jq is installed
    if command -v jq &> /dev/null; then
        # Use jq to update the SSID
        jq --arg ssid "$SSID" '.ssid = $ssid' "$CONFIG_FILE" > "$CONFIG_FILE.tmp" && mv "$CONFIG_FILE.tmp" "$CONFIG_FILE"
    else
        # Fallback to sed if jq is not available
        sed -i "s|\"ssid\": \"[^\"]*\"|\"ssid\": \"$SSID\"|" "$CONFIG_FILE"
    fi
    
    echo "SSID updated successfully."
fi

# Test the connection if requested
if [ "$TEST_CONNECTION" = true ]; then
    echo "Testing connection with the new SSID..."
    
    # Check if we're in a virtual environment
    if [ -d "venv" ]; then
        source venv/bin/activate
    fi
    
    # Run the test script if it exists
    if [ -f "test_ssid_direct.py" ]; then
        python test_ssid_direct.py
        TEST_RESULT=$?
        
        if [ $TEST_RESULT -ne 0 ]; then
            echo "Warning: Connection test failed. The SSID may be invalid."
            echo "You can still proceed, but the bot may not work correctly."
            
            # Ask for confirmation to continue
            read -p "Do you want to continue anyway? (y/n) " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                echo "Operation cancelled."
                exit 1
            fi
        else
            echo "Connection test successful. The SSID is valid."
        fi
    else
        echo "Warning: test_ssid_direct.py not found. Skipping connection test."
    fi
fi

# Restart the service if requested
if [ "$RESTART_SERVICE" = true ]; then
    echo "Restarting selfbot service..."
    sudo systemctl restart selfbot.service
    
    # Check if the service started successfully
    sleep 2
    if sudo systemctl is-active --quiet selfbot.service; then
        echo "Service restarted successfully."
    else
        echo "Warning: Service failed to restart. Check the logs with:"
        echo "sudo journalctl -u selfbot.service -f"
    fi
fi

echo "SSID update complete."
echo ""
echo "Next steps:"
echo "1. If you didn't restart the service, you can do so with:"
echo "   sudo systemctl restart selfbot.service"
echo ""
echo "2. Check the service status with:"
echo "   sudo systemctl status selfbot.service"
echo ""
echo "3. View the logs with:"
echo "   sudo journalctl -u selfbot.service -f"
