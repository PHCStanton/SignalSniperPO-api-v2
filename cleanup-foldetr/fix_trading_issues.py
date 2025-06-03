#!/usr/bin/env python3
"""
Fix for trading issues identified in session analysis
"""

def fix_balance_validation():
    """
    Fix for the balance comparison error in validate_signal method
    """
    fix_code = '''
    # FIXED: Handle tuple/complex balance data properly
    try:
        # Validate balance data to ensure numeric comparison
        validated_balance = 0.0
        
        if balance is None:
            validated_balance = 0.0
        elif isinstance(balance, (int, float)):
            validated_balance = float(balance)
        elif isinstance(balance, (tuple, list)):
            # Extract first numeric value from tuple/list
            for item in balance:
                try:
                    validated_balance = float(item)
                    break
                except (ValueError, TypeError):
                    continue
        elif isinstance(balance, str):
            try:
                validated_balance = float(balance.replace(',', '').replace('$', ''))
            except ValueError:
                validated_balance = 0.0
        else:
            # Handle dict or other complex types
            if hasattr(balance, 'get'):
                validated_balance = float(balance.get('balance', 0))
            else:
                validated_balance = 0.0
        
        if validated_balance < trade_amount:
            return False, f"Insufficient balance: {validated_balance} < {trade_amount}"
            
    except Exception as e:
        logger.error(f"Balance validation error: {str(e)} - Balance type: {type(balance)} - Value: {balance}")
        return False, f"Error validating balance: {str(e)}"
    '''
    return fix_code

def fix_trade_result_checking():
    """
    Fix for the check_win result parsing
    """
    fix_code = '''
    # FIXED: Handle tuple return from check_win properly
    try:
        # Check trade result
        result = self.pocket_option_client.check_win(trade_id)
        
        # Handle tuple return (profit, status)
        if isinstance(result, tuple) and len(result) >= 2:
            profit, status = result[0], result[1]
            
            if profit is not None:
                if profit > 0:
                    # Winning trade
                    logger.info(f"✅ WINNING TRADE: {trade_id} - Profit: ${profit}")
                    trade["result"] = "win"
                    trade["profit"] = profit
                    self.stats["winning_trades"] += 1
                    self.stats["total_profit"] += profit
                elif profit < 0:
                    # Losing trade
                    logger.info(f"❌ LOSING TRADE: {trade_id} - Loss: ${profit}")
                    trade["result"] = "loss"
                    trade["profit"] = profit
                    self.stats["losing_trades"] += 1
                    self.stats["total_profit"] += profit
                else:
                    # Draw
                    logger.info(f"⚖️ DRAW TRADE: {trade_id} - No profit/loss")
                    trade["result"] = "draw"
                    trade["profit"] = 0.0
        elif isinstance(result, (int, float)):
            # Handle single numeric return
            profit = result
            # ... rest of logic
        else:
            logger.warning(f"⚠️ Unexpected result format: {type(result)} - {result}")
            trade["result"] = "unknown"
            
    except Exception as e:
        logger.error(f"Error checking trade result: {str(e)}")
        trade["result"] = "error"
        trade["error_message"] = str(e)
    '''
    return fix_code

def main():
    print("🔧 TRADING ISSUES ANALYSIS & FIXES")
    print("=" * 50)
    
    print("\n1. BALANCE VALIDATION FIX:")
    print(fix_balance_validation())
    
    print("\n2. TRADE RESULT CHECKING FIX:")
    print(fix_trade_result_checking())
    
    print("\n📊 RECOMMENDATIONS:")
    print("- Apply these fixes to self_bot.py")
    print("- Test with demo mode first")
    print("- Add more robust error handling")
    print("- Implement balance data logging for debugging")

if __name__ == "__main__":
    main()
