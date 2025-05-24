# Telegram Signal to Pocket Option API: Parsing Guide

This document provides a comprehensive guide on how to correctly parse Telegram signals from the BINARY TRADING CLUB channel and convert them to the appropriate format for the Pocket Option API.

## Signal Format Analysis

Based on the examples in the `docs/parsing-Telegram-signals/` folder, the trading signals follow a specific pattern:

### Signal Types

1. **Two-Message Format**:
   - **First Message**: Contains the trading pair
   - **Second Message**: Contains timer, direction, and expiry

2. **Single-Message Format**:
   - Contains all information in one message (trading pair, direction, and expiry)

### Example Signals

#### Two-Message Format:
```
🔴Trading Pair: AUD/USD (OTC)

❗️SET THE TIMER TO 00:01:00❗️
LOWER ⬇️
Trade time: 1 MIN
```

#### Single-Message Format:
```
🔥 Trade signal: USD/JPY
HIGHER ⬆️
Set to: 1 MIN
```

## Parsing Strategy

### 1. Extract Key Components

For each signal, we need to extract:

- **Trading Pair**: e.g., "AUD/USD"
- **Direction**: "HIGHER" or "LOWER"
- **Timer**: e.g., "00:01:00" (when to execute the trade)
- **Expiry**: e.g., "1 MIN" (duration of the trade)

### 2. Regex Patterns

Based on the signal variations, here are the recommended regex patterns:

```python
# Trading Pair (handles both formats)
pair_pattern = r'(Trading Pair:|Trade signal:)\s*([A-Z]{3}/[A-Z]{3})'

# Direction
direction_pattern = r'\b(HIGHER|LOWER)\b'

# Timer
timer_pattern = r'(SET THE TIMER TO|TIMER TO)\s*(\d{2}:\d{2}:\d{2})'

# Expiry (handles both formats)
expiry_pattern = r'(Trade time:|Set to:)\s*(\d+)\s*MIN'
```

### 3. Conversion to Pocket Option API Format

After extracting the signal components, they need to be converted to the format expected by the Pocket Option API:

| Signal Component | Telegram Format | Pocket Option API Format |
|------------------|----------------|--------------------------|
| Trading Pair     | "EUR/USD"      | "EURUSD"                 |
| Direction        | "HIGHER"       | "call"                   |
| Direction        | "LOWER"        | "put"                    |
| Expiry           | "1 MIN"        | 60 (seconds)             |

## Implementation Example

Here's a complete implementation that correctly parses Telegram signals and converts them to the Pocket Option API format:

