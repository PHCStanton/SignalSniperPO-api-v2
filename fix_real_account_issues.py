#!/usr/bin/env python3
"""
Real Account Configuration Fix Script

This script addresses the issues when switching from demo to real account:
1. Balance retrieval failure
2. Missing amount selection (percentage vs custom)
3. Configuration synchronization

Issues to fix:
- Account balance showing as None
- No amount choice prompt (should offer percentage or custom amount)
- Ensure real account mode is properly configured
"""

import os
import sys
import json
import time
import logging
from typing import Dict, Optional, Any

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

class RealAccountFixer:
    """Fixes real account configuration and balance retrieval issues."""
    
    def __init__(self):
        self.config_file = "config/pocket_option_config.json"
        self.bot_config_file = "config/bot_config.json"
        self.config = self.load_config(self.config_file)
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
        """Analyze the SSID to determine account type and validity."""
        ssid = self.config.get("ssid", "")
        
        if not ssid:
            return {"valid": False, "error": "No SSID found in configuration"}
        
        try:
            # Parse SSID to extract account information
            if ssid.startswith('42["auth",'):
                # Extract the JSON part
                json_part = ssid[2:]  # Remove '42' prefix
                import ast
                auth_data = ast.literal_eval(json_part)
                
                if isinstance(auth_data, list) and len(auth_data) >= 2:
                    auth_info = auth_data[1]
                    
                    analysis = {
                        "valid": True,
                        "is_demo": auth_info.get("isDemo", 1) == 1,
                        "uid": auth_info.get("uid"),
                        "platform": auth_info.get("platform"),
                        "session_info": auth_info.get("session", "")
                    }
                    
                    logger.info(f"📊 SSID Analysis:")
                    logger.info(f"   Account Type: {'Demo' if analysis['is_demo'] else 'Real'}")
                    logger.info(f"   User ID: {analysis['uid']}")
                    logger.info(f"   Platform: {analysis['platform']}")
                    
                    return analysis
            
            return {"valid": False, "error": "Invalid SSID format"}
            
        except Exception as e:
            return {"valid": False, "error": f"Error parsing SSID: {str(e)}"}
    
    def test_connection_and_balance(self) -> Dict:
        """Test connection to Pocket Option and balance retrieval."""
        ssid = self.config.get("ssid")
        is_demo = self.config.get("is_demo", False)
        
        if not ssid:
            return {"success": False, "error": "No SSID provided"}
        
        try:
            logger.info(f"🔌 Testing connection (Demo mode: {is_demo})")
            
            # Initialize client
            self.client = PocketOption(ssid, is_demo)
            
            # Test connection
            connection_result = self.client.connect()
            if not connection_result:
                return {"success": False, "error": "Failed to connect to Pocket Option API"}
            
            logger.info("✅ Successfully connected to Pocket Option API")
            
            # Test balance retrieval with multiple attempts
            balance_results = []
            for attempt in range(5):
                try:
                    balance = self.client.get_balance()
                    balance_results.append({
                        "attempt": attempt + 1,
                        "balance": balance,
                        "type": type(balance).__name__,
                        "success": balance is not None
                    })
                    
                    logger.info(f"Balance attempt {attempt + 1}: {balance} (type: {type(balance).__name__})")
                    
                    if balance is not None:
                        break
                    
                    time.sleep(1)
                except Exception as e:
                    balance_results.append({
                        "attempt": attempt + 1,
                        "error": str(e),
                        "success": False
                    })
                    logger.error(f"Balance attempt {attempt + 1} failed: {str(e)}")
                    time.sleep(1)
            
            # Find successful balance
            successful_balance = None
            for result in balance_results:
                if result.get("success") and "balance" in result:
                    successful_balance = result["balance"]
                    break
            
            return {
                "success": True,
                "connection": True,
                "balance_attempts": balance_results,
                "final_balance": successful_balance,
                "balance_retrieved": successful_balance is not None
            }
            
        except Exception as e:
            return {"success": False, "error": f"Connection test failed: {str(e)}"}
    
    def fix_configuration_mismatch(self) -> bool:
        """Fix configuration mismatch between SSID and config settings."""
        ssid_analysis = self.analyze_ssid()
        
        if not ssid_analysis.get("valid"):
            logger.error(f"❌ Invalid SSID: {ssid_analysis.get('error')}")
            return False
        
        ssid_is_demo = ssid_analysis.get("is_demo", True)
        config_is_demo = self.config.get("is_demo", True)
        
        if ssid_is_demo != config_is_demo:
            logger.warning(f"⚠️ Configuration mismatch detected:")
            logger.warning(f"   SSID indicates: {'Demo' if ssid_is_demo else 'Real'} account")
            logger.warning(f"   Config setting: {'Demo' if config_is_demo else 'Real'} account")
            
            # Update config to match SSID
            self.config["is_demo"] = ssid_is_demo
            
            if self.save_config(self.config, self.config_file):
                logger.info(f"✅ Fixed configuration mismatch - set is_demo to {ssid_is_demo}")
                return True
            else:
                logger.error("❌ Failed to save corrected configuration")
                return False
        else:
            logger.info("✅ Configuration matches SSID - no mismatch detected")
            return True
    
    def test_amount_calculator_setup(self) -> Dict:
        """Test the amount calculator configuration and functionality."""
        amount_config = self.bot_config.get("amount_calculator", {})
        
        logger.info("📊 Amount Calculator Configuration:")
        logger.info(f"   Enabled: {amount_config.get('enabled', True)}")
        logger.info(f"   Default Percentage: {amount_config.get('default_percentage', 10)}%")
        logger.info(f"   Min Percentage: {amount_config.get('min_percentage', 1)}%")
        logger.info(f"   Max Percentage: {amount_config.get('max_percentage', 50)}%")
        logger.info(f"   Require Confirmation: {amount_config.get('require_confirmation', True)}")
        
        # Check if amount calculator is properly configured
        issues = []
        
        if not amount_config.get("enabled", True):
            issues.append("Amount calculator is disabled")
        
        if amount_config.get("default_percentage", 10) <= 0:
            issues.append("Invalid default percentage")
        
        if amount_config.get("min_percentage", 1) <= 0:
            issues.append("Invalid minimum percentage")
        
        if amount_config.get("max_percentage", 50) <= 0:
            issues.append("Invalid maximum percentage")
        
        return {
            "configured": len(issues) == 0,
            "issues": issues,
            "config": amount_config
        }
    
    def simulate_amount_selection(self, balance: float) -> Dict:
        """Simulate the amount selection process."""
        if balance is None or balance <= 0:
            return {"success": False, "error": "Invalid balance for amount calculation"}
        
        amount_config = self.bot_config.get("amount_calculator", {})
        default_percentage = amount_config.get("default_percentage", 10)
        
        # Calculate percentage-based amount
        percentage_amount = round((balance * default_percentage) / 100, 2)
        
        # Simulate custom amount (example: $10)
        custom_amount = 10.0
        
        logger.info(f"💰 Amount Selection Simulation (Balance: ${balance:.2f}):")
        logger.info(f"   Option 1 - Percentage ({default_percentage}%): ${percentage_amount:.2f}")
        logger.info(f"   Option 2 - Custom Amount: ${custom_amount:.2f}")
        
        return {
            "success": True,
            "balance": balance,
            "percentage_option": {
                "percentage": default_percentage,
                "amount": percentage_amount
            },
            "custom_option": {
                "amount": custom_amount,
                "valid": custom_amount <= balance
            }
        }
    
    def run_comprehensive_fix(self) -> Dict:
        """Run comprehensive fix for real account issues."""
        logger.info("🔧 Starting comprehensive real account fix...")
        
        results = {
            "ssid_analysis": self.analyze_ssid(),
            "config_fix": self.fix_configuration_mismatch(),
            "connection_test": self.test_connection_and_balance(),
            "amount_calculator": self.test_amount_calculator_setup()
        }
        
        # Test amount selection if balance is available
        connection_result = results["connection_test"]
        if connection_result.get("success") and connection_result.get("balance_retrieved"):
            balance = connection_result.get("final_balance")
            if balance is not None:
                try:
                    balance_float = float(balance)
                    results["amount_simulation"] = self.simulate_amount_selection(balance_float)
                except (ValueError, TypeError):
                    results["amount_simulation"] = {"success": False, "error": f"Invalid balance format: {balance}"}
        
        return results
    
    def print_summary(self, results: Dict) -> None:
        """Print comprehensive summary of the fix results."""
        print("\n" + "="*60)
        print("🎯 REAL ACCOUNT FIX SUMMARY")
        print("="*60)
        
        # SSID Analysis
        ssid_result = results.get("ssid_analysis", {})
        if ssid_result.get("valid"):
            account_type = "Real Account" if not ssid_result.get("is_demo") else "Demo Account"
            print(f"✅ SSID Analysis: Valid - {account_type}")
            print(f"   User ID: {ssid_result.get('uid')}")
        else:
            print(f"❌ SSID Analysis: {ssid_result.get('error')}")
        
        # Configuration Fix
        config_fixed = results.get("config_fix", False)
        print(f"{'✅' if config_fixed else '❌'} Configuration Fix: {'Success' if config_fixed else 'Failed'}")
        
        # Connection Test
        connection_result = results.get("connection_test", {})
        if connection_result.get("success"):
            balance = connection_result.get("final_balance")
            balance_status = "Retrieved" if balance is not None else "Failed"
            print(f"✅ Connection Test: Success")
            print(f"   Balance Status: {balance_status}")
            if balance is not None:
                print(f"   Account Balance: ${balance}")
        else:
            print(f"❌ Connection Test: {connection_result.get('error')}")
        
        # Amount Calculator
        amount_result = results.get("amount_calculator", {})
        if amount_result.get("configured"):
            print(f"✅ Amount Calculator: Properly configured")
        else:
            print(f"❌ Amount Calculator Issues:")
            for issue in amount_result.get("issues", []):
                print(f"   - {issue}")
        
        # Amount Simulation
        amount_sim = results.get("amount_simulation", {})
        if amount_sim.get("success"):
            print(f"✅ Amount Selection: Working")
            percentage_opt = amount_sim.get("percentage_option", {})
            custom_opt = amount_sim.get("custom_option", {})
            print(f"   Percentage Option: {percentage_opt.get('percentage')}% = ${percentage_opt.get('amount')}")
            print(f"   Custom Option: ${custom_opt.get('amount')} ({'Valid' if custom_opt.get('valid') else 'Invalid'})")
        
        print("="*60)
        
        # Recommendations
        print("\n🔧 RECOMMENDATIONS:")
        
        if not ssid_result.get("valid"):
            print("1. ❌ Update your SSID - current SSID is invalid")
        
        if not connection_result.get("balance_retrieved"):
            print("2. ❌ Balance retrieval failed - check SSID validity and account status")
        
        if not amount_result.get("configured"):
            print("3. ❌ Fix amount calculator configuration in bot_config.json")
        
        if (ssid_result.get("valid") and connection_result.get("success") and 
            connection_result.get("balance_retrieved") and amount_result.get("configured")):
            print("✅ All systems working correctly - ready for real account trading!")
        
        print("="*60)

def main():
    """Main function to run the real account fix."""
    print("🔧 Real Account Configuration Fix Tool")
    print("="*50)
    
    fixer = RealAccountFixer()
    results = fixer.run_comprehensive_fix()
    fixer.print_summary(results)
    
    # Cleanup
    if fixer.client:
        try:
            fixer.client.close()
        except:
            pass

if __name__ == "__main__":
    main()
