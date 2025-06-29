#!/usr/bin/env python3
"""
Diagnostic script to check SignalSniper_mod.py for syntax errors
and verify the time offset implementation
"""

import ast
import sys

def check_syntax():
    """Check SignalSniper_mod.py for syntax errors"""
    print("🔍 Checking SignalSniper_mod.py for syntax errors...")
    
    try:
        with open('SignalSniper_mod.py', 'r', encoding='utf-8') as f:
            source_code = f.read()
        
        # Try to parse the file
        ast.parse(source_code)
        print("✅ No syntax errors found in SignalSniper_mod.py")
        
        # Check if time offset code is present
        if "time_offset" in source_code:
            print("✅ Time offset code is present in the file")
            
            # Count occurrences
            offset_count = source_code.count("time_offset")
            print(f"   Found {offset_count} references to 'time_offset'")
            
            # Check for the log message
            if "TIME OFFSET: Applying" in source_code:
                print("✅ Time offset log message is present")
            else:
                print("⚠️  Time offset log message not found")
                
            # Check for time.sleep
            if "time.sleep(offset_value)" in source_code:
                print("✅ time.sleep implementation is present")
            else:
                print("⚠️  time.sleep implementation not found")
        else:
            print("❌ Time offset code not found in the file")
            
    except SyntaxError as e:
        print(f"❌ Syntax error found: {e}")
        print(f"   Line {e.lineno}: {e.text}")
        return False
    except Exception as e:
        print(f"❌ Error reading file: {e}")
        return False
    
    return True

def check_imports():
    """Check if all required imports are present"""
    print("\n🔍 Checking imports...")
    
    try:
        # Try importing the module
        sys.path.insert(0, '.')
        import SignalSniper_mod
        print("✅ SignalSniper_mod can be imported successfully")
        
        # Check for ModularSelfBot class
        if hasattr(SignalSniper_mod, 'ModularSelfBot'):
            print("✅ ModularSelfBot class found")
            
            # Check if execute_trade_threaded method exists
            bot_class = SignalSniper_mod.ModularSelfBot
            if hasattr(bot_class, 'execute_trade_threaded'):
                print("✅ execute_trade_threaded method found")
            else:
                print("❌ execute_trade_threaded method not found")
        else:
            print("❌ ModularSelfBot class not found")
            
    except ImportError as e:
        print(f"⚠️  Import error (this is normal if dependencies are missing): {e}")
    except Exception as e:
        print(f"❌ Error importing module: {e}")

def check_config():
    """Check if bot_config.json has time_offset configuration"""
    print("\n🔍 Checking configuration...")
    
    try:
        import json
        with open('config/bot_config.json', 'r') as f:
            config = json.load(f)
        
        if 'time_offset' in config:
            print("✅ time_offset configuration found in bot_config.json")
            
            time_offset = config['time_offset']
            print(f"   Enabled: {time_offset.get('enabled', False)}")
            print(f"   Default offset: {time_offset.get('default_offset', 0)} seconds")
            
            channel_specific = time_offset.get('channel_specific', {})
            for channel, settings in channel_specific.items():
                print(f"\n   {channel}:")
                print(f"      Enabled: {settings.get('enabled', False)}")
                print(f"      Offset: {settings.get('offset_value', 0)} seconds")
                print(f"      Durations: {settings.get('apply_to_durations', [])}")
        else:
            print("❌ time_offset configuration not found in bot_config.json")
            
    except Exception as e:
        print(f"❌ Error reading configuration: {e}")

def main():
    """Main diagnostic function"""
    print("🔧 SIGNALSNIPER_MOD.PY DIAGNOSTIC CHECK")
    print("=" * 50)
    
    # Check syntax
    syntax_ok = check_syntax()
    
    # Check imports
    check_imports()
    
    # Check configuration
    check_config()
    
    print("\n" + "=" * 50)
    if syntax_ok:
        print("✅ SignalSniper_mod.py appears to be syntactically correct")
        print("\n💡 If the bot is not working, possible issues:")
        print("   1. Missing dependencies (telethon, pytz, etc.)")
        print("   2. Telegram session not initialized")
        print("   3. Pocket Option SSID not configured")
        print("   4. Channel configuration issues")
        print("\n📝 Try running with verbose mode: python SignalSniper_mod.py --verbose")
    else:
        print("❌ Syntax errors found - please fix them before running")

if __name__ == "__main__":
    main()
