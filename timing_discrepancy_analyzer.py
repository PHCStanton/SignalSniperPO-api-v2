#!/usr/bin/env python3
"""
timing_discrepancy_analyzer.py - Comprehensive Timing Analysis Tool

This tool analyzes timing discrepancies between different timestamp sources
and helps identify timezone, clock sync, and timestamp recording issues.
"""

import os
import sys
import json
import time
import pytz
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import requests
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class TimingMeasurement:
    """Represents a single timing measurement with multiple timestamp sources."""
    measurement_id: str
    local_time_utc: datetime
    local_time_paris: datetime
    system_time_ns: int
    ntp_time_utc: Optional[datetime]
    pocket_option_time: Optional[datetime]
    telegram_time: Optional[datetime]
    measurement_type: str
    notes: str = ""

class TimingDiscrepancyAnalyzer:
    """Analyzes timing discrepancies across different systems and timezones."""
    
    def __init__(self):
        self.measurements: List[TimingMeasurement] = []
        self.utc_tz = pytz.UTC
        self.paris_tz = pytz.timezone('Europe/Paris')
        
    def get_high_precision_time(self) -> Tuple[datetime, int]:
        """Get high-precision time with nanosecond timestamp."""
        ns = time.time_ns()
        dt = datetime.fromtimestamp(ns / 1e9, tz=self.utc_tz)
        return dt, ns
    
    def get_ntp_time(self) -> Optional[datetime]:
        """Get time from NTP server for comparison."""
        try:
            import ntplib
            ntp_client = ntplib.NTPClient()
            response = ntp_client.request('pool.ntp.org', version=3)
            ntp_time = datetime.fromtimestamp(response.tx_time, tz=self.utc_tz)
            return ntp_time
        except Exception as e:
            logger.warning(f"Could not get NTP time: {str(e)}")
            return None
    
    def get_system_timezone_info(self) -> Dict:
        """Get comprehensive system timezone information."""
        try:
            import subprocess
            
            # Get system timezone on Windows
            if os.name == 'nt':
                result = subprocess.run(['tzutil', '/g'], capture_output=True, text=True)
                system_tz = result.stdout.strip() if result.returncode == 0 else "Unknown"
            else:
                # Linux/Unix
                result = subprocess.run(['timedatectl', 'show', '--property=Timezone'], 
                                      capture_output=True, text=True)
                system_tz = result.stdout.strip().split('=')[1] if result.returncode == 0 else "Unknown"
            
            local_time = datetime.now()
            utc_time = datetime.utcnow()
            
            return {
                "system_timezone": system_tz,
                "local_time": local_time.isoformat(),
                "utc_time": utc_time.isoformat(),
                "utc_offset": (local_time - utc_time).total_seconds() / 3600,
                "python_timezone": str(local_time.astimezone().tzinfo),
                "environment_tz": os.environ.get('TZ', 'Not set')
            }
        except Exception as e:
            logger.error(f"Error getting timezone info: {str(e)}")
            return {"error": str(e)}
    
    def measure_timing_sources(self, measurement_type: str = "manual") -> TimingMeasurement:
        """Measure time from all available sources simultaneously."""
        measurement_id = f"{measurement_type}_{int(time.time() * 1e6)}"
        
        # Get high-precision local time
        local_utc, ns_timestamp = self.get_high_precision_time()
        local_paris = local_utc.astimezone(self.paris_tz)
        
        # Get NTP time
        ntp_time = self.get_ntp_time()
        
        # Create measurement
        measurement = TimingMeasurement(
            measurement_id=measurement_id,
            local_time_utc=local_utc,
            local_time_paris=local_paris,
            system_time_ns=ns_timestamp,
            ntp_time_utc=ntp_time,
            pocket_option_time=None,  # Would need API call
            telegram_time=None,       # Would need API call
            measurement_type=measurement_type
        )
        
        self.measurements.append(measurement)
        return measurement
    
    def analyze_session_data(self, session_data: Dict) -> Dict:
        """Analyze timing data from a trading session."""
        analysis = {
            "session_overview": {},
            "timing_discrepancies": [],
            "timezone_analysis": {},
            "recommendations": []
        }
        
        try:
            # Extract timing data from session
            signals = session_data.get("signals", [])
            trades = session_data.get("trades", [])
            
            analysis["session_overview"] = {
                "total_signals": len(signals),
                "total_trades": len(trades),
                "analysis_timestamp": datetime.now(self.utc_tz).isoformat()
            }
            
            # Analyze signal timing patterns
            for signal in signals:
                if "timestamp" in signal:
                    signal_time = datetime.fromisoformat(signal["timestamp"].replace('Z', '+00:00'))
                    
                    # Check if timestamp is in correct timezone
                    if signal_time.tzinfo is None:
                        analysis["timing_discrepancies"].append({
                            "signal_id": signal.get("id", "unknown"),
                            "issue": "Missing timezone information",
                            "timestamp": signal["timestamp"]
                        })
            
            # Analyze timezone consistency
            analysis["timezone_analysis"] = self.get_system_timezone_info()
            
            # Generate recommendations
            analysis["recommendations"] = self.generate_timing_recommendations(analysis)
            
        except Exception as e:
            analysis["error"] = str(e)
            logger.error(f"Error analyzing session data: {str(e)}")
        
        return analysis
    
    def generate_timing_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on timing analysis."""
        recommendations = []
        
        # Check timezone consistency
        tz_info = analysis.get("timezone_analysis", {})
        if tz_info.get("utc_offset", 0) != 0:
            recommendations.append(
                "⚠️ System timezone is not UTC. Consider setting system to UTC for consistency."
            )
        
        # Check for timing discrepancies
        discrepancies = analysis.get("timing_discrepancies", [])
        if discrepancies:
            recommendations.append(
                f"🔧 Found {len(discrepancies)} timing discrepancies. Review timestamp recording logic."
            )
        
        # General recommendations
        recommendations.extend([
            "🕐 Ensure all timestamp recording uses UTC timezone",
            "🔄 Implement NTP synchronization for accurate time",
            "📊 Add timezone-aware logging for better debugging",
            "⚡ Use high-precision timestamps for latency analysis"
        ])
        
        return recommendations
    
    def simulate_signal_timing(self, signal_data: Dict) -> Dict:
        """Simulate the timing flow of a signal to identify discrepancies."""
        simulation = {
            "signal_received_time": None,
            "execution_time": None,
            "timezone_conversions": {},
            "potential_issues": []
        }
        
        try:
            # Simulate signal reception
            signal_time = self.measure_timing_sources("signal_simulation")
            simulation["signal_received_time"] = {
                "utc": signal_time.local_time_utc.isoformat(),
                "paris": signal_time.local_time_paris.isoformat(),
                "nanoseconds": signal_time.system_time_ns
            }
            
            # Simulate execution delay
            time.sleep(0.1)  # Simulate processing time
            execution_time = self.measure_timing_sources("execution_simulation")
            simulation["execution_time"] = {
                "utc": execution_time.local_time_utc.isoformat(),
                "paris": execution_time.local_time_paris.isoformat(),
                "nanoseconds": execution_time.system_time_ns
            }
            
            # Calculate delays
            delay_ns = execution_time.system_time_ns - signal_time.system_time_ns
            delay_ms = delay_ns / 1e6
            
            simulation["execution_delay_ms"] = delay_ms
            
            # Check for potential issues
            if delay_ms > 200:
                simulation["potential_issues"].append("High execution delay detected")
            
            # Timezone conversion analysis
            simulation["timezone_conversions"] = {
                "utc_to_paris_offset": (signal_time.local_time_paris - signal_time.local_time_utc).total_seconds() / 3600,
                "current_dst": signal_time.local_time_paris.dst().total_seconds() != 0
            }
            
        except Exception as e:
            simulation["error"] = str(e)
            logger.error(f"Error in signal timing simulation: {str(e)}")
        
        return simulation
    
    def compare_with_reference_data(self, reference_data: Dict) -> Dict:
        """Compare current timing with reference data from your session."""
        comparison = {
            "reference_analysis": {},
            "discrepancy_analysis": {},
            "root_cause_analysis": []
        }
        
        try:
            # Analyze the reference data you provided
            signals = [
                {"pair": "AUD/NZD", "rsv": "23:00:13,405", "exc": "23:00:13,540", "simon": "21:00:13", "yours": "21:00:13"},
                {"pair": "AUD/CHF", "rsv": "23:01:53,286", "exc": "23:01:53,411", "simon": "21:01:52", "yours": "21:01:52"},
                {"pair": "EUR/USD", "rsv": "23:03:30,671", "exc": "23:03:30,793", "simon": "21:03:50", "yours": "21:03:30"},
                {"pair": "AUD/NZD", "rsv": "23:05:16,533", "exc": "23:05:16,661", "simon": "21:05:21", "yours": "21:05:16"}
            ]
            
            for i, signal in enumerate(signals, 1):
                # Parse times
                rsv_time = datetime.strptime(f"2025-06-16 {signal['rsv']}", "%Y-%m-%d %H:%M:%S,%f")
                exc_time = datetime.strptime(f"2025-06-16 {signal['exc']}", "%Y-%m-%d %H:%M:%S,%f")
                simon_time = datetime.strptime(f"2025-06-16 {signal['simon']}", "%Y-%m-%d %H:%M:%S")
                yours_time = datetime.strptime(f"2025-06-16 {signal['yours']}", "%Y-%m-%d %H:%M:%S")
                
                # Calculate discrepancies
                rsv_exc_delay = (exc_time - rsv_time).total_seconds() * 1000
                simon_yours_diff = (simon_time - yours_time).total_seconds()
                
                comparison[f"signal_{i}"] = {
                    "pair": signal["pair"],
                    "rsv_exc_delay_ms": rsv_exc_delay,
                    "simon_yours_diff_seconds": simon_yours_diff,
                    "timezone_offset_hours": 2,  # RSV/EXC are UTC+2, Simon/Yours are UTC
                    "analysis": {
                        "execution_speed": "Good" if rsv_exc_delay < 200 else "Slow",
                        "timing_anomaly": abs(simon_yours_diff) > 5
                    }
                }
            
            # Root cause analysis
            comparison["root_cause_analysis"] = [
                "🕐 RSV/EXC times are in Paris timezone (UTC+2) while SIMPO/MYPO are in UTC",
                "⚠️ Signal 3 & 4 show Simon's times LATER than yours (unusual pattern)",
                "🔍 This suggests either clock sync issues or different timestamp sources",
                "💡 Recommendation: Standardize all timestamps to UTC with explicit timezone info"
            ]
            
        except Exception as e:
            comparison["error"] = str(e)
            logger.error(f"Error comparing with reference data: {str(e)}")
        
        return comparison
    
    def generate_timing_report(self) -> Dict:
        """Generate comprehensive timing analysis report."""
        report = {
            "report_timestamp": datetime.now(self.utc_tz).isoformat(),
            "system_info": self.get_system_timezone_info(),
            "measurements": [],
            "analysis": {},
            "recommendations": []
        }
        
        try:
            # Take multiple timing measurements
            for i in range(5):
                measurement = self.measure_timing_sources(f"report_measurement_{i+1}")
                report["measurements"].append({
                    "id": measurement.measurement_id,
                    "utc_time": measurement.local_time_utc.isoformat(),
                    "paris_time": measurement.local_time_paris.isoformat(),
                    "nanoseconds": measurement.system_time_ns,
                    "ntp_available": measurement.ntp_time_utc is not None
                })
                time.sleep(0.1)  # Small delay between measurements
            
            # Analyze measurements
            if len(self.measurements) >= 2:
                time_diffs = []
                for i in range(1, len(self.measurements)):
                    diff_ns = self.measurements[i].system_time_ns - self.measurements[i-1].system_time_ns
                    time_diffs.append(diff_ns / 1e6)  # Convert to milliseconds
                
                report["analysis"] = {
                    "measurement_consistency": {
                        "avg_interval_ms": sum(time_diffs) / len(time_diffs),
                        "max_interval_ms": max(time_diffs),
                        "min_interval_ms": min(time_diffs)
                    },
                    "timezone_offset": (self.measurements[0].local_time_paris - self.measurements[0].local_time_utc).total_seconds() / 3600
                }
            
            # Generate recommendations
            report["recommendations"] = [
                "🔧 Implement unified timestamp recording with explicit UTC timezone",
                "📊 Add timezone conversion logging for debugging",
                "⏰ Synchronize system clocks with NTP servers",
                "🎯 Use nanosecond precision for latency measurements",
                "🔍 Log both local and UTC timestamps for comparison"
            ]
            
        except Exception as e:
            report["error"] = str(e)
            logger.error(f"Error generating timing report: {str(e)}")
        
        return report
    
    def save_report(self, report: Dict, filename: str = None) -> str:
        """Save timing analysis report to file."""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"timing_analysis_report_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Timing analysis report saved to: {filename}")
            return filename
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return ""

def main():
    """Main function to run timing discrepancy analysis."""
    print("🕐 Timing Discrepancy Analyzer")
    print("=" * 50)
    
    analyzer = TimingDiscrepancyAnalyzer()
    
    # Generate comprehensive timing report
    print("📊 Generating timing analysis report...")
    report = analyzer.generate_timing_report()
    
    # Analyze your reference data
    print("🔍 Analyzing reference session data...")
    reference_analysis = analyzer.compare_with_reference_data({})
    
    # Simulate signal timing
    print("⚡ Simulating signal timing flow...")
    simulation = analyzer.simulate_signal_timing({})
    
    # Combine all analyses
    comprehensive_report = {
        "timing_report": report,
        "reference_analysis": reference_analysis,
        "signal_simulation": simulation,
        "summary": {
            "key_findings": [
                "RSV/EXC timestamps are in Paris timezone (UTC+2)",
                "SIMPO/MYPO timestamps are in UTC",
                "20-second discrepancy suggests clock sync or source issues",
                "Need to standardize all timestamps to UTC"
            ],
            "immediate_actions": [
                "Verify system timezone settings on bot server",
                "Check NTP synchronization status",
                "Review timestamp recording logic in bot code",
                "Implement timezone-aware logging"
            ]
        }
    }
    
    # Save report
    filename = analyzer.save_report(comprehensive_report)
    
    print(f"\n✅ Analysis complete! Report saved to: {filename}")
    print("\n🔍 Key Findings:")
    for finding in comprehensive_report["summary"]["key_findings"]:
        print(f"  • {finding}")
    
    print("\n🔧 Immediate Actions:")
    for action in comprehensive_report["summary"]["immediate_actions"]:
        print(f"  • {action}")

if __name__ == "__main__":
    main()
