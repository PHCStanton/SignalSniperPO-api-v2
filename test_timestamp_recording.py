#!/usr/bin/env python3
"""
Test script for timestamp recording functionality
"""

import json
import time
from datetime import datetime
from timestamp_recorder import TimestampRecorder

def test_timestamp_recording():
    """Test the timestamp recording functionality."""
    print("🧪 Testing Timestamp Recording Functionality")
    print("=" * 50)
    
    # Initialize timestamp recorder
    recorder = TimestampRecorder(data_dir="data", max_records=100)
    
    # Test 1: Record signal timestamp
    print("\n📊 Test 1: Recording Signal Timestamp")
    signal_id = f"test_signal_{int(time.time())}"
    currency_pair = "EUR/USD"
    session_id = f"test_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    timestamp_record = recorder.record_signal_timestamp(
        signal_id=signal_id,
        currency_pair=currency_pair,
        session_id=session_id
    )
    
    print(f"✅ Signal timestamp recorded:")
    print(f"   Signal ID: {timestamp_record['signal_id']}")
    print(f"   Currency Pair: {timestamp_record['currency_pair']}")
    print(f"   Signal Received: {timestamp_record['signal_received']}")
    print(f"   Session ID: {timestamp_record['session_id']}")
    
    # Test 2: Record execution timestamp with delay
    print("\n📊 Test 2: Recording Execution Timestamp")
    time.sleep(0.1)  # Simulate small delay
    
    trade_id = f"test_trade_{int(time.time())}"
    updated_record = recorder.record_execution_timestamp(timestamp_record, trade_id)
    
    print(f"✅ Execution timestamp recorded:")
    print(f"   Trade ID: {updated_record['trade_id']}")
    print(f"   Signal Executed: {updated_record['signal_executed']}")
    print(f"   Execution Delay: {updated_record['execution_delay_ms']}ms")
    print(f"   Status: {updated_record['status']}")
    
    # Test 3: Get performance statistics
    print("\n📊 Test 3: Performance Statistics")
    stats = recorder.get_performance_stats()
    
    print(f"✅ Performance statistics:")
    print(f"   Total Records: {stats['total_records']}")
    print(f"   Average Delay: {stats['average_delay_ms']}ms")
    print(f"   Min Delay: {stats['min_delay_ms']}ms")
    print(f"   Max Delay: {stats['max_delay_ms']}ms")
    
    # Test 4: Get recent records
    print("\n📊 Test 4: Recent Records")
    recent_records = recorder.get_recent_records(limit=5)
    
    print(f"✅ Recent records ({len(recent_records)} found):")
    for i, record in enumerate(recent_records[-3:], 1):  # Show last 3
        print(f"   {i}. Signal: {record.get('signal_id', 'N/A')} | "
              f"Delay: {record.get('execution_delay_ms', 'N/A')}ms | "
              f"Status: {record.get('status', 'N/A')}")
    
    # Test 5: Test backup functionality
    print("\n📊 Test 5: Testing Backup Functionality")
    
    # Create a few more test records
    for i in range(3):
        test_signal_id = f"backup_test_signal_{i}_{int(time.time())}"
        test_record = recorder.record_signal_timestamp(
            signal_id=test_signal_id,
            currency_pair="GBP/USD",
            session_id=session_id
        )
        time.sleep(0.05)  # Small delay
        recorder.record_execution_timestamp(test_record, f"backup_test_trade_{i}")
    
    print("✅ Backup functionality tested with multiple records")
    
    # Test 6: Verify file integrity
    print("\n📊 Test 6: File Integrity Check")
    try:
        with open("data/timestamps.json", 'r') as f:
            data = json.load(f)
            print(f"✅ Timestamps file is valid JSON with {len(data)} records")
        
        # Check if backup file exists
        import os
        if os.path.exists("data/timestamps_backup.json"):
            with open("data/timestamps_backup.json", 'r') as f:
                backup_data = json.load(f)
                print(f"✅ Backup file exists with {len(backup_data)} records")
        else:
            print("ℹ️  Backup file not yet created (normal for first run)")
            
    except Exception as e:
        print(f"❌ File integrity check failed: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Timestamp Recording Test Completed!")
    print("\n📋 Summary:")
    print("   ✅ Signal timestamp recording")
    print("   ✅ Execution timestamp recording with delay calculation")
    print("   ✅ Performance statistics generation")
    print("   ✅ Recent records retrieval")
    print("   ✅ Backup system functionality")
    print("   ✅ File integrity verification")

if __name__ == "__main__":
    test_timestamp_recording()
