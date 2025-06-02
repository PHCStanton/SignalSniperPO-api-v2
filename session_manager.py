#!/usr/bin/env python3
"""
session_manager.py - Session Management and Signal Deduplication for Self Bot v1.5

This module implements:
1. Session singleton pattern to prevent multiple sessions per day
2. Signal deduplication system with fingerprinting
3. Session recovery mechanism
4. Robust session state management

PHASE 2 IMPLEMENTATION - Session Management and Signal Deduplication
"""
import os
import json
import hashlib
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Any
from dataclasses import dataclass, asdict
import pytz

logger = logging.getLogger(__name__)

@dataclass
class SessionInfo:
    """Session information data class."""
    # Fields without default values
    session_id: str
    start_time: str
    status: str  # 'active', 'completed', 'terminated', 'error'
    trades_count: int
    signals_count: int
    balance_start: float
    profit_loss: float
    wins: int
    losses: int
    draws: int
    errors: int
    last_activity: str
    # Fields with default values
    end_time: Optional[str] = None
    balance_end: Optional[float] = None
    recovery_data: Optional[Dict] = None

class SessionManager:
    """
    Manages trading sessions with singleton pattern and recovery mechanisms.
    Ensures only one active session per day and provides robust session tracking.
    """
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls, *args, **kwargs):
        """Singleton pattern implementation."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(SessionManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self, data_dir: str = "data", timezone: str = "Africa/Johannesburg"):
        """Initialize session manager."""
        if hasattr(self, '_initialized'):
            return
        
        self.data_dir = data_dir
        self.timezone = pytz.timezone(timezone)
        self.sessions_file = os.path.join(data_dir, "sessions.json")
        self.active_session_file = os.path.join(data_dir, "active_session.json")
        self.recovery_file = os.path.join(data_dir, "session_recovery.json")
        
        # Thread safety
        self._session_lock = threading.RLock()
        
        # Current session
        self.current_session: Optional[SessionInfo] = None
        
        # Session limits
        self.max_sessions_per_day = 999  # Effectively unlimited
        self.session_timeout_hours = 24
        
        # Initialize storage
        self._initialize_storage()
        
        # Attempt to load from active_session.json first (for externally started sessions)
        loaded_externally = self._load_from_active_session_file()
        if not loaded_externally:
            # If not loaded from active_session.json, then try recovery file
            self._check_recovery()
        
        self._initialized = True
        logger.info("SessionManager initialized successfully")
    
    def _initialize_storage(self) -> None:
        """Initialize session storage files."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        # Initialize sessions file
        if not os.path.exists(self.sessions_file):
            with open(self.sessions_file, 'w') as f:
                json.dump([], f)
        
        # Initialize active session file
        if not os.path.exists(self.active_session_file):
            with open(self.active_session_file, 'w') as f:
                json.dump({}, f)
        
        # Initialize recovery file
        if not os.path.exists(self.recovery_file):
            with open(self.recovery_file, 'w') as f:
                json.dump({}, f)
    
    def _check_recovery(self) -> None:
        """Check for session recovery data and handle incomplete sessions."""
        try:
            with open(self.recovery_file, 'r') as f:
                recovery_data = json.load(f)
            
            if recovery_data and recovery_data.get('session_id'):
                logger.info(f"Found recovery data for session: {recovery_data['session_id']}")
                
                # Check if session is still valid (within timeout)
                session_start = datetime.fromisoformat(recovery_data['start_time'])
                now = datetime.now(self.timezone)
                
                if (now - session_start).total_seconds() < (self.session_timeout_hours * 3600):
                    logger.info("Attempting session recovery...")
                    self._recover_session(recovery_data)
                else:
                    logger.warning("Recovery session expired, marking as terminated")
                    self._mark_session_terminated(recovery_data['session_id'])
                    self._clear_recovery_data()
        except Exception as e:
            logger.error(f"Error checking recovery: {str(e)}")
    
    def _recover_session(self, recovery_data: Dict) -> bool:
        """Recover an incomplete session."""
        try:
            session_info = SessionInfo(
                session_id=recovery_data['session_id'],
                start_time=recovery_data['start_time'],
                end_time=None,
                status='active',
                trades_count=recovery_data.get('trades_count', 0),
                signals_count=recovery_data.get('signals_count', 0),
                balance_start=recovery_data.get('balance_start', 0.0),
                balance_end=None,
                profit_loss=recovery_data.get('profit_loss', 0.0),
                wins=recovery_data.get('wins', 0),
                losses=recovery_data.get('losses', 0),
                draws=recovery_data.get('draws', 0),
                errors=recovery_data.get('errors', 0),
                last_activity=datetime.now(self.timezone).isoformat(),
                recovery_data=recovery_data
            )
            
            self.current_session = session_info
            self._save_active_session()
            
            logger.info(f"Session recovered successfully: {session_info.session_id}")
            return True
        except Exception as e:
            logger.error(f"Error recovering session: {str(e)}")
            return False
    
    def can_start_new_session(self) -> tuple[bool, str]:
        """Check if a new session can be started today."""
        with self._session_lock:
            try:
                # Check if there's already an active session
                if self.current_session and self.current_session.status == 'active':
                    return False, f"Active session already exists: {self.current_session.session_id}"
                
                # Check daily session limit
                today = datetime.now(self.timezone).date()
                today_sessions = self._get_sessions_for_date(today)
                
                if len(today_sessions) >= self.max_sessions_per_day:
                    return False, f"Daily session limit reached: {len(today_sessions)}/{self.max_sessions_per_day}"
                
                return True, "New session can be started"
            except Exception as e:
                logger.error(f"Error checking session availability: {str(e)}")
                return False, f"Error checking session availability: {str(e)}"
    
    def start_new_session(self, balance_start: float = 0.0) -> Optional[SessionInfo]:
        """Start a new trading session."""
        with self._session_lock:
            try:
                can_start, message = self.can_start_new_session()
                if not can_start:
                    logger.error(f"Cannot start new session: {message}")
                    return None
                
                # Generate session ID
                now = datetime.now(self.timezone)
                session_id = f"session_{now.strftime('%Y%m%d_%H%M%S')}"
                
                # Create session info
                session_info = SessionInfo(
                    session_id=session_id,
                    start_time=now.isoformat(),
                    end_time=None,
                    status='active',
                    trades_count=0,
                    signals_count=0,
                    balance_start=balance_start,
                    balance_end=None,
                    profit_loss=0.0,
                    wins=0,
                    losses=0,
                    draws=0,
                    errors=0,
                    last_activity=now.isoformat(),
                    recovery_data=None
                )
                
                # Set as current session
                self.current_session = session_info
                
                # Save session data
                self._save_session(session_info)
                self._save_active_session()
                self._save_recovery_data()
                
                logger.info(f"New session started: {session_id}")
                return session_info
            except Exception as e:
                logger.error(f"Error starting new session: {str(e)}")
                return None
    
    def update_session(self, **kwargs) -> bool:
        """Update current session data."""
        with self._session_lock:
            try:
                if not self.current_session:
                    logger.error("No active session to update")
                    return False
                
                # Update session fields
                for key, value in kwargs.items():
                    if hasattr(self.current_session, key):
                        setattr(self.current_session, key, value)
                
                # Update last activity
                self.current_session.last_activity = datetime.now(self.timezone).isoformat()
                
                # Save updates
                self._save_session(self.current_session)
                self._save_active_session()
                self._save_recovery_data()
                
                return True
            except Exception as e:
                logger.error(f"Error updating session: {str(e)}")
                return False
    
    def end_session(self, balance_end: Optional[float] = None) -> bool:
        """End the current session."""
        with self._session_lock:
            try:
                if not self.current_session:
                    logger.error("No active session to end")
                    return False
                
                # Update session end data
                now = datetime.now(self.timezone)
                self.current_session.end_time = now.isoformat()
                self.current_session.status = 'completed'
                self.current_session.last_activity = now.isoformat()
                
                if balance_end is not None:
                    self.current_session.balance_end = balance_end
                
                # Save final session data
                self._save_session(self.current_session)
                
                # Clear active session
                self._clear_active_session()
                self._clear_recovery_data()
                
                logger.info(f"Session ended: {self.current_session.session_id}")
                
                # Clear current session
                self.current_session = None
                
                return True
            except Exception as e:
                logger.error(f"Error ending session: {str(e)}")
                return False
    
    def get_current_session(self) -> Optional[SessionInfo]:
        """Get current active session."""
        return self.current_session
    
    def get_session_stats(self) -> Dict:
        """Get current session statistics."""
        if not self.current_session:
            return {"error": "No active session"}
        
        return {
            "session_id": self.current_session.session_id,
            "duration": self._calculate_session_duration(),
            "trades_count": self.current_session.trades_count,
            "signals_count": self.current_session.signals_count,
            "profit_loss": self.current_session.profit_loss,
            "win_rate": self._calculate_win_rate(),
            "status": self.current_session.status
        }
    
    def _get_sessions_for_date(self, date) -> List[Dict]:
        """Get all sessions for a specific date."""
        try:
            with open(self.sessions_file, 'r') as f:
                all_sessions = json.load(f)
            
            date_sessions = []
            for session in all_sessions:
                session_date = datetime.fromisoformat(session['start_time']).date()
                if session_date == date:
                    date_sessions.append(session)
            
            return date_sessions
        except Exception as e:
            logger.error(f"Error getting sessions for date: {str(e)}")
            return []
    
    def _save_session(self, session_info: SessionInfo) -> None:
        """Save session to sessions file."""
        try:
            # Load existing sessions
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
            
            # Update or add session
            session_dict = asdict(session_info)
            updated = False
            
            for i, session in enumerate(sessions):
                if session['session_id'] == session_info.session_id:
                    sessions[i] = session_dict
                    updated = True
                    break
            
            if not updated:
                sessions.append(session_dict)
            
            # Save back to file
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving session: {str(e)}")
    
    def _save_active_session(self) -> None:
        """Save current active session."""
        try:
            if self.current_session:
                with open(self.active_session_file, 'w') as f:
                    json.dump(asdict(self.current_session), f, indent=2)
        except Exception as e:
            logger.error(f"Error saving active session: {str(e)}")
    
    def _save_recovery_data(self) -> None:
        """Save recovery data for session recovery."""
        try:
            if self.current_session:
                recovery_data = {
                    "session_id": self.current_session.session_id,
                    "start_time": self.current_session.start_time,
                    "trades_count": self.current_session.trades_count,
                    "signals_count": self.current_session.signals_count,
                    "balance_start": self.current_session.balance_start,
                    "profit_loss": self.current_session.profit_loss,
                    "wins": self.current_session.wins,
                    "losses": self.current_session.losses,
                    "draws": self.current_session.draws,
                    "errors": self.current_session.errors,
                    "last_save": datetime.now(self.timezone).isoformat()
                }
                
                with open(self.recovery_file, 'w') as f:
                    json.dump(recovery_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving recovery data: {str(e)}")
    
    def _clear_active_session(self) -> None:
        """Clear active session file."""
        try:
            with open(self.active_session_file, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Error clearing active session: {str(e)}")
    
    def _clear_recovery_data(self) -> None:
        """Clear recovery data file."""
        try:
            with open(self.recovery_file, 'w') as f:
                json.dump({}, f)
        except Exception as e:
            logger.error(f"Error clearing recovery data: {str(e)}")
    
    def _mark_session_terminated(self, session_id: str) -> None:
        """Mark a session as terminated."""
        try:
            with open(self.sessions_file, 'r') as f:
                sessions = json.load(f)
            
            for session in sessions:
                if session['session_id'] == session_id:
                    session['status'] = 'terminated'
                    session['end_time'] = datetime.now(self.timezone).isoformat()
                    break
            
            with open(self.sessions_file, 'w') as f:
                json.dump(sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error marking session terminated: {str(e)}")
    
    def _calculate_session_duration(self) -> str:
        """Calculate current session duration."""
        if not self.current_session:
            return "No active session"
        
        try:
            start_time = datetime.fromisoformat(self.current_session.start_time)
            now = datetime.now(self.timezone)
            duration = now - start_time
            
            hours, remainder = divmod(duration.total_seconds(), 3600)
            minutes, seconds = divmod(remainder, 60)
            
            return f"{int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}"
        except Exception as e:
            return f"Error calculating duration: {str(e)}"
    
    def _calculate_win_rate(self) -> float:
        """Calculate win rate for current session."""
        if not self.current_session:
            return 0.0
        
        total_trades = self.current_session.wins + self.current_session.losses
        if total_trades == 0:
            return 0.0
        
        return (self.current_session.wins / total_trades) * 100

    def _load_from_active_session_file(self) -> bool:
        """
        Attempts to load and set an active session from active_session.json.
        This is primarily for sessions started by external tools like session_control.py.
        Returns True if a session was successfully loaded and set, False otherwise.
        """
        try:
            if not os.path.exists(self.active_session_file):
                logger.debug(f"{self.active_session_file} not found. Cannot load external session.")
                return False

            with open(self.active_session_file, 'r') as f:
                active_session_data = json.load(f)

            if not active_session_data or not active_session_data.get('session_id'):
                logger.debug(f"{self.active_session_file} is empty or has no session_id.")
                # Consider clearing it if it's invalid structure for an active session
                # self._clear_active_session() 
                return False

            session_id = active_session_data.get('session_id')
            status = active_session_data.get('status')

            if status != 'active':
                logger.debug(f"Session '{session_id}' in {self.active_session_file} is not 'active' (status: {status}). Skipping load here.")
                return False

            logger.info(f"Found externally started active session in {self.active_session_file}: {session_id}")

            now_iso = datetime.now(self.timezone).isoformat()
            start_time = active_session_data.get('start_time', now_iso)
            # TODO: Ensure start_time is timezone-aware if loaded from file.
            # If datetime.fromisoformat(start_time).tzinfo is None, it needs localization.
            # For now, assume it's compatible or SessionInfo handles it.

            session_info = SessionInfo(
                session_id=session_id,
                start_time=start_time,
                status='active',  # Ensure it's active
                trades_count=active_session_data.get('trades_count', 0),
                signals_count=active_session_data.get('signals_count', 0),
                balance_start=active_session_data.get('balance_start', 0.0), # Bot will update this later
                profit_loss=active_session_data.get('profit_loss', 0.0),
                wins=active_session_data.get('wins', 0),
                losses=active_session_data.get('losses', 0),
                draws=active_session_data.get('draws', 0),
                errors=active_session_data.get('errors', 0),
                last_activity=now_iso,  # Update last_activity
                end_time=active_session_data.get('end_time'), # Should be None for active
                balance_end=active_session_data.get('balance_end'), # Should be None for active
                recovery_data=active_session_data.get('recovery_data') # Might be None
            )

            self.current_session = session_info
            # Re-save active session to ensure full structure and updated last_activity
            self._save_active_session() 
            # Create a recovery point as the bot is taking over this session
            self._save_recovery_data() 
            
            logger.info(f"Successfully loaded and adopted active session from {self.active_session_file}: {session_info.session_id}")
            return True

        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from {self.active_session_file}. File might be corrupt. Clearing it.")
            self._clear_active_session()
            return False
        except Exception as e:
            logger.error(f"Error loading from {self.active_session_file}: {str(e)}")
            return False


class SignalDeduplicator:
    """
    Signal deduplication system using fingerprinting to prevent duplicate signal processing.
    """
    
    def __init__(self, data_dir: str = "data", max_fingerprints: int = 1000):
        """Initialize signal deduplicator."""
        self.data_dir = data_dir
        self.fingerprints_file = os.path.join(data_dir, "signal_fingerprints.json")
        self.max_fingerprints = max_fingerprints
        
        # Thread safety
        self._fingerprint_lock = threading.RLock()
        
        # In-memory cache for fast lookups
        self._fingerprint_cache: Set[str] = set()
        
        # Initialize storage
        self._initialize_storage()
        self._load_fingerprints()
        
        logger.info("SignalDeduplicator initialized successfully")
    
    def _initialize_storage(self) -> None:
        """Initialize fingerprint storage."""
        os.makedirs(self.data_dir, exist_ok=True)
        
        if not os.path.exists(self.fingerprints_file):
            with open(self.fingerprints_file, 'w') as f:
                json.dump([], f)
    
    def _load_fingerprints(self) -> None:
        """Load existing fingerprints into memory cache."""
        try:
            with open(self.fingerprints_file, 'r') as f:
                fingerprints_data = json.load(f)
            
            # Load recent fingerprints into cache
            for fp_data in fingerprints_data[-self.max_fingerprints:]:
                self._fingerprint_cache.add(fp_data['fingerprint'])
            
            logger.debug(f"Loaded {len(self._fingerprint_cache)} fingerprints into cache")
        except Exception as e:
            logger.error(f"Error loading fingerprints: {str(e)}")
    
    def generate_signal_fingerprint(self, signal_data: Dict) -> str:
        """Generate a unique fingerprint for a signal."""
        try:
            # Create fingerprint from key signal components
            fingerprint_data = {
                "pair": signal_data.get("pair", ""),
                "direction": signal_data.get("direction", ""),
                "expiry": signal_data.get("expiry", 0),
                "timer": signal_data.get("timer", ""),
                # Use minute-level timestamp to allow for slight timing variations
                "timestamp_minute": signal_data.get("timestamp", "")[:16] if signal_data.get("timestamp") else ""
            }
            
            # Create hash
            fingerprint_string = json.dumps(fingerprint_data, sort_keys=True)
            fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:16]
            
            return fingerprint
        except Exception as e:
            logger.error(f"Error generating signal fingerprint: {str(e)}")
            return ""
    
    def is_duplicate_signal(self, signal_data: Dict) -> tuple[bool, str]:
        """Check if a signal is a duplicate."""
        with self._fingerprint_lock:
            try:
                fingerprint = self.generate_signal_fingerprint(signal_data)
                if not fingerprint:
                    return False, "Could not generate fingerprint"
                
                # Check cache first (fast lookup)
                if fingerprint in self._fingerprint_cache:
                    return True, f"Duplicate signal detected (fingerprint: {fingerprint})"
                
                return False, "Signal is unique"
            except Exception as e:
                logger.error(f"Error checking duplicate signal: {str(e)}")
                return False, f"Error checking duplicate: {str(e)}"
    
    def register_signal(self, signal_data: Dict) -> bool:
        """Register a new signal to prevent future duplicates."""
        with self._fingerprint_lock:
            try:
                fingerprint = self.generate_signal_fingerprint(signal_data)
                if not fingerprint:
                    return False
                
                # Add to cache
                self._fingerprint_cache.add(fingerprint)
                
                # Save to persistent storage
                fingerprint_record = {
                    "fingerprint": fingerprint,
                    "timestamp": datetime.now().isoformat(),
                    "signal_id": signal_data.get("id", ""),
                    "pair": signal_data.get("pair", ""),
                    "direction": signal_data.get("direction", "")
                }
                
                # Load existing fingerprints
                with open(self.fingerprints_file, 'r') as f:
                    fingerprints_data = json.load(f)
                
                # Add new fingerprint
                fingerprints_data.append(fingerprint_record)
                
                # Cleanup old fingerprints if exceeding limit
                if len(fingerprints_data) > self.max_fingerprints:
                    fingerprints_data = fingerprints_data[-self.max_fingerprints:]
                    
                    # Update cache to match
                    self._fingerprint_cache = {fp['fingerprint'] for fp in fingerprints_data}
                
                # Save back to file
                with open(self.fingerprints_file, 'w') as f:
                    json.dump(fingerprints_data, f, indent=2)
                
                logger.debug(f"Registered signal fingerprint: {fingerprint}")
                return True
            except Exception as e:
                logger.error(f"Error registering signal: {str(e)}")
                return False
    
    def get_fingerprint_stats(self) -> Dict:
        """Get fingerprint statistics."""
        return {
            "total_fingerprints": len(self._fingerprint_cache),
            "max_fingerprints": self.max_fingerprints,
            "cache_size": len(self._fingerprint_cache)
        }
    
    def cleanup_old_fingerprints(self, days_old: int = 7) -> int:
        """Clean up fingerprints older than specified days."""
        with self._fingerprint_lock:
            try:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                with open(self.fingerprints_file, 'r') as f:
                    fingerprints_data = json.load(f)
                
                # Filter out old fingerprints
                filtered_fingerprints = []
                for fp_data in fingerprints_data:
                    fp_timestamp = datetime.fromisoformat(fp_data['timestamp'])
                    if fp_timestamp > cutoff_date:
                        filtered_fingerprints.append(fp_data)
                
                removed_count = len(fingerprints_data) - len(filtered_fingerprints)
                
                # Save filtered fingerprints
                with open(self.fingerprints_file, 'w') as f:
                    json.dump(filtered_fingerprints, f, indent=2)
                
                # Update cache
                self._fingerprint_cache = {fp['fingerprint'] for fp in filtered_fingerprints}
                
                logger.info(f"Cleaned up {removed_count} old fingerprints")
                return removed_count
            except Exception as e:
                logger.error(f"Error cleaning up fingerprints: {str(e)}")
                return 0
