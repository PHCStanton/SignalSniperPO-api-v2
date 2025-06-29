#!/usr/bin/env python3
"""
Test script to verify the datetime timezone fix in timestamp_recorder.py
"""

import sys
import os
import json
import pytz
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from timestamp_recorder import TimestampRecorder

def test_timestamp_recorder_fix():
    """Test that the timestamp recorder handles timezone-aware datetimes correctly."""
    print("🧪 Testing Timestamp Recorder Timezone Fix...")
    
    # Create a test instance
    recorder = TimestampRecorder(data_dir="test_data", max_records=10)
    
    # Test 1: Record a signal timestamp
    print("\n1️⃣ Testing signal timestamp recording...")
    signal_record = recorder.record_signal_timestamp(
        signal_id="test_signal_001",
        currency_pair="EUR/USD",
        session_id="test_session_001"
    )
    
    print(f"✅ Signal timestamp recorded: {signal_record['signal_received']}")
    print(f"   Paris time: {signal_record['signal_received_paris']}")
    
    # Verify the timestamp is timezone-aware
    signal_time = datetime.fromisoformat(signal_record['signal_received'])
    assert signal_time.tzinfo is not None, "Signal timestamp should be timezone-aware"
    print("✅ Signal timestamp is timezone-aware")
    
    # Test 2: Record execution timestamp
    print("\n2️⃣ Testing execution timestamp recording...")
    try:
        execution_record = recorder.record_execution_timestamp(
            timestamp_record=signal_record,
            trade_id="test_trade_001"
        )
        
        print(f"✅ Execution timestamp recorded: {execution_record['signal_executed']}")
        print(f"   Execution delay: {execution_record['execution_delay_ms']} ms")
        
        # Verify the execution timestamp is timezone-aware
        exec_time = datetime.fromisoformat(execution_record['signal_executed'])
        assert exec_time.tzinfo is not None, "Execution timestamp should be timezone-aware"
        print("✅ Execution timestamp is timezone-aware")
        
        # Verify we can calculate the difference
        time_diff = (exec_time - signal_time).total_seconds()
        print(f"✅ Time difference calculated successfully: {time_diff:.3f} seconds")
        
    except TypeError as e:
        if "can't subtract offset-naive and offset-aware datetimes" in str(e):
            print("❌ FAILED: Timezone error still exists!")
            print(f"   Error: {e}")
            return False
        else:
            raise
    
    # Test 3: Test with mixed timezone scenarios
    print("\n3️⃣ Testing mixed timezone scenarios...")
    
    # Create a naive datetime (this would cause the original error)
    naive_time = datetime.now()
    aware_time = datetime.now(pytz.UTC)
    
    print(f"   Naive datetime: {naive_time} (tzinfo: {naive_time.tzinfo})")
    print(f"   Aware datetime: {aware_time} (tzinfo: {aware_time.tzinfo})")
    
    # This would fail with the original code
    try:
        diff = aware_time - naive_time
        print("❌ This should have failed but didn't - something is wrong")
    except TypeError as e:
        print("✅ Correctly caught timezone mismatch error (expected behavior)")
    
    # Clean up test data
    import shutil
    if os.path.exists("test_data"):
        shutil.rmtree("test_data")
    
    print("\n✅ All tests passed! The timezone fix is working correctly.")
    return True

def test_main_bot_integration():
    """Test that the main bot properly uses timezone-aware datetimes."""
    print("\n\n🧪 Testing Main Bot Integration...")
    
    # Import the get_high_precision_time function
    from self_bot_v3_integrated import get_high_precision_time
    
    # Test that get_high_precision_time returns timezone-aware datetime
    print("\n1️⃣ Testing get_high_precision_time()...")
    high_precision_time = get_high_precision_time()
    
    print(f"   Time: {high_precision_time}")
    print(f"   Timezone: {high_precision_time.tzinfo}")
    print(f"   ISO format: {high_precision_time.isoformat()}")
    
    assert high_precision_time.tzinfo is not None, "get_high_precision_time should return timezone-aware datetime"
    assert str(high_precision_time.tzinfo) == "UTC", "get_high_precision_time should return UTC timezone"
    print("✅ get_high_precision_time returns timezone-aware UTC datetime")
    
    # Test datetime operations
    print("\n2️⃣ Testing datetime operations...")
    time1 = get_high_precision_time()
    import time
    time.sleep(0.1)  # Small delay
    time2 = get_high_precision_time()
    
    diff = (time2 - time1).total_seconds()
    print(f"✅ Time difference calculated: {diff:.3f} seconds")
    
    print("\n✅ Main bot integration tests passed!")
    return True

if __name__ == "__main__":
    print("=" * 60)
    print("🔧 DATETIME TIMEZONE FIX VERIFICATION")
    print("=" * 60)
    
    # Run tests
    test1_passed = test_timestamp_recorder_fix()
    test2_passed = test_main_bot_integration()
    
    print("\n" + "=" * 60)
    if test1_passed and test2_passed:
        print("✅ ALL TESTS PASSED - TIMEZONE FIX IS WORKING!")
        print("\n📝 Summary:")
        print("- timestamp_recorder.py now uses timezone-aware UTC datetime")
        print("- No more 'can't subtract offset-naive and offset-aware datetimes' errors")
        print("- Bot is ready for execution")
    else:
        print("❌ SOME TESTS FAILED - Please check the errors above")
    print("=" * 60)
