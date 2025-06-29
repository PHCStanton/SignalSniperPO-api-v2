# SignalSniper Timeframe Toggle Feature Guide

## Overview

The Timeframe Toggle feature allows users to selectively enable or disable specific trading timeframes (1-minute, 3-minute, 5-minute, etc.) for the SignalSniper bot. This provides granular control over which signals the bot will process and execute trades for.

## Features

- **Interactive Configuration**: Easy-to-use script for managing timeframe settings
- **Real-time Control**: Changes take effect immediately without code modifications
- **Manual Review**: Built-in prompts for user confirmation before applying changes
- **Backup System**: Automatic backup creation before configuration changes
- **Integration**: Seamless integration with both SignalSniper.py and SignalSniper_mod.py

## Files Created

### 1. Configuration File
- **Path**: `config/timeframe_config.json`
- **Purpose**: Stores timeframe enable/disable settings
- **Default**: Enables 1, 3, and 5-minute timeframes

### 2. Toggle Script
- **Path**: `timeframe_toggle.py`
- **Purpose**: Interactive script for managing timeframe settings
- **Usage**: `python timeframe_toggle.py`

### 3. Test Suite
- **Path**: `test_timeframe_toggle.py`
- **Purpose**: Comprehensive testing of timeframe toggle functionality
- **Usage**: `python test_timeframe_toggle.py`

## Configuration Structure

```json
{
    "timeframe_control": {
        "enabled": true,
        "description": "Timeframe suspension control for SignalSniper bot",
        "default_enabled_timeframes": [1, 3, 5],
        "available_timeframes": [1, 2, 3, 4, 5, 10, 15, 30, 60],
        "suspended_timeframes": [],
        "last_updated": "2025-06-28T19:02:00Z",
        "updated_by": "timeframe_toggle_system"
    },
    "timeframe_settings": {
        "1": {
            "enabled": true,
            "description": "1-minute signals",
            "typical_channels": ["BINARY TRADING CLUB", "Generic"],
            "optimization_available": true
        },
        "5": {
            "enabled": true,
            "description": "5-minute signals",
            "typical_channels": ["TeeBinary Premium"],
            "optimization_available": false
        }
    },
    "suspension_rules": {
        "manual_review_required": true,
        "prompt_user_for_suspension": true,
        "allow_runtime_changes": true,
        "backup_before_changes": true,
        "log_all_changes": true
    }
}
```

## How to Use

### 1. Interactive Toggle Script

Run the timeframe toggle script:

```bash
python timeframe_toggle.py
```

**Menu Options:**
1. **View Current Status** - Display all timeframe settings
2. **Suspend Timeframes** - Disable specific timeframes
3. **Enable Timeframe** - Re-enable suspended timeframes
4. **Reset to Defaults** - Restore default settings (1, 3, 5 minutes)
5. **Save & Exit** - Apply changes and restart bot
6. **Exit Without Saving** - Discard changes

### 2. Suspending Timeframes

When prompted "Which Timeframes should be suspended:", you can:

- **Suspend multiple**: `1,3,5` (comma-separated)
- **Suspend single**: `2`
- **Suspend with spaces**: `1, 3, 5`
- **No suspension**: `none` or leave empty

### 3. Example Usage Session

```
🎯 SIGNALSNIPER TIMEFRAME TOGGLE CONTROL
============================================================
1. 📊 View Current Status
2. 🚫 Suspend Timeframes
3. ✅ Enable Timeframe
4. 🔄 Reset to Defaults
5. 💾 Save & Exit
6. ❌ Exit Without Saving
------------------------------------------------------------
🎯 Select option (1-6): 2

🔧 TIMEFRAME SUSPENSION CONFIGURATION
============================================================

📊 Currently Enabled Timeframes: [1, 3, 5]

❓ Which Timeframes should be suspended:
   (Enter timeframe numbers separated by commas, or 'none' for no changes)
   (Example: 1,2,5 or none)

🎯 Enter timeframes to suspend: 2,10

📋 Timeframes to suspend: [2, 10]
✅ Confirm suspension? (y/n): y
✅ Successfully suspended timeframes: [2, 10]
```