```python
import re
from datetime import datetime, timedelta
import asyncio

def parse_telegram_signal(message_text):
    """
    Parse a Telegram signal message and extract trading information.
    
    Args:
        message_text: The text of the Telegram message
        
    Returns:
        Dictionary with parsed signal data or None if parsing failed
    """
    # Define regex patterns
    pair_pattern = r'(Trading Pair:|Trade signal:)\s*([A-Z]{3}/[A-Z]{3})'
    direction_pattern = r'\b(HIGHER|LOWER)\b'
    timer_pattern = r'(SET THE TIMER TO|TIMER TO)\s*(\d{2}:\d{2}:\d{2})'
    expiry_pattern = r'(Trade time:|Set to:)\s*(\d+)\s*MIN'
    
    # Extract data using regex
    pair_match = re.search(pair_pattern, message_text, re.IGNORECASE)
    direction_match = re.search(direction_pattern, message_text, re.IGNORECASE)
    timer_match = re.search(timer_pattern, message_text, re.IGNORECASE)
    expiry_match = re.search(expiry_pattern, message_text, re.IGNORECASE)
    
    # Check if we have the minimum required information
    if not (pair_match and direction_match):
        return None
    
    # Extract values
    pair = pair_match.group(2)
    direction = direction_match.group(1).upper()
    timer = timer_match.group(2) if timer_match else None
    expiry = int(expiry_match.group(2)) if expiry_match else 1  # Default to 1 minute if not specified
    
    # Create signal dictionary
    signal = {
        "pair": pair,
        "direction": direction,
        "timer": timer,
        "expiry": expiry
    }
    
    return signal

def convert_to_pocket_option_format(signal):
    """
    Convert a parsed Telegram signal to Pocket Option API format.
    
    Args:
        signal: Dictionary with parsed signal data
        
    Returns:
        Dictionary with data in Pocket Option API format
    """
    # Convert pair format (remove slash)
    asset = signal["pair"].replace("/", "")
    
    # Convert direction
    direction_map = {"HIGHER": "call", "LOWER": "put"}
    direction = direction_map.get(signal["direction"])
    
    # Convert expiry to seconds
    duration = signal["expiry"] * 60
    
    return {
        "asset": asset,
        "direction": direction,
        "duration": duration
    }

async def execute_trade(pocket_option_client, signal_data, amount=10):
    """
    Execute a trade using the Pocket Option API.
    
    Args:
        pocket_option_client: Initialized PocketOption client
        signal_data: Dictionary with parsed and converted signal data
        amount: Trade amount
        
    Returns:
        Trade result or None if execution failed
    """
    try:
        # Execute the trade
        result = pocket_option_client.buy(
            amount=amount,
            active=signal_data["asset"],
            action=signal_data["direction"],
            expirations=signal_data["duration"]
        )
        
        if result and result[0]:
            trade_id = result[1]
            print(f"Trade executed successfully. ID: {trade_id}")
            
            # Wait for trade to complete
            await asyncio.sleep(signal_data["duration"] + 2)  # Add 2 seconds buffer
            
            # Check trade result
            trade_result = pocket_option_client.check_win(trade_id)
            return trade_result
        else:
            print(f"Failed to execute trade: {result}")
            return None
    except Exception as e:
        print(f"Error executing trade: {str(e)}")
        return None

async def process_telegram_signal(message_text, pocket_option_client, amount=10):
    """
    Process a Telegram signal and execute a trade.
    
    Args:
        message_text: The text of the Telegram message
        pocket_option_client: Initialized PocketOption client
        amount: Trade amount
        
    Returns:
        Trade result or None if processing failed
    """
    # Parse the signal
    signal = parse_telegram_signal(message_text)
    if not signal:
        print("Failed to parse signal")
        return None
    
    # Convert to Pocket Option format
    po_format = convert_to_pocket_option_format(signal)
    
    # If timer is specified, wait until the specified time
    if signal["timer"]:
        # Parse timer
        timer_parts = signal["timer"].split(":")
        timer_hour = int(timer_parts[0])
        timer_minute = int(timer_parts[1])
        timer_second = int(timer_parts[2])
        
        # Check if the timer is in the format "00:01:00" which means "1 minute from now"
        # rather than a specific time of day
        now = datetime.now()
        if timer_hour == 0 and timer_minute <= 5:  # Assuming signals are for short timeframes (≤ 5 minutes)
            # Calculate execution time as X minutes from now
            timer_time = now + timedelta(minutes=timer_minute, seconds=timer_second)
            print(f"Interpreting timer as relative time: {timer_minute} minutes and {timer_second} seconds from now")
        else:
            # Use the original absolute time calculation
            timer_time = now.replace(hour=timer_hour, minute=timer_minute, second=timer_second, microsecond=0)
            
            # If the timer is in the past, assume it's for the next day
            if timer_time < now:
                timer_time = timer_time + timedelta(days=1)
        
        # Calculate seconds until timer
        seconds_until_timer = (timer_time - now).total_seconds()
        
        print(f"Waiting {seconds_until_timer:.2f} seconds until {timer_time.strftime('%H:%M:%S')}")
        
        # Wait until timer
        await asyncio.sleep(seconds_until_timer)
    
    # Execute the trade
    return await execute_trade(pocket_option_client, po_format, amount)
```

## Two-Message Format Handling

For the two-message format, we need to track the first message and correlate it with the second message:

