#!/usr/bin/env python3
"""
install_dependencies.py - Install dependencies for Self Bot v1.0

This script installs all required dependencies for the Self Bot v1.0.
It checks for Python version, installs required packages, and sets up
the directory structure.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

def print_header(message):
    """Print a formatted header message."""
    print("\n" + "=" * 80)
    print(f" {message}")
    print("=" * 80)

def check_python_version():
    """Check if Python version is compatible."""
    print_header("Checking Python version")
    
    required_version = (3, 7)
    current_version = sys.version_info
    
    print(f"Current Python version: {current_version.major}.{current_version.minor}.{current_version.micro}")
    print(f"Required Python version: {required_version[0]}.{required_version[1]}+")
    
    if current_version.major < required_version[0] or \
       (current_version.major == required_version[0] and current_version.minor < required_version[1]):
        print(f"Error: Python {required_version[0]}.{required_version[1]}+ is required.")
        return False
    
    print("Python version check passed.")
    return True

def install_requirements():
    """Install required packages from requirements.txt."""
    print_header("Installing required packages")
    
    requirements_file = "requirements.txt"
    if not os.path.exists(requirements_file):
        print(f"Error: {requirements_file} not found.")
        return False
    
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_file])
        print("All packages installed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error installing packages: {e}")
        return False

def create_directories():
    """Create required directories."""
    print_header("Creating directories")
    
    directories = [
        "config",
        "data",
        "logs"
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")
    
    return True

def check_config_files():
    """Check if configuration files exist."""
    print_header("Checking configuration files")
    
    config_files = [
        "config/bot_config.json",
        "config/telegram_config.json",
        "config/pocket_option_config.json"
    ]
    
    all_exist = True
    for config_file in config_files:
        if os.path.exists(config_file):
            print(f"Found configuration file: {config_file}")
        else:
            print(f"Warning: Configuration file not found: {config_file}")
            all_exist = False
    
    if not all_exist:
        print("\nPlease create the missing configuration files before running the bot.")
    
    return all_exist

def check_pocketoption_api():
    """Check if PocketOptionAPI-v2 is available."""
    print_header("Checking PocketOptionAPI-v2")
    
    api_dir = "PocketOptionAPI-v2"
    if os.path.exists(api_dir) and os.path.isdir(api_dir):
        print(f"Found PocketOptionAPI-v2 directory: {api_dir}")
        return True
    
    print(f"Warning: PocketOptionAPI-v2 directory not found: {api_dir}")
    print("Please make sure the PocketOptionAPI-v2 directory is in the project root.")
    return False

def main():
    """Main function."""
    print_header("Self Bot v1.0 Dependency Installation")
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Create directories
    if not create_directories():
        sys.exit(1)
    
    # Install requirements
    if not install_requirements():
        sys.exit(1)
    
    # Check PocketOptionAPI-v2
    if not check_pocketoption_api():
        sys.exit(1)
    
    # Check configuration files
    check_config_files()
    
    print_header("Installation completed successfully")
    print("You can now run the Self Bot using:")
    print("  python self_bot.py")
    print("For more options, run:")
    print("  python self_bot.py --help")

if __name__ == "__main__":
    main()
