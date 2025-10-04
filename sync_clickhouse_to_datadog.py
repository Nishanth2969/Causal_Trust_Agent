#!/usr/bin/env python3
"""
Sync ClickHouse logs and audit_results to Datadog
Continuously queries both tables and sends comparison metrics to Datadog
"""

import os
import time
import signal
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from integrations.clickhouse import get_log_stats, get_audit_stats, get_comparison_stats
from integrations.datadog import (
    send_clickhouse_log_metrics, 
    send_clickhouse_audit_metrics,
    send_clickhouse_comparison_metrics,
    is_enabled as datadog_enabled
)

# Configuration
SYNC_INTERVAL = int(os.getenv("CLICKHOUSE_SYNC_INTERVAL", "300"))  # 5 minutes default
SYNC_ENABLED = os.getenv("CLICKHOUSE_SYNC_ENABLED", "true").lower() == "true"
TIME_WINDOW = 3600  # 1 hour

# Global flag for graceful shutdown
running = True

def signal_handler(sig, frame):
    """Handle Ctrl+C gracefully"""
    global running
    print("\n\n[INFO] Shutdown signal received. Stopping sync...")
    running = False

signal.signal(signal.SIGINT, signal_handler)

def print_banner():
    """Print startup banner"""
    print("=" * 80)
    print("CLICKHOUSE TO DATADOG SYNC SERVICE")
    print("=" * 80)
    print(f"\nConfiguration:")
    print(f"  Sync Interval: {SYNC_INTERVAL} seconds")
    print(f"  Time Window: {TIME_WINDOW} seconds")
    print(f"  Sync Enabled: {SYNC_ENABLED}")
    print(f"  Datadog Enabled: {datadog_enabled()}")
    print("\n" + "=" * 80)

def sync_metrics():
    """Query ClickHouse and send metrics to Datadog"""
    try:
        print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting sync...")
        
        # 1. Get log stats from ClickHouse
        print("  → Querying logs table...")
        log_stats = get_log_stats(TIME_WINDOW)
        
        if log_stats:
            print(f"    ✓ Found {log_stats.get('total_logs', 0)} logs")
            # Send to Datadog
            if datadog_enabled():
                send_clickhouse_log_metrics(log_stats)
        else:
            print("    ⚠ No log stats available")
        
        # 2. Get audit stats from ClickHouse
        print("  → Querying audit_results table...")
        audit_stats = get_audit_stats(TIME_WINDOW)
        
        if audit_stats:
            print(f"    ✓ Found {audit_stats.get('total_evaluated', 0)} audited events")
            print(f"    ✓ Anomalies: {audit_stats.get('anomalies_detected', 0)} ({audit_stats.get('anomaly_rate', 0):.2f}%)")
            # Send to Datadog
            if datadog_enabled():
                send_clickhouse_audit_metrics(audit_stats)
        else:
            print("    ⚠ No audit stats available")
        
        # 3. Get comparison stats
        print("  → Calculating comparison metrics...")
        comparison_stats = get_comparison_stats(TIME_WINDOW)
        
        if comparison_stats:
            print(f"    ✓ Audit Coverage: {comparison_stats.get('audit_coverage', 0):.2f}%")
            print(f"    ✓ Detection Rate: {comparison_stats.get('detection_rate', 0):.2f}%")
            print(f"    ✓ Healthy Components: {comparison_stats.get('healthy_components', 0)}")
            print(f"    ✓ Unhealthy Components: {comparison_stats.get('unhealthy_components', 0)}")
            # Send to Datadog
            if datadog_enabled():
                send_clickhouse_comparison_metrics(comparison_stats)
        else:
            print("    ⚠ No comparison stats available")
        
        print(f"  ✓ Sync completed successfully")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Sync failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def run_continuous():
    """Run sync continuously"""
    print_banner()
    
    if not SYNC_ENABLED:
        print("[WARN] Sync is disabled. Set CLICKHOUSE_SYNC_ENABLED=true to enable.")
        return
    
    if not datadog_enabled():
        print("[WARN] Datadog is not enabled. Metrics will not be sent.")
        print("[INFO] Set DATADOG_API_KEY and DATADOG_APP_KEY to enable Datadog integration.")
    
    print("\n[INFO] Starting continuous sync...")
    print(f"[INFO] Will sync every {SYNC_INTERVAL} seconds")
    print("[INFO] Press Ctrl+C to stop\n")
    
    sync_count = 0
    success_count = 0
    
    while running:
        sync_count += 1
        print(f"\n{'=' * 80}")
        print(f"SYNC #{sync_count}")
        print('=' * 80)
        
        success = sync_metrics()
        if success:
            success_count += 1
        
        if not running:
            break
        
        # Wait for next sync
        print(f"\n[INFO] Next sync in {SYNC_INTERVAL} seconds...")
        
        # Sleep in 1-second intervals to allow for quick shutdown
        for i in range(SYNC_INTERVAL):
            if not running:
                break
            time.sleep(1)
    
    # Print summary
    print("\n" + "=" * 80)
    print("SYNC SERVICE STOPPED")
    print("=" * 80)
    print(f"Total syncs: {sync_count}")
    print(f"Successful: {success_count}")
    print(f"Failed: {sync_count - success_count}")
    print("\n✅ Shutdown complete")

def run_once():
    """Run sync once and exit"""
    print_banner()
    print("\n[INFO] Running single sync...\n")
    
    success = sync_metrics()
    
    if success:
        print("\n✅ Sync completed successfully")
        return 0
    else:
        print("\n✗ Sync failed")
        return 1

if __name__ == "__main__":
    # Check for --once flag
    if "--once" in sys.argv:
        exit_code = run_once()
        sys.exit(exit_code)
    else:
        run_continuous()

