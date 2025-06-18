#!/usr/bin/env python3
"""
test_timing_fixes.py - Test Script for Timing Discrepancy Fixes

This script tests the implemented timing fixes to ensure UTC timestamps
and timezone-aware logging are working correctly.
"""

import os
import sys
import json
import time
import pytz
from datetime import datetime
from typing import Dict, List

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import the fixed functions
from self_bot_v3_integrated import get_high_precision_time, log_timing_event
from timestamp_recorder import TimestampRecorder

def test_utc_timestamp_consistency():
    """Test that UTC timestamps are consistent and properly formatted."""
    print("🕐 Testing UTC Timestamp Consistency...")
    
    results = []
    for i in range(5):
        timestamp = get_high_precision_time()
        results.append({
            "iteration": i + 1,
            "timestamp": timestamp.isoformat(),
            "timezone": str(timestamp.tzinfo),
            "is_utc": timestamp.tzinfo == pytz.UTC,
            "nanoseconds": time.time_ns()
        })
        time.sleep(0.1)
    
    # Check consistency
    all_utc = all(result["is_utc"] for result in results)
    
    print(f"✅ All timestamps are UTC: {all_utc}")
    for result in results:
        print(f"  {result['iteration']}: {result['timestamp']} (UTC: {result['is_utc']})")
    
    return all_utc, results

def test_timezone_aware_logging():
    """Test timezone-aware logging functionality."""
    print("\n🌍 Testing Timezone-Aware Logging...")
    
    # Test the log_timing_event function
    test_timestamp = get_high_precision_time()
    logged_timestamp = log_timing_event("TEST_EVENT", test_timestamp)
    
    # Verify the logged timestamp is the same
    timestamp_match = logged_timestamp == test_timestamp
    
    print(f"✅ Timezone-aware logging working: {timestamp_match}")
    print(f"  Original: {test_timestamp.isoformat()}")
    print(f"  Logged: {logged_timestamp.isoformat()}")
    
    return timestamp_match

def test_timestamp_recorder_fixes():
    """Test the updated TimestampRecorder with UTC timestamps."""
    print("\n📊 Testing TimestampRecorder UTC Fixes...")
    
    # Create a test recorder
    recorder = TimestampRecorder(data_dir="test_data", max_records=10)
    
    # Record a test signal timestamp
    test_record = recorder.record_signal_timestamp(
        signal_id="test_signal_001",
        currency_pair="EUR/USD",
        session_id="test_session"
    )
    
    # Check if the record contains both UTC and Paris timestamps
    has_utc = "signal_received" in test_record
    has_paris = "signal_received_paris" in test_record
    has_nanoseconds = "nanoseconds" in test_record
    
    print(f"✅ UTC timestamp recorded: {has_utc}")
    print(f"✅ Paris timestamp recorded: {has_paris}")
    print(f"✅ Nanosecond precision: {has_nanoseconds}")
    
    if has_utc and has_paris:
        utc_time = datetime.fromisoformat(test_record["signal_received"])
        paris_time = datetime.fromisoformat(test_record["signal_received_paris"])
        
        # Check timezone offset (should be 2 hours for Paris in summer)
        offset_hours = (paris_time - utc_time).total_seconds() / 3600
        expected_offset = 2.0  # UTC+2 for Paris in summer
        
        print(f"  UTC: {test_record['signal_received']}")
        print(f"  Paris: {test_record['signal_received_paris']}")
        print(f"  Offset: {offset_hours} hours (expected: {expected_offset})")
        print(f"  Nanoseconds: {test_record['nanoseconds']}")
        
        offset_correct = abs(offset_hours - expected_offset) < 0.1
        print(f"✅ Timezone offset correct: {offset_correct}")
    
    # Clean up test data
    try:
        import shutil
        if os.path.exists("test_data"):
            shutil.rmtree("test_data")
    except:
        pass
    
    return has_utc and has_paris and has_nanoseconds

def test_system_timezone_detection():
    """Test system timezone detection and reporting."""
    print("\n🖥️ Testing System Timezone Detection...")
    
    # Get system timezone info
    local_time = datetime.now()
    utc_time = datetime.utcnow()
    utc_offset = (local_time - utc_time).total_seconds() / 3600
    
    # Get timezone from environment
    env_tz = os.environ.get('TZ', 'Not set')
    
    # Get Python's detected timezone
    python_tz = str(local_time.astimezone().tzinfo)
    
    print(f"  System UTC offset: {utc_offset} hours")
    print(f"  Environment TZ: {env_tz}")
    print(f"  Python timezone: {python_tz}")
    
    # Check if system is set to UTC
    is_utc_system = abs(utc_offset) < 0.1
    print(f"✅ System appears to be UTC: {is_utc_system}")
    
    if not is_utc_system:
        print(f"⚠️ WARNING: System timezone offset is {utc_offset} hours from UTC")
        print("  Consider setting your server timezone to UTC for consistency")
    
    return {
        "utc_offset": utc_offset,
        "env_tz": env_tz,
        "python_tz": python_tz,
        "is_utc_system": is_utc_system
    }