```python
class SignalTracker:
    def __init__(self, match_window=60):
        self.last_pair = None
        self.last_timestamp = None
        self.match_window = match_window  # seconds
    
    def process_message(self, message_text, timestamp):
        """
        Process a message and determine if it's part of a signal.
        
        Args:
            message_text: The text of the message
            timestamp: The timestamp of the message
            
        Returns:
            Complete signal dictionary or None if not a complete signal
        """
        # Check for first message (trading pair)
        pair_match = re.search(r'Trading Pair:\s*([A-Z]{3}/[A-Z]{3})', message_text)
        if pair_match:
            self.last_pair = pair_match.group(1)
            self.last_timestamp = timestamp
            return None
        
        # Check for second message (timer, direction, expiry)
        if self.last_pair and self.last_timestamp:
            # Check if within match window
            time_diff = (timestamp - self.last_timestamp).total_seconds()
            if time_diff <= self.match_window:
                # Parse second message
                timer_match = re.search(r'SET THE TIMER TO\s*(\d{2}:\d{2}:\d{2})', message_text)
                direction_match = re.search(r'\b(HIGHER|LOWER)\b', message_text)
                expiry_match = re.search(r'Trade time:\s*(\d+)\s*MIN', message_text)
                
                if timer_match and direction_match and expiry_match:
                    # Create complete signal
                    signal = {
                        "pair": self.last_pair,
                        "direction": direction_match.group(1),
                        "timer": timer_match.group(1),
                        "expiry": int(expiry_match.group(1))
                    }
                    
                    # Reset tracking
                    self.last_pair = None
                    self.last_timestamp = None
                    
                    return signal
        
        return None
```

## Common Issues and Solutions

### 1. Timer Interpretation

**Issue**: The timer format "00:01:00" can be interpreted in two ways:
- As a specific time of day (12:01 AM)
- As a relative time (1 minute from now)

**Solution**: For signals with timers like "00:01:00", interpret them as relative times (X minutes from now) rather than absolute times. This is implemented in the code above.

### 2. Currency Pair Format

**Issue**: Telegram signals use "EUR/USD" format, but Pocket Option API expects "EURUSD".

**Solution**: Always remove the slash when converting to Pocket Option format.

### 3. OTC Markets

**Issue**: Some signals include "(OTC)" after the pair, which needs to be handled.

**Solution**: For pairs with "(OTC)" suffix, append "_otc" to the asset name for Pocket Option API:

```python
def convert_pair_format(telegram_pair):
    # Check if OTC
    is_otc = "(OTC)" in telegram_pair
    
    # Remove slash and any extra text
    pair = telegram_pair.replace("/", "").split(" ")[0]
    
    # Add _otc suffix if needed
    if is_otc:
        pair = f"{pair}_otc"
    
    return pair
```

### 4. Direction Mapping

**Issue**: Telegram uses "HIGHER"/"LOWER" but Pocket Option API expects "call"/"put".

**Solution**: Always map directions as follows:
- "HIGHER" → "call"
- "LOWER" → "put"

## Testing Your Parser

To test your parser, use these example signals:

```python
test_signals = [
    # Two-message format
    [
        "🔴Trading Pair: EUR/USD (OTC)",
        "❗️SET THE TIMER TO 00:01:00❗️\nLOWER ⬇️\nTrade time: 1 MIN"
    ],
    # Single-message format
    [
        "🔥 Trade signal: USD/JPY\nHIGHER ⬆️\nSet to: 1 MIN"
    ]
]

# Expected results after parsing and conversion:
expected_results = [
    {
        "asset": "EURUSD_otc",
        "direction": "put",
        "duration": 60
    },
    {
        "asset": "USDJPY",
        "direction": "call",
        "duration": 60
    }
]
```

## Conclusion

By following this guide, you can correctly parse Telegram signals from the BINARY TRADING CLUB channel and convert them to the format expected by the Pocket Option API. The implementation handles both single-message and two-message formats, as well as special cases like OTC markets and relative timer interpretation.

Remember to always test your parser with a variety of signal formats to ensure it handles all cases correctly.
