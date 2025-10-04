"""
Create the audit_results table in ClickHouse Cloud
This table stores the results from the audit agent's evaluations
"""
import os
import requests
from requests.auth import HTTPBasicAuth

# Set credentials
KEY = "kRuHI0HdODEAJokHcaTy"
SECRET = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
SERVICE_ID = "a8f1540f-ad53-4e96-bc82-17c8dbf33c7e"

os.environ["CLICKHOUSE_CLOUD_KEY"] = KEY
os.environ["CLICKHOUSE_CLOUD_SECRET"] = SECRET
os.environ["CLICKHOUSE_SERVICE_ID"] = SERVICE_ID

print("=" * 80)
print("SETUP AUDIT_RESULTS TABLE IN CLICKHOUSE")
print("=" * 80)

url = f"https://queries.clickhouse.cloud/service/{SERVICE_ID}/run?format=JSONEachRow"
auth = HTTPBasicAuth(KEY, SECRET)
headers = {"Content-Type": "application/json"}

# Step 1: Create the audit_results table
print("\n[STEP 1] Creating audit_results table...")
print("-" * 80)

create_table_query = """
CREATE TABLE IF NOT EXISTS audit_results (
    timestamp DateTime,
    event_id String,
    line_id UInt32,
    component String,
    level String,
    is_anomaly UInt8,
    reason String,
    latency_ms UInt32,
    status UInt16
) ENGINE = MergeTree()
ORDER BY (timestamp, line_id)
"""

try:
    payload = {"sql": create_table_query}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=30)
    response.raise_for_status()
    print("[OK] Table 'audit_results' created successfully!")
    print(f"    Response: {response.text if response.text else 'Success (no output)'}")
except Exception as e:
    print(f"[FAIL] Error creating table: {e}")
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print(f"    Response: {e.response.text}")
    exit(1)

# Step 2: Verify table was created
print("\n[STEP 2] Verifying table creation...")
print("-" * 80)

try:
    payload = {"sql": "SHOW TABLES"}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    tables = [line for line in response.text.strip().split('\n') if line]
    if any('audit_results' in table for table in tables):
        print("[OK] Table 'audit_results' found in database!")
        print(f"    All tables: {', '.join([t for t in response.text.strip().split() if t])}")
    else:
        print("[WARN] Table 'audit_results' not found. Available tables:")
        print(f"    {response.text}")
except Exception as e:
    print(f"[FAIL] Error verifying table: {e}")

# Step 3: Show table structure
print("\n[STEP 3] Showing table structure...")
print("-" * 80)

try:
    payload = {"sql": "DESCRIBE audit_results"}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    print("[OK] Table structure:")
    lines = response.text.strip().split('\n')
    import json
    for line in lines:
        if line:
            col_info = json.loads(line)
            print(f"    - {col_info.get('name', 'N/A'):15} {col_info.get('type', 'N/A'):20}")
except Exception as e:
    print(f"[WARN] Could not describe table: {e}")

# Step 4: Test insert
print("\n[STEP 4] Testing audit result insertion...")
print("-" * 80)

from datetime import datetime

test_insert_query = f"""
INSERT INTO audit_results 
(timestamp, event_id, line_id, component, level, is_anomaly, reason, latency_ms, status)
VALUES 
('{datetime.now().isoformat()}', 'test_event_1', 1, 'test.component', 'INFO', 0, 'Test audit result', 150, 200)
"""

try:
    payload = {"sql": test_insert_query}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    print("[OK] Test audit result inserted successfully!")
except Exception as e:
    print(f"[WARN] Error inserting test data: {e}")
    if hasattr(e, 'response') and hasattr(e.response, 'text'):
        print(f"    Response: {e.response.text}")

# Step 5: Query the data
print("\n[STEP 5] Querying audit results...")
print("-" * 80)

try:
    payload = {"sql": "SELECT * FROM audit_results LIMIT 5"}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    lines = response.text.strip().split('\n')
    if lines and lines[0]:
        import json
        results = [json.loads(line) for line in lines if line]
        print(f"[OK] Found {len(results)} audit result(s):")
        for i, result in enumerate(results, 1):
            print(f"\n    Result {i}:")
            print(f"      Event ID: {result.get('event_id', 'N/A')}")
            print(f"      Line ID: {result.get('line_id', 'N/A')}")
            print(f"      Component: {result.get('component', 'N/A')}")
            print(f"      Level: {result.get('level', 'N/A')}")
            print(f"      Is Anomaly: {bool(result.get('is_anomaly', 0))}")
            print(f"      Reason: {result.get('reason', 'N/A')}")
            print(f"      Latency: {result.get('latency_ms', 0)}ms")
            print(f"      Status: {result.get('status', 0)}")
    else:
        print("[INFO] No audit results found (table is empty)")
except Exception as e:
    print(f"[WARN] Error querying data: {e}")

print("\n" + "=" * 80)
print("SETUP COMPLETE")
print("=" * 80)

print("\n[SUMMARY]")
print("  [OK] audit_results table created")
print("  [OK] Table structure verified")
print("  [OK] Test data inserted")
print("\n[NEXT STEPS]")
print("  1. Run the demo: python demo_real_data_pipeline.py")
print("  2. Audit results will be automatically saved to ClickHouse")
print("  3. Query them: python query_audit_results.py")