def test_timing_precision():
    """Test timing precision and consistency."""
    print("\n⚡ Testing Timing Precision...")
    
    measurements = []
    for i in range(10):
        start_ns = time.time_ns()
        timestamp = get_high_precision_time()
        end_ns = time.time_ns()
        
        # Calculate the time it took to get the timestamp
        duration_ns = end_ns - start_ns
        duration_us = duration_ns / 1000  # Convert to microseconds
        
        measurements.append({
            "iteration": i + 1,
            "duration_microseconds": duration_us,
            "timestamp": timestamp.isoformat()
        })
        
        time.sleep(0.01)  # Small delay between measurements
    
    # Calculate statistics
    durations = [m["duration_microseconds"] for m in measurements]
    avg_duration = sum(durations) / len(durations)
    max_duration = max(durations)
    min_duration = min(durations)
    
    print(f"  Average timestamp generation time: {avg_duration:.1f} μs")
    print(f"  Min/Max: {min_duration:.1f} / {max_duration:.1f} μs")
    
    # Check if timing is consistent (should be under 100 microseconds)
    timing_good = avg_duration < 100
    print(f"✅ Timing precision acceptable: {timing_good}")
    
    return timing_good, measurements

def generate_test_report():
    """Generate a comprehensive test report."""
    print("🔍 TIMING FIXES TEST REPORT")
    print("=" * 50)
    
    # Run all tests
    utc_consistent, utc_results = test_utc_timestamp_consistency()
    timezone_logging_ok = test_timezone_aware_logging()
    recorder_fixed = test_timestamp_recorder_fixes()
    system_info = test_system_timezone_detection()
    timing_good, timing_measurements = test_timing_precision()
    
    # Generate summary
    print("\n📋 TEST SUMMARY")
    print("-" * 30)
    
    tests_passed = 0
    total_tests = 5
    
    if utc_consistent:
        print("✅ UTC Timestamp Consistency: PASSED")
        tests_passed += 1
    else:
        print("❌ UTC Timestamp Consistency: FAILED")
    
    if timezone_logging_ok:
        print("✅ Timezone-Aware Logging: PASSED")
        tests_passed += 1
    else:
        print("❌ Timezone-Aware Logging: FAILED")
    
    if recorder_fixed:
        print("✅ TimestampRecorder Fixes: PASSED")
        tests_passed += 1
    else:
        print("❌ TimestampRecorder Fixes: FAILED")
    
    if system_info["is_utc_system"]:
        print("✅ System Timezone (UTC): PASSED")
        tests_passed += 1
    else:
        print("⚠️ System Timezone (UTC): WARNING - Not UTC")
    
    if timing_good:
        print("✅ Timing Precision: PASSED")
        tests_passed += 1
    else:
        print("❌ Timing Precision: FAILED")
    
    success_rate = (tests_passed / total_tests) * 100
    print(f"\n🎯 Overall Success Rate: {success_rate:.1f}% ({tests_passed}/{total_tests})")
    
    # Save detailed report
    report = {
        "test_timestamp": datetime.now(pytz.UTC).isoformat(),
        "summary": {
            "tests_passed": tests_passed,
            "total_tests": total_tests,
            "success_rate": success_rate
        },
        "test_results": {
            "utc_consistency": {
                "passed": utc_consistent,
                "results": utc_results
            },
            "timezone_logging": {
                "passed": timezone_logging_ok
            },
            "timestamp_recorder": {
                "passed": recorder_fixed
            },
            "system_info": system_info,
            "timing_precision": {
                "passed": timing_good,
                "measurements": timing_measurements
            }
        },
        "recommendations": []
    }
    
    # Add recommendations based on test results
    if not system_info["is_utc_system"]:
        report["recommendations"].append(
            f"Set server timezone to UTC (currently offset by {system_info['utc_offset']} hours)"
        )
    
    if not timing_good:
        report["recommendations"].append(
            "Investigate system performance issues affecting timestamp precision"
        )
    
    if success_rate < 100:
        report["recommendations"].append(
            "Review failed tests and implement additional fixes"
        )
    
    # Save report to file
    report_filename = f"timing_fixes_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n📄 Detailed report saved to: {report_filename}")
    
    return report

def main():
    """Main function to run all timing fix tests."""
    try:
        report = generate_test_report()
        
        if report["summary"]["success_rate"] >= 80:
            print("\n🎉 TIMING FIXES SUCCESSFULLY IMPLEMENTED!")
            print("Your bot should now have consistent UTC timestamps and better timing accuracy.")
        else:
            print("\n⚠️ SOME ISSUES DETECTED")
            print("Review the test results and implement additional fixes as needed.")
        
        return report["summary"]["success_rate"] >= 80
        
    except Exception as e:
        print(f"\n❌ ERROR RUNNING TESTS: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
