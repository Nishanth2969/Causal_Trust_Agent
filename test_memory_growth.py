"""
Test script to demonstrate agent memory growth
"""
import os
from integrations.clickhouse import get_audit_results

# Set credentials
os.environ["CLICKHOUSE_CLOUD_KEY"] = "kRuHI0HdODEAJokHcaTy"
os.environ["CLICKHOUSE_CLOUD_SECRET"] = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
os.environ["CLICKHOUSE_SERVICE_ID"] = "a8f1540f-ad53-4e96-bc82-17c8dbf33c7e"

print("=" * 80)
print("AGENT MEMORY GROWTH TEST")
print("=" * 80)

print("\nFetching agent's current memory...")
memory = get_audit_results(limit=1000)

if not memory:
    print("\n[INFO] Agent has no memory yet (empty)")
    print("[INFO] Run the demo to build memory:")
    print("       python demo_real_data_pipeline.py")
else:
    print(f"\n[OK] Agent has {len(memory)} memories stored")
    
    # Statistics
    anomalies = sum(1 for m in memory if m.get('is_anomaly', 0) == 1)
    print(f"\n[STATISTICS]")
    print(f"  Total memories: {len(memory)}")
    print(f"  Anomalies: {anomalies}")
    print(f"  Normal: {len(memory) - anomalies}")
    print(f"  Anomaly rate: {anomalies/len(memory)*100:.1f}%")
    
    # Components
    components = {}
    for m in memory:
        comp = m.get('component', 'unknown')
        components[comp] = components.get(comp, 0) + 1
    
    print(f"\n[COMPONENTS IN MEMORY]")
    for comp, count in sorted(components.items(), key=lambda x: x[1], reverse=True):
        print(f"  {comp}: {count} evaluations")
    
    # Recent memories
    print(f"\n[MOST RECENT MEMORIES]")
    for i, m in enumerate(memory[:3], 1):
        print(f"\n  Memory {i}:")
        print(f"    Timestamp: {m.get('timestamp', 'N/A')}")
        print(f"    Component: {m.get('component', 'N/A')}")
        print(f"    Anomaly: {bool(m.get('is_anomaly', 0))}")
        print(f"    Reason: {m.get('reason', 'N/A')}")

print("\n" + "=" * 80)
print("NEXT STEPS")
print("=" * 80)
print("\n1. Run demo to add more memories:")
print("   python demo_real_data_pipeline.py")
print("\n2. Run this test again to see growth:")
print("   python test_memory_growth.py")
print("\n3. Query all memories:")
print("   python query_audit_results.py")

