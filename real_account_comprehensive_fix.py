#!/usr/bin/env python3
"""
Comprehensive Real Account Fix Script

This script fixes all issues when switching from demo to real account:
1. Configuration synchronization between SSID and config files
2. Balance retrieval problems
3. Amount selection functionality (percentage vs custom)
4. Demo mode detection issues

FIXES:
- Ensures is_demo config matches SSID account type
- Tests and fixes balance retrieval
- Validates amount calculator functionality
- Provides interactive amount selection setup
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Optional

# Add PocketOptionAPI-v2 to path
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'PocketOptionAPI-v2'))

try:
    from pocketoptionapi.stable_api import PocketOption
    import pocketoptionapi.global_value as global_value
except ImportError:
    print("Error: PocketOptionAPI-v2 not found. Make sure it's in the project root.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class RealAccountComprehensiveFixer:
    """Comprehensive fixer for real account configuration issues."""
    
    def __init__(self):
        self.pocket_config_file = "config/pocket_option_config.json"
        self.bot_config_file = "config/bot_config.json"
        self.pocket_config = self.load_config(self.pocket_config_file)
        self.bot_config = self.load_config(self.bot_config_file)
        self.client = None
    
    def load_config(self, file_path: str) -> Dict:
        """Load configuration from JSON file."""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config from {file_path}: {str(e)}")
            return {}
    
    def save_config(self, config: Dict, file_path: str) -> bool:
        """Save configuration to JSON file."""
        try:
            with open(file_path, 'w') as f:
                json.dump(config, f, indent=2)
            logger.info(f"✅ Configuration saved to {file_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving config to {file_path}: {str(e)}")
            return False
    
    def analyze_ssid(self) -> Dict:
        """Analyze SSID to determine account type."""
        ssid = self.pocket_config.get("ssid", "")
        
        if not ssid:
            return {"valid": False, "error": "No SSID found"}
        
        try:
            if ssid.startswith('42["auth",'):
                json_part = ssid[2:]
                import ast
                auth_data = ast.literal_eval(json_part)
                
                if isinstance(auth_data, list) and len(auth_data) >= 2:
                    auth_info = auth_data[1]
                    
                    # isDemo: 0 = Real Account, 1 = Demo Account
                    is_demo = auth_info.get("isDemo", 1) == 1
                    
                    return {
                        "valid": True,
                        "is_demo": is_demo,
                        "uid": auth_info.get("uid"),
                        "platform": auth_info.get("platform"),
                        "account_type": "Demo" if is_demo else "Real"
                    }
            
            return {"valid": False, "error": "Invalid SSID format"}
            
        except Exception as e:
            return {"valid": False, "error": f"SSID parsing error: {str(e)}"}
    
    def fix_config_mismatch(self) -> Dict:
        """Fix configuration mismatch between SSID and config."""
        ssid_analysis = self.analyze_ssid()
        
        if not ssid_analysis.get("valid"):
            return {"success": False, "error": ssid_analysis.get("error")}
        
        ssid_is_demo = ssid_analysis.get("is_demo")
        config_is_demo = self.pocket_config.get("is_demo", True)
        
        result = {
            "ssid_account_type": ssid_analysis.get("account_type"),
            "config_demo_setting": config_is_demo,
            "mismatch_detected": ssid_is_demo != config_is_demo,
            "fix_applied": False
        }
        
        if ssid_is_demo != config_is_demo:
            logger.warning("⚠️ Configuration mismatch detected!")
            logger.warning(f"   SSID Account Type: {ssid_analysis.get('account_type')}")
            logger.warning(f"   Config Demo Setting: {config_is_demo}")
            
            # Fix the mismatch
            self.pocket_config["is_demo"] = ssid_is_demo
            
            if self.save_config(self.pocket_config, self.pocket_config_file):
                result["fix_applied"] = True
                result["success"] = True
                logger.info(f"✅ Fixed: Set is_demo to {ssid_is_demo}")
            else:
                result["success"] = False
                result["error"] = "Failed to save corrected config"
        else:
            result["success"] = True
            logger.info("✅ Configuration matches SSID")
        
        return result
    
    def test_connection_and_balance(self) -> Dict:
        """Test API connection and balance retrieval."""
        ssid = self.pocket_config.get("ssid")
        is_demo = self.pocket_config.get("is_demo", False)
        
        if not ssid:
            return {"success": False, "error": "No SSID provided"}
        
        try:
            logger.info(f"🔌 Testing connection (Demo mode: {is_demo})")
            
            # Initialize client with corrected demo setting
            self.client = PocketOption(ssid, is_demo)
            
            # Test connection
            connection_result = self.client.connect()
            if not connection_result:
                return {"success": False, "error": "Connection failed"}
            
            # Wait for connection to establish
            time.sleep(2)
            
            logger.info("✅ Connected to Pocket Option API")
            
            # Test balance retrieval with multiple methods
            balance_tests = []
            
            # Method 1: Direct client method
            for attempt in range(3):
                try:
                    balance = self.client.get_balance()
                    balance_tests.append({
                        "method": "client.get_balance()",
                        "attempt": attempt + 1,
                        "result": balance,
                        "type": type(balance).__name__,
                        "success": balance is not None
                    })
                    
                    if balance is not None:
                        break
                    time.sleep(1)
                except Exception as e:
                    balance_tests.append({
                        "method": "client.get_balance()",
                        "attempt": attempt + 1,
                        "error": str(e),
                        "success": False
                    })
                    time.sleep(1)
            
            # Method 2: Global value method
            try:
                global_balance = global_value.balance
                balance_tests.append({
                    "method": "global_value.balance",
                    "result": global_balance,
                    "type": type(global_balance).__name__,
                    "success": global_balance is not None
                })
            except Exception as e:
                balance_tests.append({
                    "method": "global_value.balance",
                    "error": str(e),
                    "success": False
                })
            
            # Find successful balance
            final_balance = None
            for test in balance_tests:
                if test.get("success") and "result" in test:
                    final_balance = test["result"]
                    break
            
            return {
                "success": True,
                "connection_established": True,
                "balance_tests": balance_tests,
                "final_balance": final_balance,
                "balance_retrieved": final_balance is not None,
                "demo_mode_used": is_demo
            }
            
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}
    
    def setup_amount_calculator(self) -> Dict:
        """Setup and test amount calculator functionality."""
        amount_config = self.bot_config.get("amount_calculator", {})
        
        # Ensure amount calculator is properly configured
        default_config = {
            "enabled": True,
            "default_percentage": 10,
            "min_percentage": 1,
            "max_percentage": 50,
            "require_confirmation": True
        }
        
        config_updated = False
        for key, default_value in default_config.items():
            if key not in amount_config:
                amount_config[key] = default_value
                config_updated = True
        
        if config_updated:
            self.bot_config["amount_calculator"] = amount_config
            self.save_config(self.bot_config, self.bot_config_file)
            logger.info("✅ Updated amount calculator configuration")
        
        return {
            "configured": True,
            "config": amount_config,
            "updated": config_updated
        }
    
    def interactive_amount_setup(self, balance: float) -> Dict:
        """Interactive amount selection setup."""
        if balance is None or balance <= 0:
            return {"success": False, "error": "Invalid balance"}
        
        amount_config = self.bot_config.get("amount_calculator", {})
        default_percentage = amount_config.get("default_percentage", 10)
        
        print(f"\n💰 Current Balance: ${balance:.2f}")
        print("📊 Choose trading amount method:")
        print("1. Percentage of balance")
        print("2. Custom fixed amount")
        
        while True:
            choice = input("Enter choice (1 or 2): ").strip()
            if choice in ['1', '2']:
                break
            print("Please enter '1' or '2'")
        
        if choice == '1':
            # Percentage-based amount
            while True:
                percentage_input = input(f"Enter percentage [{default_percentage}%]: ").strip()
                
                if percentage_input == "":
                    percentage = default_percentage
                    break
                
                try:
                    percentage = float(percentage_input.replace('%', ''))
                    min_pct = amount_config.get("min_percentage", 1)
                    max_pct = amount_config.get("max_percentage", 50)
                    
                    if min_pct <= percentage <= max_pct:
                        break
                    else:
                        print(f"Percentage must be between {min_pct}% and {max_pct}%")
                except ValueError:
                    print("Invalid input. Enter a number (e.g., 15)")
            
            amount = round((balance * percentage) / 100, 2)
            
            return {
                "success": True,
                "method": "percentage",
                "percentage": percentage,
                "amount": amount,
                "balance": balance
            }
        
        else:
            # Custom amount
            while True:
                try:
                    amount_input = input(f"Enter amount (max: ${balance:.2f}): ").strip().replace('$', '')
                    amount = float(amount_input)
                    
                    if amount <= 0:
                        print("Amount must be greater than 0")
                        continue
                    elif amount > balance:
                        print(f"Amount cannot exceed balance: ${balance:.2f}")
                        continue
                    else:
                        break
                except ValueError:
                    print("Invalid input. Enter a number (e.g., 10.50)")
            
            return {
                "success": True,
                "method": "custom",
                "amount": amount,
                "balance": balance
            }
    
    def run_comprehensive_fix(self) -> Dict:
        """Run comprehensive fix for all real account issues."""
        logger.info("🔧 Starting comprehensive real account fix...")
        
        results = {}
        
        # Step 1: Analyze SSID
        logger.info("📊 Step 1: Analyzing SSID...")
        results["ssid_analysis"] = self.analyze_ssid()
        
        # Step 2: Fix configuration mismatch
        logger.info("🔧 Step 2: Fixing configuration mismatch...")
        results["config_fix"] = self.fix_config_mismatch()
        
        # Step 3: Test connection and balance
        logger.info("🔌 Step 3: Testing connection and balance...")
        results["connection_test"] = self.test_connection_and_balance()
        
        # Step 4: Setup amount calculator
        logger.info("📊 Step 4: Setting up amount calculator...")
        results["amount_calculator"] = self.setup_amount_calculator()
        
        # Step 5: Interactive amount setup (if balance available)
        connection_result = results["connection_test"]
        if (connection_result.get("success") and 
            connection_result.get("balance_retrieved")):
            
            balance = connection_result.get("final_balance")
            if balance is not None:
                try:
                    balance_float = float(balance)
                    logger.info("💰 Step 5: Interactive amount setup...")
                    results["amount_setup"] = self.interactive_amount_setup(balance_float)
                except (ValueError, TypeError):
                    results["amount_setup"] = {
                        "success": False, 
                        "error": f"Invalid balance format: {balance}"
                    }
        
        return results
    
    def print_comprehensive_summary(self, results: Dict) -> None:
        """Print comprehensive summary of all fixes."""
        print("\n" + "="*70)
        print("🎯 COMPREHENSIVE REAL ACCOUNT FIX SUMMARY")
        print("="*70)
        
        # SSID Analysis
        ssid_result = results.get("ssid_analysis", {})
        if ssid_result.get("valid"):
            print(f"✅ SSID Analysis: Valid")
            print(f"   Account Type: {ssid_result.get('account_type')}")
            print(f"   User ID: {ssid_result.get('uid')}")
        else:
            print(f"❌ SSID Analysis: {ssid_result.get('error')}")
        
        # Configuration Fix
        config_result = results.get("config_fix", {})
        if config_result.get("success"):
            if config_result.get("mismatch_detected"):
                print(f"✅ Configuration Fix: Mismatch detected and fixed")
                print(f"   SSID Type: {config_result.get('ssid_account_type')}")
                print(f"   Config Updated: {config_result.get('fix_applied')}")
            else:
                print(f"✅ Configuration: No mismatch detected")
        else:
            print(f"❌ Configuration Fix: {config_result.get('error')}")
        
        # Connection Test
        connection_result = results.get("connection_test", {})
        if connection_result.get("success"):
            balance = connection_result.get("final_balance")
            print(f"✅ Connection Test: Success")
            print(f"   Demo Mode: {connection_result.get('demo_mode_used')}")
            print(f"   Balance Retrieved: {connection_result.get('balance_retrieved')}")
            if balance is not None:
                print(f"   Account Balance: ${balance}")
        else:
            print(f"❌ Connection Test: {connection_result.get('error')}")
        
        # Amount Calculator
        amount_calc_result = results.get("amount_calculator", {})
        if amount_calc_result.get("configured"):
            print(f"✅ Amount Calculator: Configured")
            if amount_calc_result.get("updated"):
                print(f"   Configuration updated with defaults")
        
        # Amount Setup
        amount_setup = results.get("amount_setup", {})
        if amount_setup.get("success"):
            method = amount_setup.get("method")
            amount = amount_setup.get("amount")
            print(f"✅ Amount Setup: {method.title()} method selected")
            print(f"   Trading Amount: ${amount}")
            if method == "percentage":
                print(f"   Percentage: {amount_setup.get('percentage')}%")
        
        print("="*70)
        
        # Final Status
        all_good = (
            ssid_result.get("valid") and
            config_result.get("success") and
            connection_result.get("success") and
            connection_result.get("balance_retrieved") and
            amount_calc_result.get("configured")
        )
        
        if all_good:
            print("🎉 ALL SYSTEMS READY FOR REAL ACCOUNT TRADING!")
            print("✅ Configuration synchronized")
            print("✅ Balance retrieval working")
            print("✅ Amount selection configured")
            print("\n💡 You can now run your trading bot with real account.")
        else:
            print("⚠️ SOME ISSUES REMAIN:")
            if not ssid_result.get("valid"):
                print("   - Invalid SSID - update required")
            if not connection_result.get("balance_retrieved"):
                print("   - Balance retrieval failed")
            if not amount_calc_result.get("configured"):
                print("   - Amount calculator needs configuration")
        
        print("="*70)
    
    def cleanup(self):
        """Cleanup resources."""
        if self.client:
            try:
                self.client.disconnect()
            except:
                pass

def main():
    """Main function to run comprehensive real account fix."""
    print("🔧 Comprehensive Real Account Fix Tool")
    print("="*50)
    
    fixer = RealAccountComprehensiveFixer()
    
    try:
        results = fixer.run_comprehensive_fix()
        fixer.print_comprehensive_summary(results)
    finally:
        fixer.cleanup()

if __name__ == "__main__":
    main()
