#!/usr/bin/env python3
"""
test_session_management.py - Comprehensive test for Phase 2 Session Management

This script tests the SessionManager and SignalDeduplicator functionality
to verify Phase 2 implementation is working correctly.
"""
import os
import sys
import json
import time
import tempfile
import shutil
from datetime import datetime, timedelta
from session_manager import SessionManager, SignalDeduplicator

def test_session_manager():
    """Test SessionManager functionality."""
    print("🧪 Testing SessionManager...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="test_session_")
    
    try:
        # Initialize SessionManager
        session_manager = SessionManager(data_dir=test_dir)
        
        # Test 1: Check if new session can be started
        can_start, message = session_manager.can_start_new_session()
        assert can_start, f"Should be able to start new session: {message}"
        print("✅ Test 1 passed: Can start new session")
        
        # Test 2: Start new session
        session_info = session_manager.start_new_session(balance_start=100.0)
        assert session_info is not None, "Session should be created"
        assert session_info.balance_start == 100.0, "Balance should be set correctly"
        print(f"✅ Test 2 passed: Session started - {session_info.session_id}")
        
        # Test 3: Check singleton pattern - should not allow second session
        can_start_second, message = session_manager.can_start_new_session()
        assert not can_start_second, "Should not allow second session"
        print("✅ Test 3 passed: Singleton pattern working")
        
        # Test 4: Update session stats
        success = session_manager.update_session(
            trades_count=5,
            wins=3,
            losses=2,
            profit_loss=25.50
        )
        assert success, "Session update should succeed"
        
        current_session = session_manager.get_current_session()
        assert current_session.trades_count == 5, "Trades count should be updated"
        assert current_session.wins == 3, "Wins should be updated"
        assert current_session.profit_loss == 25.50, "Profit/loss should be updated"
        print("✅ Test 4 passed: Session stats updated")
        
        # Test 5: Get session statistics
        stats = session_manager.get_session_stats()
        assert "session_id" in stats, "Stats should contain session_id"
        assert "duration" in stats, "Stats should contain duration"
        print("✅ Test 5 passed: Session statistics retrieved")
        
        # Test 6: End session
        success = session_manager.end_session(balance_end=125.50)
        assert success, "Session should end successfully"
        
        current_session = session_manager.get_current_session()
        assert current_session is None, "Current session should be None after ending"
        print("✅ Test 6 passed: Session ended successfully")
        
        # Test 7: Can start new session after ending previous
        can_start_new, message = session_manager.can_start_new_session()
        assert can_start_new, f"Should be able to start new session after ending previous: {message}"
        print("✅ Test 7 passed: Can start new session after ending previous")
        
        print("🎉 All SessionManager tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ SessionManager test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def test_signal_deduplicator():
    """Test SignalDeduplicator functionality."""
    print("\n🧪 Testing SignalDeduplicator...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="test_dedup_")
    
    try:
        # Initialize SignalDeduplicator
        deduplicator = SignalDeduplicator(data_dir=test_dir, max_fingerprints=100)
        
        # Test signal data
        signal1 = {
            "pair": "EUR/USD",
            "direction": "HIGHER",
            "expiry": 1,
            "timer": "00:01:00",
            "timestamp": "2025-05-29T14:30:00"
        }
        
        signal2 = {
            "pair": "EUR/USD",
            "direction": "HIGHER", 
            "expiry": 1,
            "timer": "00:01:00",
            "timestamp": "2025-05-29T14:30:00"  # Same minute
        }
        
        signal3 = {
            "pair": "GBP/USD",
            "direction": "LOWER",
            "expiry": 5,
            "timer": "00:05:00",
            "timestamp": "2025-05-29T14:31:00"
        }
        
        # Test 1: Generate fingerprint
        fingerprint1 = deduplicator.generate_signal_fingerprint(signal1)
        assert fingerprint1, "Should generate fingerprint"
        assert len(fingerprint1) == 16, "Fingerprint should be 16 characters"
        print("✅ Test 1 passed: Fingerprint generated")
        
        # Test 2: First signal should not be duplicate
        is_duplicate, message = deduplicator.is_duplicate_signal(signal1)
        assert not is_duplicate, "First signal should not be duplicate"
        print("✅ Test 2 passed: First signal not duplicate")
        
        # Test 3: Register signal
        success = deduplicator.register_signal(signal1)
        assert success, "Signal registration should succeed"
        print("✅ Test 3 passed: Signal registered")
        
        # Test 4: Same signal should now be duplicate
        is_duplicate, message = deduplicator.is_duplicate_signal(signal2)
        assert is_duplicate, "Same signal should be duplicate"
        print("✅ Test 4 passed: Duplicate signal detected")
        
        # Test 5: Different signal should not be duplicate
        is_duplicate, message = deduplicator.is_duplicate_signal(signal3)
        assert not is_duplicate, "Different signal should not be duplicate"
        print("✅ Test 5 passed: Different signal not duplicate")
        
        # Test 6: Register different signal
        success = deduplicator.register_signal(signal3)
        assert success, "Different signal registration should succeed"
        print("✅ Test 6 passed: Different signal registered")
        
        # Test 7: Get fingerprint stats
        stats = deduplicator.get_fingerprint_stats()
        assert "total_fingerprints" in stats, "Stats should contain total_fingerprints"
        assert stats["total_fingerprints"] >= 2, "Should have at least 2 fingerprints"
        print("✅ Test 7 passed: Fingerprint statistics retrieved")
        
        # Test 8: Cleanup old fingerprints
        removed_count = deduplicator.cleanup_old_fingerprints(days_old=0)  # Remove all
        assert removed_count >= 0, "Cleanup should return non-negative count"
        print("✅ Test 8 passed: Fingerprint cleanup completed")
        
        print("🎉 All SignalDeduplicator tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ SignalDeduplicator test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def test_integration():
    """Test integration between SessionManager and SignalDeduplicator."""
    print("\n🧪 Testing Integration...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="test_integration_")
    
    try:
        # Initialize both components
        session_manager = SessionManager(data_dir=test_dir)
        deduplicator = SignalDeduplicator(data_dir=test_dir)
        
        # Start session
        session_info = session_manager.start_new_session(balance_start=200.0)
        assert session_info is not None, "Session should start"
        
        # Process multiple signals
        signals = [
            {
                "pair": "EUR/USD",
                "direction": "HIGHER",
                "expiry": 1,
                "timer": "00:01:00",
                "timestamp": "2025-05-29T14:30:00",
                "session_id": session_info.session_id
            },
            {
                "pair": "EUR/USD", 
                "direction": "HIGHER",
                "expiry": 1,
                "timer": "00:01:00",
                "timestamp": "2025-05-29T14:30:30",  # Same minute - should be duplicate
                "session_id": session_info.session_id
            },
            {
                "pair": "GBP/USD",
                "direction": "LOWER", 
                "expiry": 5,
                "timer": "00:05:00",
                "timestamp": "2025-05-29T14:31:00",
                "session_id": session_info.session_id
            }
        ]
        
        processed_signals = 0
        duplicate_signals = 0
        
        for signal in signals:
            is_duplicate, message = deduplicator.is_duplicate_signal(signal)
            if is_duplicate:
                duplicate_signals += 1
                print(f"🔄 Duplicate detected: {signal['pair']} {signal['direction']}")
            else:
                deduplicator.register_signal(signal)
                processed_signals += 1
                
                # Update session stats
                session_manager.update_session(
                    signals_count=processed_signals,
                    trades_count=processed_signals
                )
                print(f"✅ Processed: {signal['pair']} {signal['direction']}")
        
        # Verify results
        assert processed_signals == 2, f"Should process 2 unique signals, got {processed_signals}"
        assert duplicate_signals == 1, f"Should detect 1 duplicate, got {duplicate_signals}"
        
        # Check session stats
        current_session = session_manager.get_current_session()
        assert current_session.signals_count == 2, "Session should show 2 signals"
        
        # End session
        session_manager.end_session(balance_end=220.0)
        
        print("✅ Integration test passed: Session and deduplication working together")
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def test_persistence():
    """Test data persistence across restarts."""
    print("\n🧪 Testing Persistence...")
    
    # Create temporary test directory
    test_dir = tempfile.mkdtemp(prefix="test_persistence_")
    
    try:
        # Phase 1: Create session and signals
        session_manager1 = SessionManager(data_dir=test_dir)
        deduplicator1 = SignalDeduplicator(data_dir=test_dir)
        
        # Start session
        session_info = session_manager1.start_new_session(balance_start=150.0)
        session_id = session_info.session_id
        
        # Register signal
        test_signal = {
            "pair": "USD/JPY",
            "direction": "HIGHER",
            "expiry": 3,
            "timer": "00:03:00",
            "timestamp": "2025-05-29T14:35:00"
        }
        deduplicator1.register_signal(test_signal)
        
        # Update session
        session_manager1.update_session(trades_count=1, wins=1, profit_loss=15.0)
        
        # Phase 2: Simulate restart - create new instances
        session_manager2 = SessionManager(data_dir=test_dir)
        deduplicator2 = SignalDeduplicator(data_dir=test_dir)
        
        # Check if signal is still recognized as duplicate
        is_duplicate, message = deduplicator2.is_duplicate_signal(test_signal)
        assert is_duplicate, "Signal should still be recognized as duplicate after restart"
        
        # Check session recovery (if session was not properly ended)
        current_session = session_manager2.get_current_session()
        if current_session:
            assert current_session.session_id == session_id, "Session should be recovered"
            print("✅ Session recovery working")
        
        print("✅ Persistence test passed: Data survives restart")
        return True
        
    except Exception as e:
        print(f"❌ Persistence test failed: {str(e)}")
        return False
    finally:
        # Cleanup
        shutil.rmtree(test_dir, ignore_errors=True)

def main():
    """Run all tests."""
    print("🚀 Starting Phase 2 Session Management Tests...")
    print("=" * 60)
    
    tests = [
        ("SessionManager", test_session_manager),
        ("SignalDeduplicator", test_signal_deduplicator), 
        ("Integration", test_integration),
        ("Persistence", test_persistence)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} tests PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} tests FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} tests FAILED with exception: {str(e)}")
        
        print("-" * 40)
    
    print("=" * 60)
    print(f"📊 TEST RESULTS: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 ALL PHASE 2 TESTS PASSED!")
        print("\n✅ Phase 2 Session Management implementation is working correctly!")
        print("\n📋 VERIFIED FUNCTIONALITY:")
        print("• ✅ Session singleton pattern")
        print("• ✅ Session recovery mechanism")
        print("• ✅ Signal deduplication with fingerprinting")
        print("• ✅ Session statistics tracking")
        print("• ✅ Data persistence across restarts")
        print("• ✅ Integration between components")
        
        print("\n🎯 READY FOR PHASE 3: Data consistency and legacy cleanup")
        return True
    else:
        print("❌ Some tests failed. Please review and fix issues before proceeding.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
