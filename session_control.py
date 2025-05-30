#!/usr/bin/env python3
"""
Self Bot v3.0 - Session Control Manager
=====================================

Complete session management tool for Self Bot v3.0
Provides full control over trading sessions with easy commands.

Usage:
    python session_control.py --help
    python session_control.py --status
    python session_control.py --start --name "morning_session"
    python session_control.py --stop
    python session_control.py --clear-all
"""

import json
import os
import sys
import argparse
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import pytz

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SessionController:
    """Advanced session management for Self Bot v3.0"""
    
    def __init__(self):
        self.data_dir = "data"
        self.config_dir = "config"
        self.sessions_dir = "sessions"
        
        # Session files in dedicated sessions folder
        self.active_session_file = os.path.join(self.sessions_dir, "active_session.json")
        self.recovery_file = os.path.join(self.sessions_dir, "session_recovery.json")
        self.sessions_file = os.path.join(self.sessions_dir, "sessions.json")
        self.session_data_file = os.path.join(self.sessions_dir, "session_data.json")
        
        # Config files
        self.bot_config_file = os.path.join(self.config_dir, "bot_config.json")
        self.pocket_config_file = os.path.join(self.config_dir, "pocket_option_config.json")
        
        # Timezone
        self.tz = pytz.timezone('Africa/Johannesburg')
        
        # Ensure directories exist
        os.makedirs(self.data_dir, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        os.makedirs(self.sessions_dir, exist_ok=True)
    
    def get_current_time(self) -> str:
        """Get current time in SAST timezone"""
        return datetime.now(self.tz).isoformat()
    
    def load_json_file(self, filepath: str, default: Any = None) -> Any:
        """Safely load JSON file"""
        if default is None:
            default = {}
        
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:
                        return json.loads(content)
            return default
        except Exception as e:
            logger.warning(f"Error loading {filepath}: {e}")
            return default
    
    def save_json_file(self, filepath: str, data: Any) -> bool:
        """Safely save JSON file"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            logger.error(f"Error saving {filepath}: {e}")
            return False
    
    def migrate_old_sessions(self):
        """Migrate session files from data/ to sessions/ folder"""
        old_files = {
            "active_session.json": os.path.join(self.data_dir, "active_session.json"),
            "session_recovery.json": os.path.join(self.data_dir, "session_recovery.json"),
            "sessions.json": os.path.join(self.data_dir, "sessions.json"),
            "session_data.json": os.path.join(self.data_dir, "session_data.json")
        }
        
        migrated = False
        for filename, old_path in old_files.items():
            if os.path.exists(old_path):
                new_path = os.path.join(self.sessions_dir, filename)
                try:
                    # Copy data to new location
                    data = self.load_json_file(old_path)
                    if data:
                        self.save_json_file(new_path, data)
                        logger.info(f"Migrated {filename} to sessions folder")
                        migrated = True
                    
                    # Remove old file
                    os.remove(old_path)
                except Exception as e:
                    logger.warning(f"Error migrating {filename}: {e}")
        
        if migrated:
            logger.info("✅ Session migration completed")
    
    def get_session_status(self) -> Dict[str, Any]:
        """Get current session status"""
        # Migrate old sessions if needed
        self.migrate_old_sessions()
        
        active_session = self.load_json_file(self.active_session_file)
        recovery_data = self.load_json_file(self.recovery_file)
        sessions_data = self.load_json_file(self.sessions_file, [])
        
        # Count today's sessions
        today = datetime.now(self.tz).date().isoformat()
        today_sessions = [s for s in sessions_data if s.get('date', '').startswith(today)]
        
        return {
            "has_active_session": bool(active_session),
            "active_session": active_session,
            "has_recovery_data": bool(recovery_data),
            "recovery_data": recovery_data,
            "total_sessions": len(sessions_data),
            "today_sessions": len(today_sessions),
            "today_sessions_list": today_sessions
        }
    
    def start_session(self, session_name: Optional[str] = None, force: bool = False) -> bool:
        """Start a new trading session"""
        status = self.get_session_status()
        
        # Check for existing active session
        if status["has_active_session"] and not force:
            logger.error(f"Active session already exists: {status['active_session'].get('session_id', 'unknown')}")
            logger.info("Use --force to override or --stop to end current session")
            return False
        
        # Generate session name if not provided
        if not session_name:
            timestamp = datetime.now(self.tz).strftime("%Y%m%d_%H%M%S")
            session_name = f"session_{timestamp}"
        
        # Create new session
        session_id = session_name
        current_time = self.get_current_time()
        
        session_data = {
            "session_id": session_id,
            "start_time": current_time,
            "status": "active",
            "trades_count": 0,
            "signals_count": 0,
            "balance_start": 0.0,
            "profit_loss": 0.0,
            "wins": 0,
            "losses": 0,
            "draws": 0,
            "errors": 0,
            "created_by": "session_control",
            "last_update": current_time
        }
        
        # Save active session
        if not self.save_json_file(self.active_session_file, session_data):
            return False
        
        # Clear recovery data
        self.save_json_file(self.recovery_file, {})
        
        # Add to sessions history
        sessions_data = self.load_json_file(self.sessions_file, [])
        sessions_data.append({
            "session_id": session_id,
            "start_time": current_time,
            "date": datetime.now(self.tz).date().isoformat(),
            "status": "active"
        })
        self.save_json_file(self.sessions_file, sessions_data)
        
        logger.info(f"✅ Started new session: {session_id}")
        return True
    
    def stop_session(self, force: bool = False) -> bool:
        """Stop the current active session"""
        status = self.get_session_status()
        
        if not status["has_active_session"]:
            logger.warning("No active session to stop")
            return True
        
        session_data = status["active_session"]
        session_id = session_data.get("session_id", "unknown")
        current_time = self.get_current_time()
        
        # Update session end time
        session_data["end_time"] = current_time
        session_data["status"] = "completed"
        session_data["last_update"] = current_time
        
        # Update sessions history
        sessions_data = self.load_json_file(self.sessions_file, [])
        for session in sessions_data:
            if session.get("session_id") == session_id:
                session["end_time"] = current_time
                session["status"] = "completed"
                break
        
        self.save_json_file(self.sessions_file, sessions_data)
        
        # Clear active session
        self.save_json_file(self.active_session_file, {})
        
        # Clear recovery data
        self.save_json_file(self.recovery_file, {})
        
        logger.info(f"✅ Stopped session: {session_id}")
        return True
    
    def clear_sessions(self, scope: str = "all") -> bool:
        """Clear session data based on scope"""
        current_time = self.get_current_time()
        
        if scope == "all":
            # Clear everything
            self.save_json_file(self.active_session_file, {})
            self.save_json_file(self.recovery_file, {})
            self.save_json_file(self.sessions_file, [])
            if os.path.exists(self.session_data_file):
                os.remove(self.session_data_file)
            logger.info("✅ Cleared all session data")
            
        elif scope == "today":
            # Clear only today's sessions
            today = datetime.now(self.tz).date().isoformat()
            sessions_data = self.load_json_file(self.sessions_file, [])
            
            # Keep sessions not from today
            filtered_sessions = [s for s in sessions_data if not s.get('date', '').startswith(today)]
            self.save_json_file(self.sessions_file, filtered_sessions)
            
            # Clear active session if it's from today
            active_session = self.load_json_file(self.active_session_file)
            if active_session:
                session_date = active_session.get('start_time', '')[:10]
                if session_date == today:
                    self.save_json_file(self.active_session_file, {})
                    self.save_json_file(self.recovery_file, {})
            
            logger.info("✅ Cleared today's session data")
            
        elif scope == "recovery":
            # Clear only recovery data
            self.save_json_file(self.recovery_file, {})
            logger.info("✅ Cleared session recovery data")
            
        return True
    
    def list_sessions(self, today_only: bool = False) -> List[Dict[str, Any]]:
        """List sessions"""
        sessions_data = self.load_json_file(self.sessions_file, [])
        
        if today_only:
            today = datetime.now(self.tz).date().isoformat()
            sessions_data = [s for s in sessions_data if s.get('date', '').startswith(today)]
        
        return sessions_data
    
    def get_session_report(self, session_name: Optional[str] = None) -> Dict[str, Any]:
        """Generate session report"""
        if session_name:
            # Specific session report
            sessions_data = self.load_json_file(self.sessions_file, [])
            session = next((s for s in sessions_data if s.get('session_id') == session_name), None)
            if not session:
                return {"error": f"Session '{session_name}' not found"}
            return session
        else:
            # Current session report
            status = self.get_session_status()
            if not status["has_active_session"]:
                return {"error": "No active session"}
            return status["active_session"]
    
    def update_ssid(self, new_ssid: str) -> bool:
        """Update SSID in pocket option config"""
        try:
            config = self.load_json_file(self.pocket_config_file, {})
            config["ssid"] = new_ssid
            config["last_updated"] = self.get_current_time()
            
            if self.save_json_file(self.pocket_config_file, config):
                logger.info("✅ Updated SSID in configuration")
                return True
            return False
        except Exception as e:
            logger.error(f"Error updating SSID: {e}")
            return False
    
    def set_session_limit(self, limit: int) -> bool:
        """Set daily session limit"""
        try:
            config = self.load_json_file(self.bot_config_file, {})
            if "session_management" not in config:
                config["session_management"] = {}
            
            config["session_management"]["daily_session_limit"] = limit
            config["session_management"]["last_updated"] = self.get_current_time()
            
            if self.save_json_file(self.bot_config_file, config):
                logger.info(f"✅ Set daily session limit to: {limit}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error setting session limit: {e}")
            return False
    
    def print_status(self):
        """Print detailed session status"""
        status = self.get_session_status()
        
        print("\n" + "="*60)
        print("🎯 SELF BOT v3.0 - SESSION STATUS")
        print("="*60)
        print(f"📁 Sessions Directory: {self.sessions_dir}/")
        print()
        
        # Active session
        if status["has_active_session"]:
            session = status["active_session"]
            print(f"📍 ACTIVE SESSION: {session.get('session_id', 'unknown')}")
            print(f"   Started: {session.get('start_time', 'unknown')}")
            print(f"   Trades: {session.get('trades_count', 0)}")
            print(f"   Signals: {session.get('signals_count', 0)}")
            print(f"   Status: ✅ RUNNING")
        else:
            print("📍 ACTIVE SESSION: None")
            print("   Status: ⭕ NO ACTIVE SESSION")
        
        print()
        
        # Recovery data
        if status["has_recovery_data"]:
            recovery = status["recovery_data"]
            print(f"🔄 RECOVERY DATA: Available")
            print(f"   Session: {recovery.get('session_id', 'unknown')}")
        else:
            print("🔄 RECOVERY DATA: None")
        
        print()
        
        # Session counts
        print(f"📊 SESSION STATISTICS:")
        print(f"   Total Sessions: {status['total_sessions']}")
        print(f"   Today's Sessions: {status['today_sessions']}")
        
        # Today's sessions
        if status["today_sessions_list"]:
            print(f"\n📅 TODAY'S SESSIONS:")
            for session in status["today_sessions_list"]:
                status_icon = "✅" if session.get('status') == 'completed' else "🔄"
                print(f"   {status_icon} {session.get('session_id', 'unknown')} - {session.get('start_time', 'unknown')}")
        
        print("\n" + "="*60)
    
    def print_help(self):
        """Print help information"""
        print("\n" + "="*60)
        print("🎯 SELF BOT v3.0 - SESSION CONTROL HELP")
        print("="*60)
        print()
        print("📋 QUICK COMMANDS:")
        print("   python session_control.py --status")
        print("   python session_control.py --start --name 'morning_session'")
        print("   python session_control.py --stop")
        print("   python session_control.py --clear-all")
        print()
        print("📅 DAILY WORKFLOW:")
        print("   1. python session_control.py --clear-today")
        print("   2. python session_control.py --start --name 'morning_session'")
        print("   3. python self_bot_v3_integrated.py --verbose")
        print("   4. python session_control.py --stop")
        print()
        print("🚨 EMERGENCY:")
        print("   python session_control.py --nuclear-reset")
        print()
        print("📖 Full documentation: docs/SESSION_MANAGEMENT_GUIDE.md")
        print("="*60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Self Bot v3.0 Session Control Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python session_control.py --status
  python session_control.py --start --name "morning_session"
  python session_control.py --stop
  python session_control.py --clear-all
  python session_control.py --list --today
        """
    )
    
    # Main actions
    parser.add_argument('--status', action='store_true', help='Show session status')
    parser.add_argument('--start', action='store_true', help='Start new session')
    parser.add_argument('--stop', action='store_true', help='Stop current session')
    parser.add_argument('--list', action='store_true', help='List sessions')
    parser.add_argument('--report', action='store_true', help='Show session report')
    
    # Session management
    parser.add_argument('--name', type=str, help='Session name')
    parser.add_argument('--force', action='store_true', help='Force action')
    parser.add_argument('--today', action='store_true', help='Today only')
    
    # Clear operations
    parser.add_argument('--clear-all', action='store_true', help='Clear all session data')
    parser.add_argument('--clear-today', action='store_true', help='Clear today\'s sessions')
    parser.add_argument('--clear-recovery', action='store_true', help='Clear recovery data')
    parser.add_argument('--nuclear-reset', action='store_true', help='Nuclear reset - clear everything')
    
    # Configuration
    parser.add_argument('--update-ssid', type=str, help='Update SSID in config')
    parser.add_argument('--set-limit', type=int, help='Set daily session limit')
    
    # Force stop
    parser.add_argument('--force-stop', action='store_true', help='Force stop session')
    
    args = parser.parse_args()
    
    # Create session controller
    controller = SessionController()
    
    # Handle no arguments - show help
    if len(sys.argv) == 1:
        controller.print_help()
        return
    
    # Execute commands
    try:
        if args.status:
            controller.print_status()
            
        elif args.start:
            success = controller.start_session(args.name, args.force)
            if not success:
                sys.exit(1)
                
        elif args.stop or args.force_stop:
            controller.stop_session(args.force_stop)
            
        elif args.clear_all or args.nuclear_reset:
            controller.clear_sessions("all")
            
        elif args.clear_today:
            controller.clear_sessions("today")
            
        elif args.clear_recovery:
            controller.clear_sessions("recovery")
            
        elif args.list:
            sessions = controller.list_sessions(args.today)
            if sessions:
                print(f"\n📋 SESSIONS ({'Today' if args.today else 'All'}):")
                for session in sessions:
                    status_icon = "✅" if session.get('status') == 'completed' else "🔄"
                    print(f"   {status_icon} {session.get('session_id', 'unknown')} - {session.get('start_time', 'unknown')}")
            else:
                print(f"\n📋 No sessions found ({'today' if args.today else 'total'})")
                
        elif args.report:
            report = controller.get_session_report(args.name)
            if "error" in report:
                print(f"❌ {report['error']}")
            else:
                print(f"\n📊 SESSION REPORT:")
                for key, value in report.items():
                    print(f"   {key}: {value}")
                    
        elif args.update_ssid:
            controller.update_ssid(args.update_ssid)
            
        elif args.set_limit is not None:
            controller.set_session_limit(args.set_limit)
            
        else:
            controller.print_help()
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
