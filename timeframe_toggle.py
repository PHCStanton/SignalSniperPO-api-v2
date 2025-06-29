#!/usr/bin/env python3
"""
Timeframe Toggle Script for SignalSniper Bot
============================================

Interactive script to manage timeframe suspension for the SignalSniper trading bot.
Allows users to enable/disable specific timeframes with manual review and confirmation.

Features:
- Interactive timeframe selection
- Manual review of current settings
- Backup creation before changes
- Real-time configuration updates
- Integration with both SignalSniper.py and SignalSniper_mod.py

Usage:
    python timeframe_toggle.py
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, List, Set
import shutil

class TimeframeToggle:
    def __init__(self):
        self.config_path = "config/timeframe_config.json"
        self.backup_dir = "config/backups"
        self.config = self.load_config()
        
    def load_config(self) -> Dict:
        """Load timeframe configuration from file."""
        try:
            if not os.path.exists(self.config_path):
                print(f"❌ Configuration file not found: {self.config_path}")
                return self.create_default_config()
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Create default timeframe configuration."""
        return {
            "timeframe_control": {
                "enabled": True,
                "description": "Timeframe suspension control for SignalSniper bot",
                "default_enabled_timeframes": [1, 3, 5],
                "available_timeframes": [1, 2, 3, 4, 5, 10, 15, 30, 60],
                "suspended_timeframes": [],
                "last_updated": datetime.now().isoformat(),
                "updated_by": "timeframe_toggle_system"
            },
            "timeframe_settings": {
                str(tf): {
                    "enabled": tf in [1, 3, 5],
                    "description": f"{tf}-minute signals",
                    "typical_channels": ["Generic"],
                    "optimization_available": tf == 1
                } for tf in [1, 2, 3, 4, 5, 10, 15, 30, 60]
            },
            "suspension_rules": {
                "manual_review_required": True,
                "prompt_user_for_suspension": True,
                "allow_runtime_changes": True,
                "backup_before_changes": True,
                "log_all_changes": True
            }
        }
    
    def save_config(self) -> bool:
        """Save configuration to file with backup."""
        try:
            # Create backup if enabled
            if self.config.get("suspension_rules", {}).get("backup_before_changes", True):
                self.create_backup()
            
            # Update timestamp
            self.config["timeframe_control"]["last_updated"] = datetime.now().isoformat()
            
            # Save configuration
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4)
            
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def create_backup(self):
        """Create backup of current configuration."""
        try:
            os.makedirs(self.backup_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = os.path.join(self.backup_dir, f"timeframe_config_backup_{timestamp}.json")
            shutil.copy2(self.config_path, backup_path)
            print(f"📁 Backup created: {backup_path}")
        except Exception as e:
            print(f"⚠️ Warning: Could not create backup: {e}")
    
    def display_current_status(self):
        """Display current timeframe status."""
        print("\n" + "="*60)
        print("📊 CURRENT TIMEFRAME STATUS")
        print("="*60)
        
        control = self.config.get("timeframe_control", {})
        settings = self.config.get("timeframe_settings", {})
        
        print(f"🔧 System Status: {'✅ ENABLED' if control.get('enabled', False) else '❌ DISABLED'}")
        print(f"📅 Last Updated: {control.get('last_updated', 'Unknown')}")
        print(f"👤 Updated By: {control.get('updated_by', 'Unknown')}")
        
        print(f"\n🎯 DEFAULT ENABLED TIMEFRAMES: {control.get('default_enabled_timeframes', [])}")
        print(f"🚫 SUSPENDED TIMEFRAMES: {control.get('suspended_timeframes', [])}")
        
        print("\n📋 DETAILED TIMEFRAME STATUS:")
        print("-" * 60)
        
        for timeframe in sorted([int(k) for k in settings.keys()]):
            tf_str = str(timeframe)
            tf_config = settings.get(tf_str, {})
            enabled = tf_config.get("enabled", False)
            status = "✅ ENABLED" if enabled else "❌ DISABLED"
            description = tf_config.get("description", f"{timeframe}-minute signals")
            channels = ", ".join(tf_config.get("typical_channels", ["Generic"]))
            optimization = "🚀 59s Opt" if tf_config.get("optimization_available", False) else ""
            
            print(f"  {timeframe:2d} min: {status:12} | {description:20} | Channels: {channels:25} {optimization}")
        
        # Display BinaryPulse bot specific settings
        self.display_binarypulse_status()
    
    def display_binarypulse_status(self):
        """Display BinaryPulse bot specific timeframe status."""
        channel_specific = self.config.get("channel_specific", {})
        binarypulse_config = channel_specific.get("binarypulse_bot", {})
        
        if not binarypulse_config:
            return
            
        print("\n🤖 BINARYPULSE BOT SPECIFIC SETTINGS:")
        print("-" * 60)
        
        override_global = binarypulse_config.get("override_global", False)
        print(f"🔄 Override Global: {'✅ YES' if override_global else '❌ NO (uses global settings)'}")
        
        if override_global:
            bp_timeframes = binarypulse_config.get("timeframes", {})
            for tf in ["1", "3", "5"]:
                if tf in bp_timeframes:
                    tf_config = bp_timeframes[tf]
                    enabled = tf_config.get("enabled", False)
                    priority = tf_config.get("priority", "medium")
                    status = "✅ ENABLED" if enabled else "❌ DISABLED"
                    print(f"  🤖 {tf} min: {status:12} | Priority: {priority:8} | BinaryPulse Bot")
        
        filtering_rules = binarypulse_config.get("filtering_rules", {})
        if filtering_rules:
            print(f"\n📊 BinaryPulse Filtering Rules:")
            print(f"  🎯 Filter by Duration: {'✅' if filtering_rules.get('filter_by_duration', False) else '❌'}")
            print(f"  🚫 Skip Disabled: {'✅' if filtering_rules.get('skip_disabled_timeframes', False) else '❌'}")
            print(f"  📝 Log Filtered: {'✅' if filtering_rules.get('log_filtered_signals', False) else '❌'}")
            print(f"  📈 Statistical Tracking: {'✅' if filtering_rules.get('statistical_tracking', False) else '❌'}")
    
    def get_enabled_timeframes(self) -> Set[int]:
        """Get currently enabled timeframes."""
        settings = self.config.get("timeframe_settings", {})
        return {int(tf) for tf, config in settings.items() if config.get("enabled", False)}
    
    def get_suspended_timeframes(self) -> Set[int]:
        """Get currently suspended timeframes."""
        return set(self.config.get("timeframe_control", {}).get("suspended_timeframes", []))
    
    def prompt_timeframe_suspension(self) -> List[int]:
        """Prompt user for timeframes to suspend."""
        print("\n" + "="*60)
        print("🔧 TIMEFRAME SUSPENSION CONFIGURATION")
        print("="*60)
        
        enabled_timeframes = self.get_enabled_timeframes()
        print(f"\n📊 Currently Enabled Timeframes: {sorted(enabled_timeframes)}")
        
        if not enabled_timeframes:
            print("⚠️ No timeframes are currently enabled!")
            return []
        
        print("\n❓ Which Timeframes should be suspended:")
        print("   (Enter timeframe numbers separated by commas, or 'none' for no changes)")
        print("   (Example: 1,2,5 or none)")
        
        while True:
            try:
                user_input = input("\n🎯 Enter timeframes to suspend: ").strip().lower()
                
                if user_input in ['none', 'n', '']:
                    return []
                
                # Parse comma-separated timeframes
                timeframes_to_suspend = []
                for tf_str in user_input.split(','):
                    tf_str = tf_str.strip()
                    if tf_str.isdigit():
                        tf = int(tf_str)
                        if tf in enabled_timeframes:
                            timeframes_to_suspend.append(tf)
                        else:
                            print(f"⚠️ Warning: {tf} is not currently enabled")
                    else:
                        print(f"❌ Invalid timeframe: {tf_str}")
                        continue
                
                if timeframes_to_suspend:
                    print(f"\n📋 Timeframes to suspend: {sorted(timeframes_to_suspend)}")
                    confirm = input("✅ Confirm suspension? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        return timeframes_to_suspend
                    else:
                        print("❌ Suspension cancelled")
                        continue
                else:
                    return []
                    
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                return []
            except Exception as e:
                print(f"❌ Error: {e}")
                continue
    
    def apply_timeframe_suspension(self, timeframes_to_suspend: List[int]) -> bool:
        """Apply timeframe suspension changes."""
        try:
            settings = self.config.get("timeframe_settings", {})
            control = self.config.get("timeframe_control", {})
            
            # Update individual timeframe settings
            for tf in timeframes_to_suspend:
                tf_str = str(tf)
                if tf_str in settings:
                    settings[tf_str]["enabled"] = False
                    print(f"🚫 Suspended: {tf}-minute signals")
            
            # Update suspended timeframes list
            current_suspended = set(control.get("suspended_timeframes", []))
            current_suspended.update(timeframes_to_suspend)
            control["suspended_timeframes"] = sorted(current_suspended)
            
            # Update timestamp and user
            control["last_updated"] = datetime.now().isoformat()
            control["updated_by"] = "manual_timeframe_toggle"
            
            return True
            
        except Exception as e:
            print(f"❌ Error applying suspension: {e}")
            return False
    
    def enable_timeframe(self, timeframe: int) -> bool:
        """Enable a specific timeframe."""
        try:
            settings = self.config.get("timeframe_settings", {})
            control = self.config.get("timeframe_control", {})
            
            tf_str = str(timeframe)
            if tf_str in settings:
                settings[tf_str]["enabled"] = True
                
                # Remove from suspended list
                suspended = set(control.get("suspended_timeframes", []))
                suspended.discard(timeframe)
                control["suspended_timeframes"] = sorted(suspended)
                
                print(f"✅ Enabled: {timeframe}-minute signals")
                return True
            else:
                print(f"❌ Timeframe {timeframe} not found in configuration")
                return False
                
        except Exception as e:
            print(f"❌ Error enabling timeframe: {e}")
            return False
    
    def interactive_menu(self):
        """Main interactive menu."""
        while True:
            print("\n" + "="*60)
            print("🎯 SIGNALSNIPER TIMEFRAME TOGGLE CONTROL")
            print("="*60)
            print("1. 📊 View Current Status")
            print("2. 🚫 Suspend Timeframes")
            print("3. ✅ Enable Timeframe")
            print("4. 🔄 Reset to Defaults")
            print("5. 💾 Save & Exit")
            print("6. ❌ Exit Without Saving")
            print("-" * 60)
            
            try:
                choice = input("🎯 Select option (1-6): ").strip()
                
                if choice == '1':
                    self.display_current_status()
                    
                elif choice == '2':
                    timeframes_to_suspend = self.prompt_timeframe_suspension()
                    if timeframes_to_suspend:
                        if self.apply_timeframe_suspension(timeframes_to_suspend):
                            print(f"✅ Successfully suspended timeframes: {timeframes_to_suspend}")
                        else:
                            print("❌ Failed to apply suspension")
                    else:
                        print("ℹ️ No timeframes suspended")
                        
                elif choice == '3':
                    suspended = self.get_suspended_timeframes()
                    if not suspended:
                        print("ℹ️ No timeframes are currently suspended")
                        continue
                        
                    print(f"\n🚫 Currently Suspended: {sorted(suspended)}")
                    try:
                        tf_input = input("✅ Enter timeframe to enable: ").strip()
                        if tf_input.isdigit():
                            tf = int(tf_input)
                            if tf in suspended:
                                self.enable_timeframe(tf)
                            else:
                                print(f"❌ Timeframe {tf} is not suspended")
                        else:
                            print("❌ Invalid timeframe number")
                    except ValueError:
                        print("❌ Invalid input")
                        
                elif choice == '4':
                    confirm = input("🔄 Reset to default timeframes (1,3,5)? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        self.reset_to_defaults()
                        print("✅ Reset to default configuration")
                    else:
                        print("❌ Reset cancelled")
                        
                elif choice == '5':
                    if self.save_config():
                        print("✅ Configuration saved successfully!")
                        print("🔄 Restart SignalSniper bot for changes to take effect")
                        break
                    else:
                        print("❌ Failed to save configuration")
                        
                elif choice == '6':
                    confirm = input("❌ Exit without saving changes? (y/n): ").strip().lower()
                    if confirm in ['y', 'yes']:
                        print("❌ Exiting without saving")
                        break
                    else:
                        continue
                        
                else:
                    print("❌ Invalid option. Please select 1-6.")
                    
            except KeyboardInterrupt:
                print("\n❌ Operation cancelled by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
    
    def reset_to_defaults(self):
        """Reset timeframes to default configuration."""
        default_enabled = [1, 3, 5]
        settings = self.config.get("timeframe_settings", {})
        control = self.config.get("timeframe_control", {})
        
        # Reset all timeframes
        for tf_str, tf_config in settings.items():
            tf = int(tf_str)
            tf_config["enabled"] = tf in default_enabled
        
        # Clear suspended list
        control["suspended_timeframes"] = []
        control["default_enabled_timeframes"] = default_enabled
        control["last_updated"] = datetime.now().isoformat()
        control["updated_by"] = "reset_to_defaults"

def main():
    """Main function."""
    print("🎯 SignalSniper Timeframe Toggle Control")
    print("=" * 50)
    
    try:
        toggle = TimeframeToggle()
        toggle.interactive_menu()
        
    except KeyboardInterrupt:
        print("\n❌ Program interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
