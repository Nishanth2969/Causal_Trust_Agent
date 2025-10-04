"""
Fetch logs from your ClickHouse Cloud logs table
"""
import os
from integrations.clickhouse import fetch_logs_from_cloud, get_client

# Set credentials
os.environ["CLICKHOUSE_CLOUD_KEY"] = "kRuHI0HdODEAJokHcaTy"
os.environ["CLICKHOUSE_CLOUD_SECRET"] = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
os.environ["CLICKHOUSE_SERVICE_ID"] = "a8f1540f-ad53-4e96-bc82-17c8dbf33c7e"

print("=" * 80)
print("FETCHING LOGS FROM CLICKHOUSE CLOUD")
print("=" * 80)

# Initialize client
client = get_client()

print(f"\n[INFO] Connection status: {'Connected' if client.use_cloud else 'Not connected'}")
print(f"[INFO] Fetching from table: logs")

# Fetch logs
print("\nFetching logs...")
logs = fetch_logs_from_cloud("logs", limit=10)

if logs:
    print(f"\n[OK] Successfully fetched {len(logs)} logs!")
    
    print("\n" + "-" * 80)
    print("LOG STRUCTURE")
    print("-" * 80)
    
    if logs:
        first_log = logs[0]
        print(f"\nFields in logs table ({len(first_log)} fields):")
        for i, key in enumerate(first_log.keys(), 1):
            print(f"  {i}. {key}")
        
        print("\n" + "-" * 80)
        print("SAMPLE LOGS")
        print("-" * 80)
        
        for i, log in enumerate(logs[:5], 1):
            print(f"\n[LOG {i}]")
            for key, value in log.items():
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"  {key}: {value_str}")
        
        if len(logs) > 5:
            print(f"\n... and {len(logs) - 5} more logs")
else:
    print("[WARN] No logs fetched - table might be empty")

print("\n" + "=" * 80)
print("DONE")
print("=" * 80)

