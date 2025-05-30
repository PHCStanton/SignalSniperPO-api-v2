#!/usr/bin/env python3
"""
integrate_session_management.py - Integration script for Phase 2 Session Management

This script integrates the SessionManager and SignalDeduplicator into the existing self_bot.py
to complete Phase 2 implementation as specified in the Custom Instructions.
"""
import os
import re
import shutil
from datetime import datetime

def backup_file(file_path):
    """Create a backup of the original file."""
    backup_path = f"{file_path}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    shutil.copy2(file_path, backup_path)
    print(f"✅ Created backup: {backup_path}")
    return backup_path

def integrate_session_management():
    """Integrate session management into self_bot.py."""
    file_path = "self_bot.py"
    
    if not os.path.exists(file_path):
        print(f"❌ Error: {file_path} not found")
        return False
    
    # Create backup
    backup_path = backup_file(file_path)
    
    try:
        # Read the current file
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 1. Add session manager and signal deduplicator initialization
        # Find the position after timestamp recorder initialization
        timestamp_pattern = r'(        # Timestamp recorder for robust timestamp recording\n        self\.timestamp_recorder = TimestampRecorder\(\n            data_dir=data_dir,\n            max_records=json_config\.get\("max_records", 1000\)\n        \))'
        
        if re.search(timestamp_pattern, content):
            replacement = r'\1\n        \n        # Session manager for singleton pattern and session recovery\n        self.session_manager = SessionManager(\n            data_dir=data_dir,\n            timezone=self.config.get("timezone", "Africa/Johannesburg")\n        )\n        \n        # Signal deduplicator for preventing duplicate signal processing\n        self.signal_deduplicator = SignalDeduplicator(\n            data_dir=data_dir,\n            max_fingerprints=json_config.get("max_fingerprints", 1000)\n        )'
            
            content = re.sub(timestamp_pattern, replacement, content)
            print("✅ Added session manager and signal deduplicator initialization")
        else:
            print("⚠️ Could not find timestamp recorder pattern, trying alternative approach")
            # Alternative: Add after amount calculator
            amount_pattern = r'(        # Amount calculator\n        self\.amount_calculator = None\n        self\.session_amount = None)'
            
            if re.search(amount_pattern, content):
                replacement = r'\1\n        \n        # Session manager for singleton pattern and session recovery\n        self.session_manager = SessionManager(\n            data_dir=data_dir,\n            timezone=self.config.get("timezone", "Africa/Johannesburg")\n        )\n        \n        # Signal deduplicator for preventing duplicate signal processing\n        self.signal_deduplicator = SignalDeduplicator(\n            data_dir=data_dir,\n            max_fingerprints=json_config.get("max_fingerprints", 1000)\n        )'
                
                content = re.sub(amount_pattern, replacement, content)
                print("✅ Added session manager and signal deduplicator initialization (alternative position)")
            else:
                print("❌ Could not find suitable position for session manager initialization")
                return False
        
        # 2. Update session initialization to use SessionManager
        session_pattern = r'        # Session data\n        self\.session_id = f"session_{datetime\.now\(\)\.strftime\(\'%Y%m%d_%H%M%S\'\)}"\n        self\.session_data = \{\n            "session_id": self\.session_id,\n            "start_time": datetime\.now\(\)\.isoformat\(\),\n            "balance_start": 0\.0,\n            "trades_count": 0,\n            "wins": 0,\n            "losses": 0,\n            "draws": 0,\n            "profit_loss": 0\.0\n        \}'
        
        session_replacement = '''        # Session data - will be managed by SessionManager
        self.session_id = None
        self.session_data = {}'''
        
        if re.search(session_pattern, content):
            content = re.sub(session_pattern, session_replacement, content)
            print("✅ Updated session data initialization")
        
        # 3. Add session management methods
        methods_to_add = '''
    def initialize_session_management(self) -> bool:
        """Initialize session management with singleton pattern and recovery."""
        try:
            # Check if we can start a new session
            can_start, message = self.session_manager.can_start_new_session()
            if not can_start:
                logger.error(f"Cannot start new session: {message}")
                return False
            
            # Get initial balance for session
            initial_balance = 0.0
            if self.pocket_option_client:
                try:
                    balance = self.pocket_option_client.get_balance()
                    if balance is not None:
                        initial_balance = float(balance)
                except Exception as e:
                    logger.warning(f"Could not get initial balance: {str(e)}")
            
            # Start new session
            session_info = self.session_manager.start_new_session(initial_balance)
            if session_info:
                self.session_id = session_info.session_id
                self.session_data = {
                    "session_id": session_info.session_id,
                    "start_time": session_info.start_time,
                    "balance_start": session_info.balance_start,
                    "trades_count": session_info.trades_count,
                    "wins": session_info.wins,
                    "losses": session_info.losses,
                    "draws": session_info.draws,
                    "profit_loss": session_info.profit_loss
                }
                logger.info(f"✅ Session management initialized: {self.session_id}")
                return True
            else:
                logger.error("Failed to start new session")
                return False
        except Exception as e:
            logger.error(f"Error initializing session management: {str(e)}")
            return False
    
    def update_session_stats(self, **kwargs) -> None:
        """Update session statistics."""
        try:
            if self.session_manager:
                self.session_manager.update_session(**kwargs)
                
                # Update local session data
                current_session = self.session_manager.get_current_session()
                if current_session:
                    self.session_data.update({
                        "trades_count": current_session.trades_count,
                        "wins": current_session.wins,
                        "losses": current_session.losses,
                        "draws": current_session.draws,
                        "profit_loss": current_session.profit_loss
                    })
        except Exception as e:
            logger.error(f"Error updating session stats: {str(e)}")
    
    def check_signal_duplicate(self, signal_data: Dict) -> bool:
        """Check if signal is a duplicate using the signal deduplicator."""
        try:
            is_duplicate, message = self.signal_deduplicator.is_duplicate_signal(signal_data)
            if is_duplicate:
                logger.warning(f"🔄 DUPLICATE SIGNAL DETECTED: {message}")
                return True
            
            # Register the signal to prevent future duplicates
            self.signal_deduplicator.register_signal(signal_data)
            return False
        except Exception as e:
            logger.error(f"Error checking signal duplicate: {str(e)}")
            return False
    
    def get_session_statistics(self) -> Dict:
        """Get comprehensive session statistics."""
        try:
            session_stats = self.session_manager.get_session_stats() if self.session_manager else {}
            fingerprint_stats = self.signal_deduplicator.get_fingerprint_stats() if self.signal_deduplicator else {}
            timestamp_stats = self.get_timestamp_performance_stats()
            
            return {
                "session": session_stats,
                "fingerprints": fingerprint_stats,
                "timestamps": timestamp_stats,
                "trading_stats": self.stats
            }
        except Exception as e:
            logger.error(f"Error getting session statistics: {str(e)}")
            return {"error": str(e)}
    
    def cleanup_session(self) -> None:
        """Clean up session data and end current session."""
        try:
            if self.session_manager:
                # Get final balance
                final_balance = None
                if self.pocket_option_client:
                    try:
                        final_balance = self.pocket_option_client.get_balance()
                        if final_balance is not None:
                            final_balance = float(final_balance)
                    except Exception as e:
                        logger.warning(f"Could not get final balance: {str(e)}")
                
                # End session
                self.session_manager.end_session(final_balance)
                logger.info("✅ Session cleanup completed")
        except Exception as e:
            logger.error(f"Error during session cleanup: {str(e)}")
'''
        
        # Find the position before get_timestamp_performance_stats method
        stats_method_pattern = r'(\n    def get_timestamp_performance_stats\(self\) -> Dict:)'
        
        if re.search(stats_method_pattern, content):
            content = re.sub(stats_method_pattern, methods_to_add + r'\1', content)
            print("✅ Added session management methods")
        else:
            # Add before the parse_arguments function
            parse_args_pattern = r'(\ndef parse_arguments\(\):)'
            if re.search(parse_args_pattern, content):
                content = re.sub(parse_args_pattern, methods_to_add + r'\1', content)
                print("✅ Added session management methods (alternative position)")
        
        # 4. Update process_message to include duplicate checking
        process_message_pattern = r'(                logger\.info\(f"🎯 COMPLETE SIGNAL DETECTED: \{complete_signal\}"\)\n                self\.stats\["total_signals"\] \+= 1)'
        
        process_message_replacement = r'\1\n                \n                # Check for duplicate signals\n                if self.check_signal_duplicate(complete_signal):\n                    logger.warning("❌ Duplicate signal ignored")\n                    return'
        
        if re.search(process_message_pattern, content):
            content = re.sub(process_message_pattern, process_message_replacement, content)
            print("✅ Added duplicate signal checking to process_message")
        
        # 5. Update main function to initialize session management
        main_init_pattern = r'(    json_storage_initialized = bot\.initialize_json_storage\(\)\n    if not json_storage_initialized:\n        logger\.error\("Failed to initialize JSON storage\. Exiting\.\.\."\)\n        sys\.exit\(1\))'
        
        main_init_replacement = r'\1\n    \n    # Initialize session management\n    session_management_initialized = bot.initialize_session_management()\n    if not session_management_initialized:\n        logger.error("Failed to initialize session management. Exiting...")\n        sys.exit(1)'
        
        if re.search(main_init_pattern, content):
            content = re.sub(main_init_pattern, main_init_replacement, content)
            print("✅ Added session management initialization to main function")
        
        # 6. Update signal handler to include cleanup
        signal_handler_pattern = r'(def signal_handler\(sig, frame\):\n        logger\.info\("Shutting down Self Bot\.\.\."\)\n        sys\.exit\(0\))'
        
        signal_handler_replacement = r'def signal_handler(sig, frame):\n        logger.info("Shutting down Self Bot...")\n        if "bot" in locals():\n            bot.cleanup_session()\n        sys.exit(0)'
        
        if re.search(signal_handler_pattern, content):
            content = re.sub(signal_handler_pattern, signal_handler_replacement, content)
            print("✅ Updated signal handler to include session cleanup")
        
        # 7. Update trade execution to update session stats
        trade_execution_pattern = r'(            # Increment executed trades counter\n            self\.stats\["executed_trades"\] \+= 1)'
        
        trade_execution_replacement = r'\1\n            \n            # Update session statistics\n            self.update_session_stats(trades_count=self.stats["executed_trades"])'
        
        if re.search(trade_execution_pattern, content):
            content = re.sub(trade_execution_pattern, trade_execution_replacement, content)
            print("✅ Added session stats update to trade execution")
        
        # Write the updated content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Successfully integrated session management into {file_path}")
        print(f"📋 Backup created at: {backup_path}")
        return True
        
    except Exception as e:
        print(f"❌ Error during integration: {str(e)}")
        # Restore backup
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, file_path)
            print(f"🔄 Restored from backup: {backup_path}")
        return False

def main():
    """Main function to run the integration."""
    print("🚀 Starting Phase 2 Session Management Integration...")
    print("=" * 60)
    
    success = integrate_session_management()
    
    print("=" * 60)
    if success:
        print("✅ Phase 2 Session Management Integration COMPLETED!")
        print("\n📋 INTEGRATION SUMMARY:")
        print("• ✅ SessionManager and SignalDeduplicator initialized")
        print("• ✅ Session singleton pattern implemented")
        print("• ✅ Signal deduplication system added")
        print("• ✅ Session recovery mechanism integrated")
        print("• ✅ Session statistics and cleanup methods added")
        print("• ✅ Main function updated with session management")
        print("• ✅ Signal processing updated with duplicate checking")
        print("\n🎯 NEXT STEPS:")
        print("1. Test the updated self_bot.py")
        print("2. Verify session management functionality")
        print("3. Continue with Phase 3 implementation")
    else:
        print("❌ Phase 2 Session Management Integration FAILED!")
        print("Please check the error messages above and try again.")

if __name__ == "__main__":
    main()
