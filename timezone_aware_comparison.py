import pandas as pd
import json
from datetime import datetime, timedelta
import pytz

def timezone_aware_analysis():
    """Perform timezone-aware timestamp comparison"""
    
    # Load the converted Excel data
    with open(r'data\2025-05-29_TIMESTAMPS\export_history_converted.json', 'r', encoding='utf-8') as f:
        excel_data = json.load(f)
    
    # Load the timestamps data
    with open(r'data\2025-05-29_TIMESTAMPS\2025-05-29_timestamps.json', 'r', encoding='utf-8') as f:
        timestamps_data = json.load(f)
    
    print("="*80)
    print("TIMEZONE-AWARE TIMESTAMP COMPARISON ANALYSIS")
    print("="*80)
    
    # Convert timestamps to datetime objects
    excel_trades = []
    for trade in excel_data:
        # Assume Excel times are in local timezone (possibly UTC+2 or similar)
        open_time = datetime.strptime(trade['Open time'], '%Y-%m-%d %H:%M:%S')
        excel_trades.append({
            'order_id': trade['Order'],
            'asset': trade['Asset'],
            'direction': trade['Direction'],
            'open_time': open_time,
            'close_time': datetime.strptime(trade['Close time'], '%Y-%m-%d %H:%M:%S'),
            'profit': trade['Profit'],
            'amount': trade['Trade amount']
        })
    
    signal_records = []
    for signal in timestamps_data:
        signal_time = datetime.fromisoformat(signal['signal_executed'].replace('Z', '+00:00'))
        signal_records.append({
            'signal_id': signal['signal_id'],
            'currency_pair': signal['currency_pair'],
            'signal_received': datetime.fromisoformat(signal['signal_received'].replace('Z', '+00:00')),
            'signal_executed': signal_time,
            'trade_id': signal['trade_id'],
            'execution_delay_ms': signal['execution_delay_ms']
        })
    
    print(f"\nExcel Trades: {len(excel_trades)}")
    print(f"Signal Records: {len(signal_records)}")
    
    # Analyze time patterns to detect timezone offset
    print("\n" + "="*80)
    print("TIMEZONE ANALYSIS")
    print("="*80)
    
    # Look for potential matches by currency pair first
    currency_matches = {}
    
    def normalize_pair(pair):
        return pair.replace('/', '').replace(' OTC', '').upper()
    
    # Group by currency pairs
    signal_pairs = {}
    for signal in signal_records:
        pair = normalize_pair(signal['currency_pair'])
        if pair not in signal_pairs:
            signal_pairs[pair] = []
        signal_pairs[pair].append(signal)
    
    trade_pairs = {}
    for trade in excel_trades:
        pair = normalize_pair(trade['asset'])
        if pair not in trade_pairs:
            trade_pairs[pair] = []
        trade_pairs[pair].append(trade)
    
    print("Currency pairs in signals:", list(signal_pairs.keys()))
    print("Currency pairs in trades:", list(trade_pairs.keys()))
    
    # Find common currency pairs
    common_pairs = set(signal_pairs.keys()) & set(trade_pairs.keys())
    print(f"Common currency pairs: {list(common_pairs)}")
    
    # Try different timezone offsets to find the best match
    print("\n" + "="*80)
    print("TESTING TIMEZONE OFFSETS")
    print("="*80)
    
    best_matches = []
    best_offset = None
    max_matches = 0
    
    # Test offsets from -12 to +12 hours
    for offset_hours in range(-12, 13):
        matches = 0
        offset_matches = []
        
        for pair in common_pairs:
            signals = signal_pairs[pair]
            trades = trade_pairs[pair]
            
            for signal in signals:
                # Convert signal time to potential local time
                signal_local = signal['signal_executed'].replace(tzinfo=None) + timedelta(hours=offset_hours)
                
                for trade in trades:
                    time_diff = abs((trade['open_time'] - signal_local).total_seconds())
                    
                    # Allow up to 5 minutes difference
                    if time_diff <= 300:  # 5 minutes
                        matches += 1
                        offset_matches.append({
                            'signal': signal,
                            'trade': trade,
                            'time_diff': time_diff,
                            'signal_local': signal_local
                        })
                        break
        
        if matches > max_matches:
            max_matches = matches
            best_offset = offset_hours
            best_matches = offset_matches
        
        if matches > 0:
            print(f"Offset {offset_hours:+3d}h: {matches} matches")
    
    print(f"\nBest timezone offset: {best_offset:+d} hours ({max_matches} matches)")
    
    if best_matches:
        print("\n" + "="*80)
        print(f"MATCHED TRADES WITH {best_offset:+d}H OFFSET")
        print("="*80)
        
        for i, match in enumerate(best_matches):
            signal = match['signal']
            trade = match['trade']
            signal_local = match['signal_local']
            time_diff = match['time_diff']
            
            print(f"\n{i+1}. MATCH:")
            print(f"   Signal: {signal['currency_pair']} at {signal['signal_executed'].strftime('%H:%M:%S')} UTC")
            print(f"   Local:  {signal_local.strftime('%H:%M:%S')} (UTC{best_offset:+d})")
            print(f"   Trade:  {trade['asset']} at {trade['open_time'].strftime('%H:%M:%S')}")
            print(f"   Time Difference: {time_diff:.1f} seconds")
            print(f"   Trade Result: {trade['direction']} - Profit: {trade['profit']}")
            print(f"   Signal ID: {signal['signal_id']}")
    
    # Create final summary with timezone correction
    print("\n" + "="*80)
    print("FINAL ANALYSIS SUMMARY")
    print("="*80)
    
    if best_offset is not None:
        print(f"Detected timezone offset: UTC{best_offset:+d}")
        print(f"Successfully matched: {len(best_matches)} out of {len(signal_records)} signals")
        
        matched_signal_ids = [match['signal']['signal_id'] for match in best_matches]
        unmatched_signals = [s for s in signal_records if s['signal_id'] not in matched_signal_ids]
        
        matched_trade_ids = [match['trade']['order_id'] for match in best_matches]
        unmatched_trades = [t for t in excel_trades if t['order_id'] not in matched_trade_ids]
        
        print(f"Unmatched signals: {len(unmatched_signals)}")
        print(f"Unmatched trades: {len(unmatched_trades)}")
        
        if unmatched_signals:
            print("\nUnmatched signals:")
            for signal in unmatched_signals:
                local_time = signal['signal_executed'].replace(tzinfo=None) + timedelta(hours=best_offset)
                print(f"   {signal['currency_pair']} at {local_time.strftime('%H:%M:%S')} local")
        
        if unmatched_trades:
            print("\nUnmatched trades:")
            for trade in unmatched_trades:
                print(f"   {trade['asset']} at {trade['open_time'].strftime('%H:%M:%S')} - Profit: {trade['profit']}")
    
    # Trading performance summary
    total_profit = sum(trade['profit'] for trade in excel_trades)
    winning_trades = len([trade for trade in excel_trades if trade['profit'] > 0])
    
    print(f"\nTrading Performance:")
    print(f"Total Trades: {len(excel_trades)}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Win Rate: {(winning_trades/len(excel_trades)*100):.1f}%")
    print(f"Total Profit: ${total_profit:.2f}")
    
    avg_execution_delay = sum(signal['execution_delay_ms'] for signal in signal_records) / len(signal_records)
    print(f"Average Execution Delay: {avg_execution_delay:.1f}ms")
    
    return best_matches, best_offset

if __name__ == "__main__":
    matches, offset = timezone_aware_analysis()
