#!/usr/bin/env python3
"""
Create ClickHouse tables for CTA autonomous remediation
Run this script to automatically create the required tables in your ClickHouse instance
"""

import os
from dotenv import load_dotenv
from integrations.clickhouse import get_client

# Load environment variables from .env file
load_dotenv()

# Set your ClickHouse Cloud credentials if not already set
# os.environ["CLICKHOUSE_CLOUD_KEY"] = "your_key"
# os.environ["CLICKHOUSE_CLOUD_SECRET"] = "your_secret"
# os.environ["CLICKHOUSE_SERVICE_ID"] = "your_service_id"

print("=" * 80)
print("CLICKHOUSE TABLE CREATION SCRIPT")
print("=" * 80)

client = get_client()

if client.use_mock:
    print("\n[ERROR] Not connected to ClickHouse")
    print("Please set your ClickHouse connection credentials:")
    print("  - CLICKHOUSE_CLOUD_KEY")
    print("  - CLICKHOUSE_CLOUD_SECRET")
    print("  - CLICKHOUSE_SERVICE_ID (for Cloud Query API)")
    print("  OR")
    print("  - CLICKHOUSE_CLOUD_HOST (for native protocol)")
    exit(1)

print(f"\n[OK] Connected to ClickHouse {'Cloud' if client.use_cloud else 'local'}")

# Table creation queries
tables = {
    "cta_results": """
        CREATE TABLE IF NOT EXISTS cta_results (
            run_id String,
            timestamp DateTime DEFAULT now(),
            analysis_method String,
            confidence Float32,
            primary_cause String,
            patch_applied String,
            canary_error_rate Float32,
            canary_latency_p95 Float32,
            decision String,
            mttr_seconds Float32,
            before_error_rate Float32,
            after_error_rate Float32
        ) ENGINE = MergeTree()
        ORDER BY (run_id, timestamp)
        SETTINGS index_granularity = 8192
    """,
    "trace_events": """
        CREATE TABLE IF NOT EXISTS trace_events (
            run_id String,
            idx UInt32,
            timestamp DateTime DEFAULT now(),
            type String,
            payload String
        ) ENGINE = MergeTree()
        ORDER BY (run_id, idx, timestamp)
        SETTINGS index_granularity = 8192
    """
}

print("\n[STEP 1: Creating Tables]")
print("-" * 80)

for table_name, create_query in tables.items():
    print(f"\nCreating table: {table_name}")
    try:
        if client.use_cloud:
            # Use HTTP API for ClickHouse Cloud
            response = client._execute_cloud_query(create_query)
            print(f"  ✓ Table {table_name} created successfully")
        else:
            # Use native client
            client.client.execute(create_query)
            print(f"  ✓ Table {table_name} created successfully")
    except Exception as e:
        print(f"  ✗ Failed to create table {table_name}: {e}")
        print(f"    You may need to create it manually in your ClickHouse console")

print("\n[STEP 2: Verifying Tables]")
print("-" * 80)

try:
    if client.use_cloud:
        # Query system tables
        result = client._execute_cloud_query(
            "SELECT name FROM system.tables WHERE database = currentDatabase() AND name IN ('cta_results', 'trace_events')"
        )
    else:
        result = client.client.execute(
            "SELECT name FROM system.tables WHERE database = currentDatabase() AND name IN ('cta_results', 'trace_events')"
        )
    
    if result:
        print("\nTables found:")
        for row in result:
            table_name = row['name'] if isinstance(row, dict) else row[0]
            print(f"  ✓ {table_name}")
    else:
        print("\n⚠️  No tables found. Please check the creation logs above.")
        
except Exception as e:
    print(f"\n⚠️  Could not verify tables: {e}")

print("\n[STEP 3: Sample Data Check]")
print("-" * 80)

for table_name in ["cta_results", "trace_events"]:
    try:
        if client.use_cloud:
            result = client._execute_cloud_query(f"SELECT count() as cnt FROM {table_name}")
            count = result[0]['cnt'] if result else 0
        else:
            result = client.client.execute(f"SELECT count() FROM {table_name}")
            count = result[0][0] if result else 0
        
        print(f"\n{table_name}: {count} rows")
    except Exception as e:
        print(f"\n{table_name}: Could not query ({e})")

print("\n" + "=" * 80)
print("TABLE CREATION COMPLETE")
print("=" * 80)

print("\n[NEXT STEPS]")
print("-" * 80)
print("1. Enable ClickHouse data flow:")
print("   export USE_CLICKHOUSE_FOR_CTA=true")
print("   export CLICKHOUSE_TRACE_TABLE=trace_events")
print("")
print("2. Run your CTA pipeline:")
print("   python demo_real_data_pipeline.py")
print("")
print("3. Query results in ClickHouse:")
print("   SELECT * FROM cta_results ORDER BY timestamp DESC LIMIT 10;")
print("   SELECT * FROM trace_events WHERE run_id = 'your_run_id' ORDER BY idx;")
print("")
print("4. View sample queries in clickhouse_tables_schema.sql")

print("\n✅ Setup complete! Your ClickHouse instance is ready for CTA data.")

