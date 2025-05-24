# Trading Strategy Implementation for SelfBot v1.0

This document outlines a practical trading strategy implementation for SelfBot v1.0, based on the signal parsing examples from the BINARY TRADING CLUB Telegram channel and the 1-minute EUR/USD basic strategy. This implementation will be used to test the bot in real-world scenarios.

## Signal Parsing Strategy

Based on the analysis of the Telegram signals from BINARY TRADING CLUB, we've identified the following pattern:

1. **First Message Format**: `Trading Pair: XXX/XXX (OTC)`
2. **Second Message Format**: 
   ```
   SET THE TIMER TO XX:XX:XX
   Currency pair XXX/XXX
   HIGHER/LOWER
   Trade time: X MIN
   ```

The bot successfully parses these signals using the regex patterns defined in `telegram_config.json`:

```json
{
    "first_message_regex": "Trading Pair: (\\w+/\\w+)(?:\\s*\\(OTC\\))?",
    "second_message_regex": {
        "timer": "SET THE TIMER TO (\\d{2}:\\d{2}:\\d{2})",
        "pair": "Currency pair (\\w+/\\w+)",
        "direction": "(HIGHER|LOWER)",
        "expiry": "Trade time: (\\d+) MIN"
    },
    "pair_match_window": 60
}
```

## Trading Strategy: 1-Minute EUR/USD Basic

For our initial real-world testing, we'll implement a simplified version of the 1-minute EUR/USD basic strategy. This strategy will be used to validate signals from the Telegram channel and execute trades on Pocket Option.

### Strategy Components

1. **Asset Focus**: Primarily EUR/USD, but will accept any asset provided in the signal
2. **Timeframe**: 1-minute expiry (as specified in the signals)
3. **Direction**: Follow the signal direction (HIGHER = call, LOWER = put)
4. **Trade Amount**: $1 for initial real trade validation (configurable in `bot_config.json`)
5. **Trading Hours**: 8:00 AM to 12:00 PM SAST (high liquidity period)

### Risk Management Rules

1. **Position Sizing**: Fixed $1 per trade for initial testing
2. **Maximum Daily Trades**: 20 trades per day (configurable in `bot_config.json`)
3. **Maximum Daily Loss**: $100 (configurable in `bot_config.json`)
4. **Consecutive Losses**: Pause trading after 3 consecutive losses
5. **Minimum Time Before Timer**: Skip trades if signal arrives less than 5 seconds before the timer

### Implementation in SelfBot v1.0

The strategy is already implemented in the `self_bot.py` file:

1. **Signal Validation** (`validate_signal` method):
   - Checks if we have sufficient balance
   - Verifies we haven't reached maximum daily trades
   - Ensures we haven't reached maximum daily loss
   - Validates that the timer is in the future and not too close

2. **Trade Execution** (`execute_trade` method):
   - Converts the signal direction to Pocket Option format (HIGHER → call, LOWER → put)
   - Sets the expiry time in seconds
   - Uses the configured trade amount
   - Executes the trade at the specified time

3. **Result Tracking** (`check_trade_result` method):
   - Waits for the trade to complete
   - Checks the result (win/loss)
   - Updates statistics and database

## Real-World Testing Plan

To finalize SelfBot v1.0 operations, we'll follow this testing plan:

1. **Validate WebSocket SSID**:
   - Test the current SSID in `pocket_option_config.json` using `test_ssid_direct.py`
   - If expired, obtain a fresh SSID following the instructions in `get_fresh_ssid_guide.md`

2. **Test Mode Validation**:
   - Run `self_bot.py` with `--test-mode` flag to simulate trades
   - Verify signal parsing, trade scheduling, and database logging
   - Check trade results in the database using `query_database.py`

3. **Real Trade Execution**:
   - Update `bot_config.json` to set `"test_mode": false`
   - Set `"trade_amount": 1` for minimal risk
   - Execute one real trade to validate the entire flow
   - Verify the trade result in the database

4. **EC2 Deployment**:
   - Deploy to EC2 using `deploy_selfbot.sh` or `deploy_selfbot.ps1`
   - Set up the systemd service for automatic startup
   - Monitor logs for stability

## Signal Parsing Examples

Here are examples of how the bot parses trading signals:

### Example 1:
```
🔴Trading Pair: AUD/USD (OTC)
❗️SET THE TIMER TO 00:01:00❗️
LOWER ⬇️
Trade time: 1 MIN
```

Parsed result:
```
Pair      : AUD/USD
Direction : lower
Timer     : 00:01:00
Duration  : 1 min
```

### Example 2:
```
🔥 Trade signal: USD/JPY
HIGHER ⬆️
Set to: 1 MIN
```

Parsed result:
```
Pair      : USD/JPY
Direction : higher
Duration  : 1 min
```

## Future Strategy Enhancements (v1.5+)

For future versions, we can enhance the trading strategy with:

1. **Technical Indicators**:
   - SuperTrend (ATR Period: 7, Multiplier: 2)
   - Bollinger Bands (Deviation: 2, Period: 10)
   - EMA1 (Period: 20) and EMA2 (Period: 5)
   - Donchian Channel (Period: 10)
   - CCI (+100, -100)
   - RSI (70 high, 30 low)

2. **Advanced Risk Management**:
   - Dynamic position sizing based on account balance
   - Martingale/anti-martingale strategies
   - Time-based filters (avoid trading during news events)

3. **Performance Analysis**:
   - Track win rate by asset, time of day, and signal source
   - Generate daily/weekly reports
   - Optimize strategy parameters based on historical performance

## Conclusion

This trading strategy implementation provides a practical approach for finalizing SelfBot v1.0 operations. By focusing on signal parsing accuracy, trade execution reliability, and basic risk management, we can validate the bot's functionality in real-world scenarios while minimizing risk.

The strategy is intentionally simple for v1.0, focusing on core functionality rather than complex trading rules. This allows us to validate the entire signal-to-trade flow with minimal risk before adding more sophisticated features in future versions.
