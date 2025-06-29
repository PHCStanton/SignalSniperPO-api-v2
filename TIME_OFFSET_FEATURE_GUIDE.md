# Time Offset Feature Guide

## Overview

The Time Offset feature allows you to add a configurable delay before executing trades. This is particularly useful for compensating for signal timing variations and ensuring optimal trade entry points.

## Current Configuration

The feature is currently configured to:
- **Apply a 3-second delay** to TeeBinary Premium 5-minute signals
- **No delay** for other channels or signal durations

## Configuration Structure

The time offset configuration is located in `config/bot_config.json`:

```json
"time_offset": {
    "enabled": true,
    "default_offset": 3,
    "channel_specific": {
        "teebinary_premium": {
            "enabled": true,
            "offset_value": 3,
            "apply_to_durations": [5],
            "description": "3-second delay for 5-minute TeeBinary signals"
        },
        "binary_trading_club": {
            "enabled": false,
            "offset_value": 0,
            "apply_to_durations": [],
            "description": "No delay for Binary Trading Club signals"
        },
        "test_channel": {
            "enabled": false,
            "offset_value": 0,
            "apply_to_durations": [],
            "description": "No delay for test channel signals"
        }
    }
}
```

## Configuration Options

### Global Settings
- `enabled`: Master switch for the entire time offset feature (true/false)
- `default_offset`: Default delay in seconds (not currently used, channel-specific settings take precedence)

### Channel-Specific Settings
For each channel, you can configure:
- `enabled`: Whether to apply time offset for this channel (true/false)
- `offset_value`: Delay in seconds before executing the trade
- `apply_to_durations`: Array of signal durations (in minutes) to apply the delay to
- `description`: Human-readable description of the setting

## How It Works

1. When a signal is received, the bot checks if time offset is enabled globally
2. It then checks if there's a channel-specific configuration matching the signal's channel
3. If the channel has time offset enabled AND the signal duration is in the `apply_to_durations` array, the delay is applied
4. The bot logs: "⏱️ TIME OFFSET: Applying X-second delay for Y-minute [channel] signal"
5. After the delay, the trade is executed normally

## Examples

### Example 1: Enable 5-second delay for all TeeBinary signals
```json
"teebinary_premium": {
    "enabled": true,
    "offset_value": 5,
    "apply_to_durations": [1, 5, 15],
    "description": "5-second delay for all TeeBinary signals"
}
```

### Example 2: Add delay to Binary Trading Club 1-minute signals
```json
"binary_trading_club": {
    "enabled": true,
    "offset_value": 2,
    "apply_to_durations": [1],
    "description": "2-second delay for 1-minute Binary Trading Club signals"
}
```

### Example 3: Disable time offset for a specific channel
```json
"teebinary_premium": {
    "enabled": false,
    "offset_value": 3,
    "apply_to_durations": [5],
    "description": "Time offset disabled for TeeBinary Premium"
}
```

## Testing

To test the time offset configuration:

1. Run the test script:
   ```bash
   python test_time_offset.py
   ```

2. The script will:
   - Display current configuration
   - Test offset logic for different scenarios
   - Verify delay execution accuracy

## Adjusting the Configuration

1. Open `config/bot_config.json`
2. Navigate to the `time_offset` section
3. Modify the settings as needed
4. Save the file
5. Restart the bot for changes to take effect

## Important Notes

- The delay is applied BEFORE the trade is executed
- The delay does NOT affect signal detection or parsing
- Each channel can have different delay settings
- You can apply different delays to different signal durations within the same channel
- Setting `offset_value` to 0 effectively disables the delay even if `enabled` is true

## Troubleshooting

### Delay not applying
- Check that `time_offset.enabled` is set to `true` in the global settings
- Verify the channel name matches exactly (case-insensitive)
- Ensure the signal duration is included in `apply_to_durations`
- Check the logs for "TIME OFFSET" messages

### Wrong delay duration
- Verify the `offset_value` is set correctly (in seconds)
- Check that you're looking at the right channel configuration

### Performance impact
- The delay is implemented using `time.sleep()` in a separate thread
- This does not block signal detection or other bot operations
- The delay accuracy is typically within 0.1 seconds

## Use Cases

1. **Signal Provider Timing**: Some signal providers may send signals slightly before the optimal entry time
2. **Network Latency Compensation**: Add a buffer to ensure trades are executed at the right moment
3. **Testing Different Timings**: Experiment with different delays to find optimal entry points
4. **Channel-Specific Requirements**: Different signal sources may require different timing adjustments

## Future Enhancements

Potential improvements that could be added:
- Dynamic delay based on market conditions
- Delay adjustment based on historical performance
- Per-currency-pair delay settings
- Time-of-day based delay adjustments
