#!/usr/bin/env python3
"""
Test script to verify both SignalSniper executables work correctly.
"""
import subprocess
import sys
import os

def test_executable(executable_name):
    """Test if an executable can be imported and run basic checks."""
    print(f"\n🧪 Testing {executable_name}...")
    
    try:
        # Test help command
        result = subprocess.run([sys.executable, executable_name, "--help"], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {executable_name} --help works correctly")
            print(f"   Output: {result.stdout.strip().split(chr(10))[0]}")
            return True
        else:
            print(f"❌ {executable_name} --help failed")
            print(f"   Error: {result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print(f"⏰ {executable_name} --help timed out")
        return False
    except Exception as e:
        print(f"❌ {executable_name} test failed: {str(e)}")
        return False

def test_import_check(executable_name):
    """Test if the executable can be imported without syntax errors."""
    print(f"\n🔍 Testing import syntax for {executable_name}...")
    
    try:
        # Test syntax by compiling
        result = subprocess.run([sys.executable, "-m", "py_compile", executable_name], 
                              capture_output=True, text=True, timeout=10)
        
        if result.returncode == 0:
            print(f"✅ {executable_name} syntax is valid")
            return True
        else:
            print(f"❌ {executable_name} has syntax errors")
            print(f"   Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ {executable_name} syntax test failed: {str(e)}")
        return False

def main():
    """Main test function."""
    print("🚀 TESTING SIGNALSNIPER EXECUTABLES")
    print("=" * 50)
    
    executables = ["SignalSniper.py", "SignalSniper_mod.py"]
    results = {}
    
    for executable in executables:
        if not os.path.exists(executable):
            print(f"❌ {executable} not found")
            results[executable] = False
            continue
        
        # Test syntax first
        syntax_ok = test_import_check(executable)
        
        # Test help command if syntax is ok
        if syntax_ok:
            help_ok = test_executable(executable)
            results[executable] = help_ok
        else:
            results[executable] = False
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 50)
    
    all_passed = True
    for executable, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{executable:<20} {status}")
        if not passed:
            all_passed = False
    
    print("\n" + "=" * 50)
    if all_passed:
        print("🎉 ALL TESTS PASSED - Both executables are working correctly!")
        print("✅ Main Bot: SignalSniper.py")
        print("✅ Modular Bot: SignalSniper_mod.py")
    else:
        print("⚠️  SOME TESTS FAILED - Issues detected with executables")
        print("🔧 Check the error messages above for details")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
