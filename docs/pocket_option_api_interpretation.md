# Pocket Option API Reference Guide

This document provides a reference for the parsing format and parameters needed to communicate with the Pocket Option API through the PocketOptionAPI-v2 library.

## Key Parameters

### Authentication

- **SSID**: The session ID used for authentication with the Pocket Option WebSocket API
  - Format: String
  - Example: `"a1b2c3d4e5f6g7h8i9j0"`

### Account Management

- **Balance Type**: Specifies whether to use practice or real account
  - Values: `"PRACTICE"` or `"REAL"`
  - Example: `account.change_balance("REAL")`

### Trade Execution

- **asset**: The currency pair to trade
  - Format: String without slash
  - Examples: 
    - `"EURUSD"` (standard)
    - `"NZDUSD_otc"` (OTC market)
    - `"GOLD"`
    - `"CRYPTO_BTC"`

- **amount**: The trade amount
  - Format: Integer or Float
  - Example: `10` or `10.5`

- **dir**: The trade direction
  - Values: 
    - `"call"` for BUY/HIGHER
    - `"put"` for SELL/LOWER
  - Example: `"call"`

- **duration**: Trade expiry time in seconds
  - Format: Integer
  - Common values: `30`, `60`, `120`, `300`
  - Example: `60` (for 1 minute expiry)

### Trade Result

- **trade_id**: The ID of the executed trade
  - Format: String
  - Example: `"12345678"`

- **win**: Whether the trade was a win or loss
  - Format: Boolean
  - Example: `true` or `false`

- **profit**: The profit or loss from the trade
  - Format: Float
  - Example: `8.0` (profit) or `-10.0` (loss)

## Mapping from Telegram Signals to API Format

| Telegram Signal | Pocket Option API |
|-----------------|-------------------|
| EUR/USD         | EURUSD            |
| AUD/CAD         | AUDCAD            |
| HIGHER          | call              |
| LOWER           | put               |
| 1 MIN           | 60 (seconds)      |
| 5 MIN           | 300 (seconds)     |

## Example Code

### Basic Connection and Authentication

```python
from pocketoptionapi.stable_api import PocketOption

# Initialize with SSID
ssid = "your_ssid_here"
is_demo = False  # Set to True for practice account
api = PocketOption(ssid, is_demo)

# Connect to the API
if api.connect():
    print("Successfully connected to Pocket Option API")
    balance = api.get_balance()
    print(f"Account balance: {balance}")
else:
    print("Failed to connect to Pocket Option API")
```

### Executing a Trade

```python
# Execute a trade
if api.connect():
    # Optional: Switch between practice and real account
    # api.change_balance("REAL")  # or "PRACTICE"
    
    asset = "EURUSD"
    amount = 10
    direction = "call"  # "call" for BUY/HIGHER, "put" for SELL/LOWER
    expiry = 60  # Duration in seconds (1 minute)
    
    result = api.buy(
        amount=amount,
        active=asset,
        action=direction,
        expirations=expiry
    )
    
    if result and result[0]:
        trade_id = result[1]
        print(f"Trade executed successfully. ID: {trade_id}")
        
        # Wait for trade to complete
        import time
        time.sleep(expiry + 2)  # Add 2 seconds buffer
        
        # Check trade result
        trade_result = api.check_win(trade_id)
        if trade_result:
            win = trade_result.get("win", False)
            profit = trade_result.get("profit", 0.0)
            print(f"Trade result: {'WIN' if win else 'LOSS'} (Profit: {profit})")
        else:
            print("Failed to get trade result")
    else:
        print(f"Failed to execute trade: {result}")
```

### Handling Multiple Currency Pairs

```python
# Function to convert Telegram format to Pocket Option format
def convert_pair_format(telegram_pair):
    # Remove slash
    return telegram_pair.replace("/", "")

# Example usage
telegram_pairs = ["EUR/USD", "AUD/CAD", "GBP/JPY"]
pocket_option_pairs = [convert_pair_format(pair) for pair in telegram_pairs]
print(pocket_option_pairs)  # ['EURUSD', 'AUDCAD', 'GBPJPY']
```

### Converting Expiry Time

```python
# Function to convert expiry time from minutes to seconds
def convert_expiry_time(minutes):
    return minutes * 60

# Example usage
telegram_expiry = 1  # 1 minute
pocket_option_expiry = convert_expiry_time(telegram_expiry)
print(pocket_option_expiry)  # 60 seconds
```

### Converting Direction

```python
# Function to convert direction from Telegram format to Pocket Option format
def convert_direction(telegram_direction):
    if telegram_direction == "HIGHER":
        return "call"
    elif telegram_direction == "LOWER":
        return "put"
    else:
        raise ValueError(f"Unknown direction: {telegram_direction}")

# Example usage
telegram_directions = ["HIGHER", "LOWER"]
pocket_option_directions = [convert_direction(dir) for dir in telegram_directions]
print(pocket_option_directions)  # ['call', 'put']
```

## Common Issues and Solutions

1. **Balance Not Fetched (Returns None)**
   - Issue: SSID may be expired or invalid
   - Solution: Refresh the SSID using the extract_pocket_option_ssid.py script

2. **Currency Pair Not Found**
   - Issue: The currency pair format may be incorrect
   - Solution: Ensure the pair is formatted without slashes and check if it's available on Pocket Option

3. **Trade Execution Fails**
   - Issue: Insufficient balance or market closed
   - Solution: Check account balance and verify market hours

4. **WebSocket Connection Drops**
   - Issue: Network issues or server-side disconnection
   - Solution: Implement reconnection logic with exponential backoff

## Additional Resources

- Official PocketOption API Documentation: https://lu-yi-hsun.github.io/pocketoptionapi/
- GitHub Repository: https://github.com/lu-yi-hsun/pocketoptionapi
