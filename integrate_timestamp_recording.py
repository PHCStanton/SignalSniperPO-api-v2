#!/usr/bin/env python3
"""
Integration script to add timestamp recording functionality to self_bot.py
"""

import re

def integrate_timestamp_recording():
    """Integrate timestamp recording into self_bot.py"""
    
    # Read the current self_bot.py file
    with open('self_bot.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 1. Update execute_trade_threaded method signature to accept timestamp_record
    content = re.sub(
        r'def execute_trade_threaded\(self, signal: Dict\) -> None:',
        'def execute_trade_threaded(self, signal: Dict, timestamp_record: Dict = None) -> None:',
        content
    )
    
    # 2. Add timestamp recording at the beginning of execute_trade_threaded
    execute_trade_start = content.find('def execute_trade_threaded(self, signal: Dict, timestamp_record: Dict = None) -> None:')
    if execute_trade_start != -1:
        # Find the try block start
        try_start = content.find('try:', execute_trade_start)
        if try_start != -1:
            # Find the end of the try line
            try_end = content.find('\n', try_start)
            if try_end != -1:
                # Insert timestamp recording code after the try line
                timestamp_code = '''
            # Record execution timestamp if timestamp_record provided
            if timestamp_record:
                timestamp_record = self.timestamp_recorder.record_execution_timestamp(
                    timestamp_record, 
                    f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self.session_data['trades_count'] + 1:03d}"
                )
'''
                content = content[:try_end + 1] + timestamp_code + content[try_end + 1:]
    
    # 3. Update the first trade thread creation (single message format)
    pattern1 = r'(# Save signal to JSON storage\s+self\.storage\.save_signal\(complete_signal\)\s+# Execute trade immediately using threading to avoid event loop conflict\s+logger\.info\("🚀 EXECUTING TRADE IMMEDIATELY"\)\s+trade_thread = threading\.Thread\(target=self\.execute_trade_threaded, args=\(complete_signal,\)\))'
    
    replacement1 = '''# Record signal timestamp
                    timestamp_record = self.timestamp_recorder.record_signal_timestamp(
                        signal_id=complete_signal["id"],
                        currency_pair=complete_signal["pair"],
                        session_id=self.session_id
                    )
                    
                    # Save signal to JSON storage
                    self.storage.save_signal(complete_signal)
                    
                    # Execute trade immediately using threading to avoid event loop conflict
                    logger.info("🚀 EXECUTING TRADE IMMEDIATELY")
                    trade_thread = threading.Thread(target=self.execute_trade_threaded, args=(complete_signal, timestamp_record))'''
    
    content = re.sub(pattern1, replacement1, content, flags=re.MULTILINE | re.DOTALL)
    
    # 4. Update the second trade thread creation (two-message format)
    pattern2 = r'(# Save signal to JSON storage\s+self\.storage\.save_signal\(complete_signal\)\s+# Execute trade immediately using threading\s+logger\.info\("🚀 EXECUTING TRADE IMMEDIATELY"\)\s+trade_thread = threading\.Thread\(target=self\.execute_trade_threaded, args=\(complete_signal,\)\))'
    
    replacement2 = '''# Record signal timestamp
                                timestamp_record = self.timestamp_recorder.record_signal_timestamp(
                                    signal_id=complete_signal["id"],
                                    currency_pair=complete_signal["pair"],
                                    session_id=self.session_id
                                )
                                
                                # Save signal to JSON storage
                                self.storage.save_signal(complete_signal)
                                
                                # Execute trade immediately using threading
                                logger.info("🚀 EXECUTING TRADE IMMEDIATELY")
                                trade_thread = threading.Thread(target=self.execute_trade_threaded, args=(complete_signal, timestamp_record))'''
    
    content = re.sub(pattern2, replacement2, content, flags=re.MULTILINE | re.DOTALL)
    
    # 5. Add performance stats method to SelfBot class
    stats_method = '''
    def get_timestamp_performance_stats(self) -> Dict:
        """Get timestamp performance statistics."""
        try:
            return self.timestamp_recorder.get_performance_stats()
        except Exception as e:
            logger.error(f"Error getting timestamp performance stats: {str(e)}")
            return {"error": str(e)}
    
    def get_recent_timestamp_records(self, limit: int = 10) -> List[Dict]:
        """Get recent timestamp records."""
        try:
            return self.timestamp_recorder.get_recent_records(limit)
        except Exception as e:
            logger.error(f"Error getting recent timestamp records: {str(e)}")
            return []
'''
    
    # Find the end of the SelfBot class (before the parse_arguments function)
    parse_args_start = content.find('def parse_arguments():')
    if parse_args_start != -1:
        content = content[:parse_args_start] + stats_method + '\n' + content[parse_args_start:]
    
    # Write the updated content back to the file
    with open('self_bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Timestamp recording integration completed successfully!")
    print("📊 Added features:")
    print("   - Signal timestamp recording")
    print("   - Execution timestamp recording with delay calculation")
    print("   - Performance statistics methods")
    print("   - Robust backup system for timestamp data")

if __name__ == "__main__":
    integrate_timestamp_recording()
