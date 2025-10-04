"""
Query and display audit results from ClickHouse
"""
import os
from datetime import datetime
from integrations.clickhouse import get_audit_results, get_client

# Set credentials
os.environ["CLICKHOUSE_CLOUD_KEY"] = "kRuHI0HdODEAJokHcaTy"
os.environ["CLICKHOUSE_CLOUD_SECRET"] = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
os.environ["CLICKHOUSE_SERVICE_ID"] = "a8f1540f-ad53-4e96-bc82-17c8dbf33c7e"

print("=" * 80)
print("QUERY AUDIT RESULTS FROM CLICKHOUSE")
print("=" * 80)

# Initialize client
client = get_client()
print(f"\n[INFO] Connection status: {'Connected' if client.use_cloud else 'Not connected'}")

# Fetch all audit results
print("\n[STEP 1] Fetching all audit results...")
print("-" * 80)

results = get_audit_results(limit=100)

if results:
    print(f"\n[OK] Found {len(results)} audit result(s)")
    
    # Summary statistics
    anomaly_count = sum(1 for r in results if r.get('is_anomaly', 0) == 1)
    normal_count = len(results) - anomaly_count
    
    print(f"\n[STATISTICS]")
    print(f"  Total audits: {len(results)}")
    print(f"  Anomalies: {anomaly_count} ({anomaly_count/len(results)*100:.1f}%)")
    print(f"  Normal: {normal_count} ({normal_count/len(results)*100:.1f}%)")
    
    # Component breakdown
    components = {}
    for r in results:
        comp = r.get('component', 'unknown')
        components[comp] = components.get(comp, 0) + 1
    
    print(f"\n[COMPONENT BREAKDOWN]")
    for comp, count in sorted(components.items(), key=lambda x: x[1], reverse=True):
        print(f"  {comp}: {count} audit(s)")
    
    # Level breakdown
    levels = {}
    for r in results:
        level = r.get('level', 'unknown')
        levels[level] = levels.get(level, 0) + 1
    
    print(f"\n[LEVEL BREAKDOWN]")
    for level, count in sorted(levels.items(), key=lambda x: x[1], reverse=True):
        print(f"  {level}: {count} audit(s)")
    
    # Show recent anomalies
    print("\n[RECENT ANOMALIES]")
    print("-" * 80)
    anomalies = [r for r in results if r.get('is_anomaly', 0) == 1]
    
    if anomalies:
        for i, result in enumerate(anomalies[:5], 1):
            print(f"\n  Anomaly {i}:")
            print(f"    Timestamp: {result.get('timestamp', 'N/A')}")
            print(f"    Event ID: {result.get('event_id', 'N/A')}")
            print(f"    Line ID: {result.get('line_id', 'N/A')}")
            print(f"    Component: {result.get('component', 'N/A')}")
            print(f"    Level: {result.get('level', 'N/A')}")
            print(f"    Reason: {result.get('reason', 'N/A')}")
            print(f"    Latency: {result.get('latency_ms', 0)}ms")
            print(f"    Status: {result.get('status', 0)}")
        
        if len(anomalies) > 5:
            print(f"\n  ... and {len(anomalies) - 5} more anomalies")
    else:
        print("  No anomalies found")
    
    # Show sample normal results
    print("\n[RECENT NORMAL RESULTS]")
    print("-" * 80)
    normal = [r for r in results if r.get('is_anomaly', 0) == 0]
    
    if normal:
        for i, result in enumerate(normal[:3], 1):
            print(f"\n  Result {i}:")
            print(f"    Timestamp: {result.get('timestamp', 'N/A')}")
            print(f"    Component: {result.get('component', 'N/A')}")
            print(f"    Level: {result.get('level', 'N/A')}")
            print(f"    Reason: {result.get('reason', 'N/A')}")
            print(f"    Latency: {result.get('latency_ms', 0)}ms")
        
        if len(normal) > 3:
            print(f"\n  ... and {len(normal) - 3} more normal results")
    else:
        print("  No normal results found")

else:
    print("\n[INFO] No audit results found")
    print("[INFO] Run the demo first: python demo_real_data_pipeline.py")

# Query with filters
print("\n" + "=" * 80)
print("[STEP 2] Querying anomalies only...")
print("-" * 80)

anomaly_results = get_audit_results(limit=50, filters={"is_anomaly": 1})

if anomaly_results:
    print(f"\n[OK] Found {len(anomaly_results)} anomaly result(s)")
    
    for i, result in enumerate(anomaly_results[:3], 1):
        print(f"\n  Anomaly {i}:")
        print(f"    Line ID: {result.get('line_id', 'N/A')}")
        print(f"    Component: {result.get('component', 'N/A')}")
        print(f"    Reason: {result.get('reason', 'N/A')}")
else:
    print("\n[INFO] No anomalies found")

print("\n" + "=" * 80)
print("QUERY COMPLETE")
print("=" * 80)

print("\n[ACTIONS]")
print("  - View audit results in ClickHouse Cloud console")
print("  - Run demo again to generate more audit data")
print("  - Use filters to query specific components or anomalies")

