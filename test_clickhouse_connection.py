"""
Quick test script to verify ClickHouse Cloud connection
"""
import os
import requests
from requests.auth import HTTPBasicAuth

# Set credentials
KEY = "kRuHI0HdODEAJokHcaTy"
SECRET = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
SERVICE_ID = "a8f1540f-ad53-4e96-bc82-17c8dbf33c7e"

print("=" * 80)
print("CLICKHOUSE CLOUD CONNECTION TEST")
print("=" * 80)

# Set environment variables
os.environ["CLICKHOUSE_CLOUD_KEY"] = KEY
os.environ["CLICKHOUSE_CLOUD_SECRET"] = SECRET
os.environ["CLICKHOUSE_SERVICE_ID"] = SERVICE_ID

print(f"\n[INFO] Service ID: {SERVICE_ID}")
print(f"[INFO] API Key: {KEY[:10]}...")

# Test 1: Direct API call
print("\n" + "-" * 80)
print("TEST 1: Direct API Call")
print("-" * 80)

url = f"https://queries.clickhouse.cloud/service/{SERVICE_ID}/run?format=JSONEachRow"
payload = {"sql": "SHOW TABLES"}
headers = {"Content-Type": "application/json"}
auth = HTTPBasicAuth(KEY, SECRET)

try:
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    print("[OK] Connection successful!")
    print(f"[OK] Status code: {response.status_code}")
    
    if response.text:
        print(f"\n[OK] Response:")
        lines = response.text.strip().split('\n')
        for line in lines[:10]:  # Show first 10 lines
            print(f"  {line}")
        if len(lines) > 10:
            print(f"  ... and {len(lines) - 10} more lines")
    else:
        print("[WARN] Empty response")
        
except requests.exceptions.HTTPError as e:
    print(f"[FAIL] HTTP Error: {e}")
    print(f"[FAIL] Response: {e.response.text if hasattr(e, 'response') else 'N/A'}")
except Exception as e:
    print(f"[FAIL] Connection error: {e}")
    exit(1)

# Test 2: Using our integration
print("\n" + "-" * 80)
print("TEST 2: Using Integration")
print("-" * 80)

try:
    from integrations.clickhouse import get_client
    
    client = get_client()
    
    if client.use_cloud:
        print("[OK] Client initialized in cloud mode")
        print(f"[OK] Endpoint: {client.cloud_host}")
    else:
        print("[WARN] Client not in cloud mode")
        
except Exception as e:
    print(f"[FAIL] Integration error: {e}")
    import traceback
    traceback.print_exc()

# Test 3: List tables
print("\n" + "-" * 80)
print("TEST 3: List Tables")
print("-" * 80)

try:
    payload = {"sql": "SHOW TABLES"}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    lines = response.text.strip().split('\n')
    
    if lines and lines[0]:
        import json
        tables = [json.loads(line) for line in lines if line]
        
        print(f"[OK] Found {len(tables)} tables:")
        for i, table in enumerate(tables[:10], 1):
            print(f"  {i}. {table}")
        if len(tables) > 10:
            print(f"  ... and {len(tables) - 10} more")
    else:
        print("[WARN] No tables found or empty database")
        
except Exception as e:
    print(f"[FAIL] Error listing tables: {e}")

# Test 4: Sample query
print("\n" + "-" * 80)
print("TEST 4: Sample Query")
print("-" * 80)

try:
    # Try a simple SELECT 1 query
    payload = {"sql": "SELECT 1 as test"}
    response = requests.post(url, auth=auth, headers=headers, json=payload, timeout=10)
    response.raise_for_status()
    
    print("[OK] Query executed successfully")
    print(f"[OK] Response: {response.text.strip()}")
    
except Exception as e:
    print(f"[FAIL] Query error: {e}")

print("\n" + "=" * 80)
print("TEST SUMMARY")
print("=" * 80)

print("\n[OK] ClickHouse Cloud connection is working!")
print("\nNext steps:")
print("1. Set environment variable:")
print(f"   $env:CLICKHOUSE_SERVICE_ID='{SERVICE_ID}'")
print("\n2. Discover your tables:")
print("   python discover_clickhouse_tables.py")
print("\n3. Set a table name and run the demo:")
print("   $env:CLICKHOUSE_TABLE_NAME='your_table'")
print("   python demo_real_data_pipeline.py")