## Integration with SignalSniper Bot

### Signal Validation Process

The bot now includes timeframe validation in the signal processing pipeline:

1. **Signal Received** - Bot receives trading signal from Telegram
2. **Timeframe Check** - `validate_timeframe()` method checks if timeframe is enabled
3. **Validation Result**:
   - ✅ **Enabled**: Signal proceeds to trade execution
   - ❌ **Disabled**: Signal is blocked with log message

### Code Integration

The timeframe validation is integrated into the `validate_signal()` method:

```python
def validate_signal(self, signal: Dict) -> Tuple[bool, str]:
    """Validate a trading signal."""
    try:
        # Check timeframe suspension first
        timeframe_valid, timeframe_message = self.validate_timeframe(signal)
        if not timeframe_valid:
            return False, timeframe_message
        
        # Continue with other validations...
```

### Log Messages

When timeframes are suspended, you'll see log messages like:

```
❌ Invalid signal: Timeframe 2 minutes is suspended
❌ Invalid signal: Timeframe 10 minutes is disabled
✅ Signal validation passed: Timeframe 5 minutes is enabled
```

## Default Configuration

### Enabled by Default
- **1 minute**: Binary Trading Club signals, 59-second optimization available
- **3 minute**: Generic signals
- **5 minute**: TeeBinary Premium signals

### Disabled by Default
- **2 minute**: Generic signals
- **4 minute**: Generic signals
- **10 minute**: Generic signals
- **15 minute**: Generic signals
- **30 minute**: Generic signals
- **60 minute**: Generic signals

## Channel-Specific Behavior

### TeeBinary Premium
- **Primary Timeframe**: 5 minutes
- **Signal Format**: Single message (EUR/USD CALL 5MIN)
- **Time Offset**: 5-second delay configured

### Binary Trading Club
- **Primary Timeframe**: 1 minute
- **Signal Format**: Two-message format
- **Optimization**: 59-second trade duration available

### Generic Channels
- **Supported Timeframes**: 1-60 minutes
- **Default Behavior**: Follows global timeframe settings

## Testing

### Run Comprehensive Tests

```bash
python test_timeframe_toggle.py
```

**Test Coverage:**
1. ✅ Configuration file creation and structure
2. ✅ Toggle script functionality
3. ✅ Signal validation integration
4. ✅ Timeframe suspension simulation
5. ✅ Interactive prompt simulation

### Expected Test Results

