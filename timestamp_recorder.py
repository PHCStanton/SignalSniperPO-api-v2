#!/usr/bin/env python3
"""
timestamp_recorder.py - Robust Timestamp Recording Module for Self Bot v1.5

This module provides comprehensive timestamp recording functionality with backup systems
and performance monitoring for the trading bot.
"""

import os
import json
import time
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class TimestampRecorder:
    """Handles robust timestamp recording with backup mechanisms and buffered writes for low latency."""

    def __init__(self, data_dir: str = "data", max_records: int = 1000, buffer_size: int = 10):
        self.data_dir = data_dir
        self.timestamps_file = os.path.join(data_dir, "timestamps.json")
        self.backup_file = os.path.join(data_dir, "timestamps_backup.json")
        self.max_records = max_records
        self.buffer_size = buffer_size
        self._buffered_records = []

        # Create data directory if it doesn't exist
        os.makedirs(data_dir, exist_ok=True)

        # Initialize empty file if it doesn't exist
        if not os.path.exists(self.timestamps_file):
            with open(self.timestamps_file, 'w') as f:
                json.dump([], f)
    
    def record_signal_timestamp(self, signal_id: str, currency_pair: str, session_id: str) -> Dict:
        """Record when a signal is received and return timestamp record."""
        signal_received_time = datetime.now()
        
        timestamp_record = {
            "signal_id": signal_id,
            "currency_pair": currency_pair,
            "signal_received": signal_received_time.isoformat(),
            "session_id": session_id,
            "status": "signal_received"
        }
        
        logger.debug(f"Signal timestamp recorded: {signal_id}")
        return timestamp_record
    
    def record_execution_timestamp(self, timestamp_record: Dict, trade_id: str) -> Dict:
        """Record when trade execution starts and calculate delay."""
        execution_time = datetime.now()
        
        # Calculate execution delay
        signal_time = datetime.fromisoformat(timestamp_record["signal_received"])
        delay_ms = (execution_time - signal_time).total_seconds() * 1000
        
        # Update timestamp record
        timestamp_record.update({
            "signal_executed": execution_time.isoformat(),
            "execution_delay_ms": round(delay_ms, 3),
            "trade_id": trade_id,
            "status": "trade_executed"
        })
        
        # Save to storage
        self.save_timestamp_record(timestamp_record)
        
        logger.info(f"Trade execution timestamp recorded: {trade_id} (Delay: {delay_ms:.1f}ms)")
        return timestamp_record
    
    def save_timestamp_record(self, timestamp_record: Dict) -> bool:
        """Buffer timestamp record and flush to disk when buffer is full."""
        try:
            self._buffered_records.append(timestamp_record)
            if len(self._buffered_records) >= self.buffer_size:
                self.flush_buffer()
            return True
        except Exception as e:
            logger.error(f"Error buffering timestamp record: {str(e)}")
            # Try backup save
            return self._save_backup_timestamp(timestamp_record)

    def flush_buffer(self):
        """Flush buffered timestamp records to disk."""
        if not self._buffered_records:
            return
        try:
            # Load existing timestamps
            timestamps = self._load_timestamps()
            timestamps.extend(self._buffered_records)
            # Cleanup old records
            timestamps = self._cleanup_old_records(timestamps)
            # Save with atomic operation
            self._save_timestamps_atomic(timestamps)
            self._buffered_records = []
        except Exception as e:
            logger.error(f"Error flushing timestamp buffer: {str(e)}")
    
    def _load_timestamps(self) -> List[Dict]:
        """Load timestamps from file with error handling."""
        try:
            with open(self.timestamps_file, 'r') as f:
                data = json.load(f)
                return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading timestamps: {str(e)}")
            # Try loading from backup
            return self._load_backup_timestamps()
    
    def _load_backup_timestamps(self) -> List[Dict]:
        """Load timestamps from backup file."""
        try:
            if os.path.exists(self.backup_file):
                with open(self.backup_file, 'r') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except Exception as e:
            logger.error(f"Error loading backup timestamps: {str(e)}")
        return []
    
    def _save_timestamps_atomic(self, timestamps: List[Dict]) -> bool:
        """Save timestamps using atomic operation."""
        try:
            # Create backup first
            if os.path.exists(self.timestamps_file):
                shutil.copy2(self.timestamps_file, self.backup_file)
            
            # Write to temporary file first
            temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, dir=self.data_dir)
            json.dump(timestamps, temp_file, indent=2)
            temp_file.close()
            
            # Replace original file
            shutil.move(temp_file.name, self.timestamps_file)
            return True
            
        except Exception as e:
            logger.error(f"Error in atomic save: {str(e)}")
            return False
    
    def _save_backup_timestamp(self, timestamp_record: Dict) -> bool:
        """Save single timestamp record to backup file."""
        try:
            backup_timestamps = self._load_backup_timestamps()
            backup_timestamps.append(timestamp_record)
            backup_timestamps = self._cleanup_old_records(backup_timestamps)
            
            with open(self.backup_file, 'w') as f:
                json.dump(backup_timestamps, f, indent=2)
            
            logger.info(f"Timestamp saved to backup: {timestamp_record.get('signal_id')}")
            return True
            
        except Exception as e:
            logger.error(f"Backup timestamp save failed: {str(e)}")
            return False
    
    def _cleanup_old_records(self, timestamps: List[Dict]) -> List[Dict]:
        """Remove old records if exceeding max limit."""
        if len(timestamps) > self.max_records:
            return timestamps[-self.max_records:]
        return timestamps
    
    def get_performance_stats(self) -> Dict:
        """Get timestamp performance statistics."""
        try:
            timestamps = self._load_timestamps()
            if not timestamps:
                return {
                    "total_records": 0,
                    "average_delay_ms": 0.0,
                    "min_delay_ms": 0.0,
                    "max_delay_ms": 0.0,
                    "last_record": None
                }
            
            # Calculate statistics
            delays = [record.get("execution_delay_ms", 0) for record in timestamps 
                     if "execution_delay_ms" in record]
            
            stats = {
                "total_records": len(timestamps),
                "average_delay_ms": round(sum(delays) / len(delays), 2) if delays else 0.0,
                "min_delay_ms": round(min(delays), 2) if delays else 0.0,
                "max_delay_ms": round(max(delays), 2) if delays else 0.0,
                "last_record": timestamps[-1] if timestamps else None
            }
            
            return stats
            
        except Exception as e:
            logger.error(f"Error calculating performance stats: {str(e)}")
            return {
                "total_records": 0,
                "average_delay_ms": 0.0,
                "error": str(e)
            }
    
    def get_recent_records(self, limit: int = 10) -> List[Dict]:
        """Get recent timestamp records."""
        try:
            timestamps = self._load_timestamps()
            return timestamps[-limit:] if timestamps else []
        except Exception as e:
            logger.error(f"Error getting recent records: {str(e)}")
            return []
    
    def cleanup_old_files(self, days_to_keep: int = 30) -> bool:
        """Clean up old timestamp files."""
        try:
            cutoff_time = time.time() - (days_to_keep * 24 * 60 * 60)
            
            # Check and remove old backup files
            for filename in os.listdir(self.data_dir):
                if filename.startswith("timestamps_backup_"):
                    filepath = os.path.join(self.data_dir, filename)
                    if os.path.getmtime(filepath) < cutoff_time:
                        os.remove(filepath)
                        logger.info(f"Removed old timestamp backup: {filename}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error cleaning up old files: {str(e)}")
            return False
