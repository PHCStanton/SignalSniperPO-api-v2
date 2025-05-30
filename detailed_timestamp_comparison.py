import pandas as pd
import json
from datetime import datetime, timedelta
import pytz

def detailed_timestamp_analysis():
    """Perform detailed timestamp comparison between Excel trades and signal timestamps"""
    
    # Load the converted Excel data
    with open(r'data\2025-05-29_TIMESTAMPS\export_history_converted.json', 'r', encoding='utf-8') as f:
        excel_data = json.load(f)
    
    # Load the timestamps data
    with open(r'data\2025-05-29_TIMESTAMPS\2025-05-29_timestamps.json', 'r', encoding='utf-8') as f:
        timestamps_data = json.load(f)
    
    print("="*80)
    print("DETAILED TIMESTAMP COMPARISON ANALYSIS")
    print("="*80)
    
    # Convert timestamps to datetime objects for comparison
    excel_trades = []
    for trade in excel_data:
        excel_trades.append({
            'order_id': trade['Order'],
            'asset': trade['Asset'],
            'direction': trade['Direction'],
            'open_time': datetime.strptime(trade['Open time'], '%Y-%m-%d %H:%M:%S'),
            'close_time': datetime.strptime(trade['Close time'], '%Y-%m-%d %H:%M:%S'),
            'profit': trade['Profit'],
            'amount': trade['Trade amount']
        })
    
    signal_records = []
    for signal in timestamps_data:
        signal_records.append({
            'signal_id': signal['signal_id'],
            'currency_pair': signal['currency_pair'],
            'signal_received': datetime.fromisoformat(signal['signal_received'].replace('Z', '+00:00')),
            'signal_executed': datetime.fromisoformat(signal['signal_executed'].replace('Z', '+00:00')),
            'trade_id': signal['trade_id'],
            'execution_delay_ms': signal['execution_delay_ms']
        })
    
    print(f"\nExcel Trades: {len(excel_trades)}")
    print(f"Signal Records: {len(signal_records)}")
    
    # Sort both by time
    excel_trades.sort(key=lambda x: x['open_time'])
    signal_records.sort(key=lambda x: x['signal_executed'])
    
    print("\n" + "="*80)
    print("TRADE EXECUTION TIMELINE COMPARISON")
    print("="*80)
    
    # Show timeline comparison
    print("\nSIGNAL EXECUTION TIMES:")
    for i, signal in enumerate(signal_records):
        print(f"{i+1:2d}. {signal['signal_executed'].strftime('%H:%M:%S.%f')[:-3]} - {signal['currency_pair']} (ID: {signal['trade_id']})")
    
    print("\nEXCEL TRADE OPEN TIMES:")
    for i, trade in enumerate(excel_trades):
        print(f"{i+1:2d}. {trade['open_time'].strftime('%H:%M:%S')} - {trade['asset']} ({trade['direction']}) - Profit: {trade['profit']}")
    
    # Try to match trades by currency pair and time proximity
    print("\n" + "="*80)
    print("TRADE MATCHING ANALYSIS")
    print("="*80)
    
    matches = []
    unmatched_signals = []
    unmatched_trades = []
    
    # Convert currency pairs for matching
    def normalize_currency_pair(pair):
        if 'OTC' in pair:
            return pair.replace(' OTC', '').replace('/', '')
        return pair.replace('/', '')
    
    def normalize_signal_pair(pair):
        return pair.replace('/', '')
    
    # Try to match each signal with a trade
    for signal in signal_records:
        signal_pair = normalize_signal_pair(signal['currency_pair'])
        signal_time = signal['signal_executed']
        
        best_match = None
        min_time_diff = timedelta(hours=1)  # Maximum acceptable time difference
        
        for trade in excel_trades:
            trade_pair = normalize_currency_pair(trade['asset'])
            
            # Check if currency pairs match (approximately)
            if signal_pair in trade_pair or trade_pair in signal_pair:
                # Calculate time difference (considering timezone differences)
                time_diff = abs(trade['open_time'] - signal_time.replace(tzinfo=None))
                
                if time_diff < min_time_diff:
                    min_time_diff = time_diff
                    best_match = trade
        
        if best_match:
            matches.append({
                'signal': signal,
                'trade': best_match,
                'time_diff': min_time_diff
            })
        else:
            unmatched_signals.append(signal)
    
    # Find unmatched trades
    matched_trade_ids = [match['trade']['order_id'] for match in matches]
    unmatched_trades = [trade for trade in excel_trades if trade['order_id'] not in matched_trade_ids]
    
    print(f"\nMATCHED TRADES: {len(matches)}")
    print(f"UNMATCHED SIGNALS: {len(unmatched_signals)}")
    print(f"UNMATCHED TRADES: {len(unmatched_trades)}")
    
    if matches:
        print("\nMATCHED TRADES DETAILS:")
        for i, match in enumerate(matches):
            signal = match['signal']
            trade = match['trade']
            time_diff = match['time_diff']
            
            print(f"\n{i+1}. MATCH:")
            print(f"   Signal: {signal['currency_pair']} at {signal['signal_executed'].strftime('%H:%M:%S.%f')[:-3]}")
            print(f"   Trade:  {trade['asset']} at {trade['open_time'].strftime('%H:%M:%S')}")
            print(f"   Time Difference: {time_diff}")
            print(f"   Trade Result: {trade['direction']} - Profit: {trade['profit']}")
            print(f"   Signal ID: {signal['signal_id']}")
            print(f"   Trade ID: {trade['order_id']}")
    
    if unmatched_signals:
        print(f"\nUNMATCHED SIGNALS ({len(unmatched_signals)}):")
        for signal in unmatched_signals:
            print(f"   {signal['currency_pair']} at {signal['signal_executed'].strftime('%H:%M:%S.%f')[:-3]} (ID: {signal['signal_id']})")
    
    if unmatched_trades:
        print(f"\nUNMATCHED TRADES ({len(unmatched_trades)}):")
        for trade in unmatched_trades:
            print(f"   {trade['asset']} at {trade['open_time'].strftime('%H:%M:%S')} - {trade['direction']} - Profit: {trade['profit']}")
    
    # Summary statistics
    print("\n" + "="*80)
    print("SUMMARY STATISTICS")
    print("="*80)
    
    total_profit = sum(trade['profit'] for trade in excel_trades)
    winning_trades = len([trade for trade in excel_trades if trade['profit'] > 0])
    losing_trades = len([trade for trade in excel_trades if trade['profit'] < 0])
    
    print(f"Total Trades: {len(excel_trades)}")
    print(f"Winning Trades: {winning_trades}")
    print(f"Losing Trades: {losing_trades}")
    print(f"Win Rate: {(winning_trades/len(excel_trades)*100):.1f}%")
    print(f"Total Profit: ${total_profit:.2f}")
    
    if signal_records:
        avg_execution_delay = sum(signal['execution_delay_ms'] for signal in signal_records) / len(signal_records)
        print(f"Average Execution Delay: {avg_execution_delay:.1f}ms")
    
    return matches, unmatched_signals, unmatched_trades

if __name__ == "__main__":
    matches, unmatched_signals, unmatched_trades = detailed_timestamp_analysis()