```
🎯 SIGNALSNIPER TIMEFRAME TOGGLE COMPREHENSIVE TEST
============================================================

📋 Test 1: Timeframe Configuration File
--------------------------------------------------
✅ Found section: timeframe_control
✅ Found section: timeframe_settings
✅ Found section: suspension_rules
✅ Default enabled timeframes correct: [1, 3, 5]
✅ Timeframe configuration structure is valid

✅ Configuration File Creation: PASSED

🔧 Test 2: Timeframe Toggle Script
--------------------------------------------------
✅ Configuration loaded successfully
✅ Enabled timeframes detected correctly: {1, 3, 5}
✅ Suspended timeframes detected: set()
✅ Timeframe toggle script functionality verified

✅ Toggle Script Functionality: PASSED

🎯 Test 3: Signal Validation Integration
--------------------------------------------------
   1 min: ✅ ALLOWED    | 1-minute signal (should be enabled)     | Timeframe 1 minutes is enabled
   2 min: ❌ BLOCKED    | 2-minute signal (should be disabled)    | Timeframe 2 minutes is disabled
   3 min: ✅ ALLOWED    | 3-minute signal (should be enabled)     | Timeframe 3 minutes is enabled
   5 min: ✅ ALLOWED    | 5-minute signal (should be enabled)     | Timeframe 5 minutes is enabled
  10 min: ❌ BLOCKED    | 10-minute signal (should be disabled)   | Timeframe 10 minutes is disabled
✅ Signal validation integration tested

✅ Signal Validation Integration: PASSED

🚫 Test 4: Timeframe Suspension Simulation
--------------------------------------------------
✅ Simulated suspension of 1-minute timeframe
✅ 1-minute timeframe correctly blocked when suspended
✅ Original configuration restored
✅ Timeframe suspension simulation completed successfully

✅ Timeframe Suspension Simulation: PASSED

❓ Test 5: Interactive Prompt Simulation
--------------------------------------------------
📊 Currently Enabled Timeframes: [1, 3, 5]
✅ Input '1,3': Valid comma-separated input - Parsed correctly: [1, 3]
✅ Input '5': Single timeframe input - Parsed correctly: [5]
✅ Input '1, 3, 5': Comma-separated with spaces - Parsed correctly: [1, 3, 5]
✅ Input 'none': No suspension input - Parsed correctly: []
✅ Input '': Empty input - Parsed correctly: []
✅ Input '2,10': Invalid timeframes (not enabled) - Parsed correctly: []
✅ Interactive prompt simulation completed successfully

✅ Interactive Prompt Simulation: PASSED

============================================================
📊 TEST RESULTS SUMMARY
============================================================
Total Tests: 5
Passed: 5
Failed: 0
Success Rate: 100.0%

🎉 ALL TESTS PASSED! Timeframe toggle feature is working correctly.

📋 FEATURE SUMMARY:
✅ Timeframe configuration system implemented
✅ Interactive toggle script created
✅ Signal validation integration working
✅ Suspension functionality verified
✅ User prompt system functional

🚀 READY FOR DEPLOYMENT!
```

## Troubleshooting

### Common Issues

1. **Configuration File Not Found**
   - Run `python timeframe_toggle.py` to create default configuration
   - Check that `config/` directory exists

2. **Changes Not Taking Effect**
   - Restart the SignalSniper bot after making changes
   - Verify configuration was saved properly

3. **All Signals Being Blocked**
   - Check if timeframe control is enabled in config
   - Verify at least one timeframe is enabled
   - Use "Reset to Defaults" option

### Debug Information

Enable verbose logging in the bot to see timeframe validation messages:

```bash
python SignalSniper_mod.py --verbose
```

Look for log messages like:
```
🎯 Timeframe 5 minutes is enabled
❌ Timeframe 2 minutes is disabled
🚫 Timeframe 1 minutes is suspended
```

## Future Enhancements

### Planned Features
- **Channel-Specific Timeframes**: Different timeframe settings per channel
- **Time-Based Rules**: Enable/disable timeframes based on time of day
- **Performance Analytics**: Track performance by timeframe
- **Quick Toggle Hotkeys**: Keyboard shortcuts for common operations

### Integration Possibilities
- **Web Interface**: Browser-based timeframe management
- **Telegram Commands**: Control timeframes via Telegram bot commands
- **API Endpoints**: REST API for external timeframe control

## Support

For issues or questions regarding the Timeframe Toggle feature:

1. Run the test suite: `python test_timeframe_toggle.py`
2. Check configuration: `python timeframe_toggle.py` → Option 1
3. Review logs for timeframe validation messages
4. Reset to defaults if needed: `python timeframe_toggle.py` → Option 4

## Summary

The Timeframe Toggle feature provides comprehensive control over which trading timeframes the SignalSniper bot will process. With its intuitive interface, robust testing, and seamless integration, it enables users to fine-tune their trading strategy by selectively enabling or disabling specific timeframes based on their preferences and market conditions.

**Key Benefits:**
- ✅ **Granular Control**: Enable/disable specific timeframes
- ✅ **Easy Management**: Interactive script with clear prompts
- ✅ **Safe Operation**: Backup system and confirmation prompts
- ✅ **Real-time Updates**: Changes apply immediately
- ✅ **Comprehensive Testing**: Full test suite ensures reliability
- ✅ **Bot Integration**: Seamless integration with existing signal processing
