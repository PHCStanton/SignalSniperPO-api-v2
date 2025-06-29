#!/usr/bin/env python3
"""
Codebase Cleanup Script
Safely removes redundant and obsolete files identified in the cleanup analysis.
"""

import os
import shutil
import json
from datetime import datetime

def create_backup():
    """Create a backup of current state before cleanup"""
    backup_dir = f"backup_before_cleanup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print(f"Creating backup directory: {backup_dir}")
    
    # Create backup of essential files only
    essential_files = [
        "SignalSniper.py",
        "SignalSniper_mod.py", 
        "channel_manager.py",
        "session_manager.py",
        "timestamp_recorder.py"
    ]
    
    os.makedirs(backup_dir, exist_ok=True)
    for file in essential_files:
        if os.path.exists(file):
            shutil.copy2(file, backup_dir)
            print(f"  Backed up: {file}")
    
    return backup_dir

def cleanup_phase_1():
    """Phase 1: Delete obsolete executables and redundant test files"""
    print("\n=== PHASE 1: Obsolete Executables & Redundant Tests ===")
    
    files_to_delete = [
        # Obsolete executables
        "self_bot.py",
        "bot_integration_example.py", 
        "self_bot_v3_modular_integrated.py",
        
        # Redundant test files
        "test_pocketoptionapi.py",
        "test_channel_monitor.py",
        "test_headless_integration.py",
        "test_session_management.py",
        "test_modular_bot_integration.py",
        "test_datetime_fix_and_execution.py",
        "test_timing_fixes.py",
        "test_trade_result_fix.py",
        
        # Old latency/timing files
        "latency_monitor.py",
        "quick_latency_test.py",
        "detailed_timestamp_comparison.py",
        "timing_discrepancy_analyzer.py",
        "trading_latency_analyzer.py",
        "telegram_latency_monitor.py",
        
        # Integration/migration files
        "integrate_session_management.py",
        "integrate_timestamp_recording.py",
        "convert_excel_to_json.py",
        "install_dependencies.py",
        "extract_websocket_ssid.py",
        "get_fresh_ssid.py",
        "refresh_ssid.py",
        
        # Simulation/testing files
        "monitor_signals.py",
        "query_database.py",
        "restart_bot.py",
        "session_control.py"
    ]
    
    deleted_count = 0
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✅ Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {file}: {e}")
        else:
            print(f"  ⚠️  Not found: {file}")
    
    print(f"Phase 1 complete: {deleted_count} files deleted")

def cleanup_phase_2():
    """Phase 2: Delete log files and old JSON data"""
    print("\n=== PHASE 2: Log Files & Old JSON Data ===")
    
    files_to_delete = [
        # Log files
        "self_bot_modular.log",
        "self_bot.log",
        "check_telegram_session.log",
        
        # Old JSON data files
        "channel_latency_log_20250611_203747.json",
        "channel_latency_log_20250611_204214.json",
        "channel_latency_log_20250612_204554.json",
        "complete_latency_test_20250610_130736.json",
        "complete_latency_test_20250610_134536.json",
        "complete_latency_test_20250615_202438.json",
        "timing_analysis_report_20250616_234611.json",
        "timing_fixes_test_report_20250616_234931.json",
        
        # Duplicate config file
        "telegram_config.json"
    ]
    
    deleted_count = 0
    for file in files_to_delete:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✅ Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {file}: {e}")
        else:
            print(f"  ⚠️  Not found: {file}")
    
    print(f"Phase 2 complete: {deleted_count} files deleted")

def cleanup_phase_3():
    """Phase 3: Directory cleanup"""
    print("\n=== PHASE 3: Directory Cleanup ===")
    
    directories_to_remove = [
        "cleanup-foldetr",
        "node_modules"
    ]
    
    deleted_count = 0
    for directory in directories_to_remove:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"  ✅ Deleted directory: {directory}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {directory}: {e}")
        else:
            print(f"  ⚠️  Not found: {directory}")
    
    # Clean old backup files (keep only latest 2)
    config_dir = "config"
    if os.path.exists(config_dir):
        backup_files = [f for f in os.listdir(config_dir) if f.startswith("telegram_config.json.backup_")]
        backup_files.sort(reverse=True)  # Sort by name (newest first)
        
        # Keep only the 2 most recent backups
        files_to_delete = backup_files[2:]
        for file in files_to_delete:
            file_path = os.path.join(config_dir, file)
            try:
                os.remove(file_path)
                print(f"  ✅ Deleted old backup: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {file}: {e}")
    
    # Clean JavaScript files
    js_files = ["package.json", "package-lock.json"]
    for file in js_files:
        if os.path.exists(file):
            try:
                os.remove(file)
                print(f"  ✅ Deleted: {file}")
                deleted_count += 1
            except Exception as e:
                print(f"  ❌ Failed to delete {file}: {e}")
    
    print(f"Phase 3 complete: {deleted_count} items deleted")

def verify_essential_files():
    """Verify that essential files still exist after cleanup"""
    print("\n=== VERIFICATION: Essential Files Check ===")
    
    essential_files = [
        "SignalSniper.py",
        "SignalSniper_mod.py",
        "channel_manager.py",
        "session_manager.py",
        "timestamp_recorder.py",
        "config/bot_config.json",
        "config/telegram_config.json",
        "config/pocket_option_config.json"
    ]
    
    all_present = True
    for file in essential_files:
        if os.path.exists(file):
            print(f"  ✅ Present: {file}")
        else:
            print(f"  ❌ MISSING: {file}")
            all_present = False
    
    return all_present

def generate_cleanup_report():
    """Generate a report of the cleanup operation"""
    print("\n=== CLEANUP REPORT ===")
    
    # Count remaining files in root directory
    root_files = [f for f in os.listdir(".") if os.path.isfile(f)]
    root_dirs = [d for d in os.listdir(".") if os.path.isdir(d) and not d.startswith(".")]
    
    print(f"Remaining files in root: {len(root_files)}")
    print(f"Remaining directories: {len(root_dirs)}")
    
    # List essential files that remain
    essential_remaining = [
        f for f in root_files 
        if f.startswith(("SignalSniper", "channel_manager", "session_manager", "timestamp_recorder"))
    ]
    print(f"Essential executables: {len(essential_remaining)}")
    
    # List test files that remain
    test_remaining = [f for f in root_files if f.startswith("test_")]
    print(f"Test files remaining: {len(test_remaining)}")
    
    return {
        "total_files": len(root_files),
        "total_dirs": len(root_dirs),
        "essential_files": len(essential_remaining),
        "test_files": len(test_remaining)
    }

def main():
    """Main cleanup execution"""
    print("🧹 CODEBASE CLEANUP SCRIPT")
    print("=" * 50)
    
    # Create backup
    backup_dir = create_backup()
    
    try:
        # Execute cleanup phases
        cleanup_phase_1()
        cleanup_phase_2() 
        cleanup_phase_3()
        
        # Verify essential files
        if verify_essential_files():
            print("\n✅ All essential files verified present")
        else:
            print("\n❌ Some essential files are missing!")
            return False
        
        # Generate report
        report = generate_cleanup_report()
        
        print(f"\n🎉 CLEANUP COMPLETED SUCCESSFULLY!")
        print(f"Backup created at: {backup_dir}")
        print(f"Final file count: {report['total_files']} files, {report['total_dirs']} directories")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Cleanup failed: {e}")
        print(f"Backup available at: {backup_dir}")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
