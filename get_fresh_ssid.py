#!/usr/bin/env python3
"""
Fresh SSID Retrieval Tool for Self Bot v3.0
===========================================

This script helps you retrieve a fresh Socket.IO SSID from your Pocket Option browser session.

Usage:
    1. Login to Pocket Option in your browser
    2. Open Developer Tools (F12)
    3. Go to Network tab
    4. Look for WebSocket connections to socket.io
    5. Copy the auth message and paste it when prompted
    6. This script will extract and save the SSID

Alternative:
    python get_fresh_ssid.py --manual "your_auth_payload_here"
"""

import json
import os
import re
import argparse
import logging
from datetime import datetime
from typing import Optional, Dict, Any

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SSIDExtractor:
    """Extract and manage Pocket Option SSIDs"""
    
    def __init__(self):
        self.config_file = "config/pocket_option_config.json"
        self.backup_dir = "data/ssid_backups"
        
        # Ensure directories exist
        os.makedirs("config", exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def extract_ssid_from_auth_payload(self, auth_payload: str) -> Optional[Dict[str, Any]]:
        """
        Extract SSID information from Socket.IO auth payload.
        
        Args:
            auth_payload: The Socket.IO auth message from browser
            
        Returns:
            Dict with extracted information or None if failed
        """
        try:
            # Clean up the payload
            auth_payload = auth_payload.strip()
            
            # Handle different formats
            if auth_payload.startswith('42["auth",'):
                # Standard Socket.IO format
                json_part = auth_payload[2:]  # Remove '42' prefix
                data = json.loads(json_part)
                
                if len(data) >= 2 and data[0] == "auth":
                    auth_data = data[1]
                    
                    return {
                        "full_ssid": auth_payload,
                        "session": auth_data.get("session"),
                        "isDemo": auth_data.get("isDemo", 0),
                        "uid": auth_data.get("uid"),
                        "platform": auth_data.get("platform"),
                        "extracted_at": datetime.now().isoformat()
                    }
            
            elif '"session":' in auth_payload:
                # Try to extract session directly
                session_match = re.search(r'"session":"([^"]+)"', auth_payload)
                if session_match:
                    session = session_match.group(1)
                    
                    # Try to extract other fields
                    uid_match = re.search(r'"uid":(\d+)', auth_payload)
                    demo_match = re.search(r'"isDemo":(\d+)', auth_payload)
                    platform_match = re.search(r'"platform":(\d+)', auth_payload)
                    
                    return {
                        "full_ssid": auth_payload if auth_payload.startswith('42[') else f'42["auth",{auth_payload}]',
                        "session": session,
                        "isDemo": int(demo_match.group(1)) if demo_match else 0,
                        "uid": int(uid_match.group(1)) if uid_match else None,
                        "platform": int(platform_match.group(1)) if platform_match else 9,
                        "extracted_at": datetime.now().isoformat()
                    }
            
            logger.error("Could not parse auth payload format")
            return None
            
        except Exception as e:
            logger.error(f"Error extracting SSID: {e}")
            return None
    
    def backup_current_config(self) -> bool:
        """Backup current configuration before updating"""
        try:
            if os.path.exists(self.config_file):
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_file = os.path.join(self.backup_dir, f"pocket_option_config_backup_{timestamp}.json")
                
                with open(self.config_file, 'r') as src:
                    with open(backup_file, 'w') as dst:
                        dst.write(src.read())
                
                logger.info(f"✅ Backed up current config to: {backup_file}")
                return True
        except Exception as e:
            logger.error(f"Error backing up config: {e}")
        return False
    
    def load_current_config(self) -> Dict[str, Any]:
        """Load current configuration"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"Error loading config: {e}")
        
        # Return default config
        return {
            "ssid": "",
            "is_demo": False,
            "min_payout": 80,
            "preferred_assets": [
                "EURUSD", "GBPUSD", "USDJPY", "AUDUSD", "USDCAD",
                "NZDUSD", "USDCHF", "EURJPY", "GBPJPY", "EURGBP"
            ],
            "otc_preferred": True,
            "connection_timeout": 30,
            "reconnect_attempts": 5,
            "reconnect_delay": 5
        }
    
    def update_config_with_ssid(self, ssid_info: Dict[str, Any]) -> bool:
        """Update configuration with new SSID"""
        try:
            # Backup current config
            self.backup_current_config()
            
            # Load current config
            config = self.load_current_config()
            
            # Update with new SSID
            config["ssid"] = ssid_info["full_ssid"]
            config["is_demo"] = bool(ssid_info["isDemo"])
            
            # Add metadata
            config["ssid_metadata"] = {
                "extracted_at": ssid_info["extracted_at"],
                "uid": ssid_info["uid"],
                "platform": ssid_info["platform"],
                "session_id": self.extract_session_id(ssid_info["session"]) if ssid_info["session"] else None
            }
            
            # Save updated config
            with open(self.config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            logger.info(f"✅ Updated configuration with new SSID")
            logger.info(f"   Demo Mode: {config['is_demo']}")
            logger.info(f"   UID: {ssid_info['uid']}")
            logger.info(f"   Platform: {ssid_info['platform']}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating config: {e}")
            return False
    
    def extract_session_id(self, session_string: str) -> Optional[str]:
        """Extract session ID from session string"""
        try:
            # Look for session_id in the session string
            match = re.search(r'session_id[^:]*:s:32:"([^"]+)"', session_string)
            if match:
                return match.group(1)
        except:
            pass
        return None
    
    def validate_ssid(self, ssid_info: Dict[str, Any]) -> bool:
        """Validate extracted SSID information"""
        required_fields = ["full_ssid", "session"]
        
        for field in required_fields:
            if not ssid_info.get(field):
                logger.error(f"Missing required field: {field}")
                return False
        
        # Check SSID format
        if not ssid_info["full_ssid"].startswith('42["auth",'):
            logger.error("SSID does not have correct Socket.IO format")
            return False
        
        logger.info("✅ SSID validation passed")
        return True
    
    def interactive_ssid_input(self) -> Optional[str]:
        """Interactive SSID input with instructions"""
        print("\n" + "="*60)
        print("🔍 FRESH SSID EXTRACTION GUIDE")
        print("="*60)
        print()
        print("To get a fresh SSID from your browser:")
        print()
        print("1. 🌐 Open Pocket Option in your browser and login")
        print("2. 🔧 Press F12 to open Developer Tools")
        print("3. 📡 Go to the 'Network' tab")
        print("4. 🔄 Refresh the page or navigate around")
        print("5. 🔍 Look for WebSocket connections (filter by 'WS')")
        print("6. 📨 Find socket.io connection and look for auth messages")
        print("7. 📋 Copy the auth message that looks like:")
        print("   42[\"auth\",{\"session\":\"...\",\"isDemo\":0,\"uid\":...}]")
        print()
        print("Alternative: Look in Console tab for auth messages")
        print()
        print("="*60)
        print()
        
        try:
            auth_payload = input("📋 Paste the auth payload here (or 'quit' to exit): ").strip()
            
            if auth_payload.lower() in ['quit', 'exit', 'q']:
                return None
            
            if not auth_payload:
                print("❌ No payload provided")
                return None
            
            return auth_payload
            
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return None
    
    def process_ssid(self, auth_payload: str) -> bool:
        """Process and save SSID"""
        print(f"\n🔍 Processing auth payload...")
        print(f"   Length: {len(auth_payload)} characters")
        print(f"   Preview: {auth_payload[:50]}...")
        
        # Extract SSID information
        ssid_info = self.extract_ssid_from_auth_payload(auth_payload)
        
        if not ssid_info:
            print("❌ Failed to extract SSID information")
            return False
        
        # Validate SSID
        if not self.validate_ssid(ssid_info):
            print("❌ SSID validation failed")
            return False
        
        # Display extracted information
        print("\n✅ SSID EXTRACTED SUCCESSFULLY:")
        print(f"   Demo Mode: {'Yes' if ssid_info['isDemo'] else 'No'}")
        print(f"   User ID: {ssid_info['uid']}")
        print(f"   Platform: {ssid_info['platform']}")
        print(f"   Session ID: {self.extract_session_id(ssid_info['session']) if ssid_info['session'] else 'Not found'}")
        
        # Ask for confirmation
        try:
            confirm = input("\n💾 Save this SSID to configuration? (y/N): ").strip().lower()
            if confirm in ['y', 'yes']:
                if self.update_config_with_ssid(ssid_info):
                    print("✅ SSID saved successfully!")
                    print(f"📁 Configuration updated: {self.config_file}")
                    return True
                else:
                    print("❌ Failed to save SSID")
                    return False
            else:
                print("❌ SSID not saved")
                return False
                
        except KeyboardInterrupt:
            print("\n❌ Cancelled by user")
            return False


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Fresh SSID Retrieval Tool for Self Bot v3.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python get_fresh_ssid.py
  python get_fresh_ssid.py --manual "42[\"auth\",{...}]"
        """
    )
    
    parser.add_argument('--manual', type=str, help='Manually provide auth payload')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Create extractor
    extractor = SSIDExtractor()
    
    try:
        if args.manual:
            # Manual mode
            success = extractor.process_ssid(args.manual)
        else:
            # Interactive mode
            auth_payload = extractor.interactive_ssid_input()
            if auth_payload:
                success = extractor.process_ssid(auth_payload)
            else:
                success = False
        
        if success:
            print("\n🎉 SSID EXTRACTION COMPLETE!")
            print("\n📋 Next steps:")
            print("   1. Test the new SSID: python test_ssid_fixed.py")
            print("   2. Start a session: python session_control.py --start --name 'fresh_session'")
            print("   3. Run the bot: python self_bot_v3_integrated.py --verbose")
        else:
            print("\n❌ SSID extraction failed")
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Process cancelled by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"\n❌ Error: {e}")


if __name__ == "__main__":
    main()
