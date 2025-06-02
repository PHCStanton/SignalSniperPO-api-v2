# PowerShell Virtual Environment Fix Guide

## Problem Summary
You're experiencing permission issues when trying to create a Python virtual environment in PowerShell, getting:
```
Error: [Errno 13] Permission denied: 'C:\\projects\\SignalSniper\\venv\\Scripts\\python.exe'
```

This is happening because VS Code is running as Administrator, which creates permission conflicts with virtual environments.

## Solution Overview

I've created an updated PowerShell script (`run_bot_powershell.ps1`) that handles these permission issues automatically. The script works both inside and outside VS Code, with or without Administrator privileges.

## How to Run the Bot

### Method 1: Using the Batch File (Easiest)
1. **Outside VS Code**, navigate to `C:\projects\SignalSniper`
2. Double-click `run_bot.bat`
3. The bot will start automatically with proper permission handling

### Method 2: Using PowerShell Directly
1. Open PowerShell **WITHOUT** Administrator privileges
2. Navigate to your project:
   ```powershell
   cd C:\projects\SignalSniper
   ```
3. Run the script:
   ```powershell
   .\run_bot_powershell.ps1
   ```

### Method 3: If You Need to Create a New Virtual Environment
If the existing venv has permission issues:
```powershell
.\run_bot_powershell.ps1 -CreateNewVenv
```

## Script Features

The updated `run_bot_powershell.ps1` script includes:

1. **Automatic Permission Handling**
   - Detects if running as Administrator
   - Applies appropriate permission fixes
   - Works with both admin and non-admin contexts

2. **Virtual Environment Management**
   - Automatically creates venv if missing
   - Fixes permission issues on existing venv
   - Uses alternative activation methods if needed

3. **Performance Optimizations**
   - Sets high process priority for low latency
   - Adds Windows Defender exclusions (when admin)
   - Optimized for trading performance

4. **Error Recovery**
   - Multiple fallback methods for venv activation
   - Detailed error messages and troubleshooting tips
   - Automatic dependency installation

## Command Line Options

- `-CreateNewVenv`: Forces creation of a new virtual environment
- `-Debug`: Shows detailed environment information
- `-SkipVenvCheck`: Skips dependency verification (faster startup)
- `-Force`: Forces execution even with warnings

## Troubleshooting

### If you still get permission errors:

1. **Close VS Code completely**
2. Open a new PowerShell window (NOT as Administrator)
3. Run: `.\run_bot_powershell.ps1 -CreateNewVenv`

### If PowerShell execution is blocked:

Run this command first:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### If Python is not found:

1. Ensure Python is installed from https://python.org
2. Make sure "Add Python to PATH" was checked during installation
3. Restart PowerShell after Python installation

## Best Practices for Low Latency

1. **Run Outside VS Code**: VS Code adds overhead, especially when running as Administrator
2. **Use the Batch File**: The `run_bot.bat` file is optimized for quick startup
3. **Keep PowerShell Open**: Don't close the PowerShell window while trading
4. **Monitor Performance**: Use the `-Debug` flag to see environment details

## Quick Start Commands

```powershell
# Normal run
.\run_bot_powershell.ps1

# Create new venv and run
.\run_bot_powershell.ps1 -CreateNewVenv

# Run with debug info
.\run_bot_powershell.ps1 -Debug

# Quick run (skip checks)
.\run_bot_powershell.ps1 -SkipVenvCheck
```

## Files Created

- `run_bot_powershell.ps1` - Main PowerShell script with permission handling
- `run_bot.bat` - Simple batch file for double-click execution
- `fix_powershell_venv.ps1` - Original venv fix script (still available)

## Next Steps

1. Close VS Code
2. Double-click `run_bot.bat` in Windows Explorer
3. The bot should start with proper permissions and low latency

If you encounter any issues, the script provides detailed error messages to help diagnose the problem.
