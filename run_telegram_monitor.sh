#!/bin/bash
# run_telegram_monitor.sh - Script to run the Telegram signal monitoring test suite
#
# This script runs the check_telegram_session.py script to verify that we have a valid
# Telegram session and can access the BINARY TRADING CLUB channel, and then runs the
# monitor_signals.py script to monitor for signals.
#
# Usage:
#   ./run_telegram_monitor.sh [--duration SECONDS] [--verbose]

# Parse command line arguments
DURATION=""
VERBOSE=""

while [[ $# -gt 0 ]]; do
  case $1 in
    --duration)
      DURATION="--duration $2"
      shift 2
      ;;
    --verbose)
      VERBOSE="--verbose"
      shift
      ;;
    *)
      echo "Unknown option: $1"
      echo "Usage: ./run_telegram_monitor.sh [--duration SECONDS] [--verbose]"
      exit 1
      ;;
  esac
done

echo "Telegram Signal Monitoring Test Suite"
echo "------------------------------------"
echo ""

# Check if Python is installed
if ! command -v python &> /dev/null; then
    echo "Error: Python is not installed or not in PATH"
    exit 1
fi

# Check if required scripts exist
if [ ! -f "check_telegram_session.py" ]; then
    echo "Error: check_telegram_session.py not found"
    exit 1
fi

if [ ! -f "monitor_signals.py" ]; then
    echo "Error: monitor_signals.py not found"
    exit 1
fi

# Create data directory if it doesn't exist
mkdir -p data

# Step 1: Check Telegram session
echo "Step 1: Checking Telegram session..."
python check_telegram_session.py $VERBOSE

# Check if the session check was successful
if [ $? -ne 0 ]; then
    echo "Error: Telegram session check failed"
    echo "Please fix the session issues before continuing"
    exit 1
fi

echo ""
echo "Step 2: Starting signal monitor..."
echo "Press Ctrl+C to stop monitoring"
echo ""

# Step 2: Run signal monitor
python monitor_signals.py $DURATION $VERBOSE

# Check if the monitor was stopped by the user
if [ $? -eq 130 ]; then
    echo ""
    echo "Signal monitor stopped by user"
    exit 0
elif [ $? -ne 0 ]; then
    echo ""
    echo "Error: Signal monitor exited with an error"
    exit 1
fi

echo ""
echo "Signal monitoring completed successfully"
