"""
Utility script to discover tables and data structure in ClickHouse Cloud.
This helps you identify the correct table name and field structure for your logs.
"""
import os
from integrations.clickhouse import get_client

# Set ClickHouse Cloud credentials
os.environ["CLICKHOUSE_CLOUD_KEY"] = "kRuHI0HdODEAJokHcaTy"
os.environ["CLICKHOUSE_CLOUD_SECRET"] = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
# Set your ClickHouse Cloud host (e.g., "abc123.us-east-1.aws.clickhouse.cloud")
os.environ["CLICKHOUSE_CLOUD_HOST"] = os.getenv("CLICKHOUSE_CLOUD_HOST", "")
os.environ["CLICKHOUSE_CLOUD_PORT"] = os.getenv("CLICKHOUSE_CLOUD_PORT", "9440")

print("=" * 80)
print("CLICKHOUSE CLOUD DISCOVERY TOOL")
print("=" * 80)

client = get_client()

if not client.use_cloud:
    print("[ERROR] Not connected to ClickHouse Cloud")
    print("\nPlease set the CLICKHOUSE_CLOUD_HOST environment variable.")
    print("\nExample:")
    print("  Windows (PowerShell): $env:CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'")
    print("  Linux/Mac: export CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'")
    print("\nYou can find your host in the ClickHouse Cloud console.")
    exit(1)

print("\n[OK] Connected to ClickHouse Cloud")

print("\n[STEP 1: Discovering Tables]")
print("-" * 80)

# Try to list databases
print("\nFetching databases...")
try:
    databases = client.client.execute("SHOW DATABASES")
    print("Available databases:")
    for db in databases:
        print(f"  - {db[0]}")
except Exception as e:
    print(f"Could not fetch databases: {e}")

# Try to list tables
print("\nFetching tables...")
try:
    tables_result = client.client.execute("SHOW TABLES")
    if tables_result:
        print("Available tables:")
        tables = [t[0] for t in tables_result]
        for table in tables:
            print(f"  - {table}")
    
    print(f"\n[STEP 2: Inspecting Tables]")
    print("-" * 80)
    
    for table in tables[:5]:  # Limit to first 5 tables
        print(f"\n[TABLE] {table}")
        
        # Get table structure
        try:
            structure = client.client.execute(f"DESCRIBE TABLE {table}")
            print("   Structure:")
            for col in structure:
                print(f"      {col[0]}: {col[1]}")
        except Exception as e:
            print(f"   Could not get structure: {e}")
        
        # Get sample data
        try:
            sample_result = client.client.execute(f"SELECT * FROM {table} LIMIT 3", with_column_types=True)
            rows, columns_with_types = sample_result[0], sample_result[1]
            column_names = [col[0] for col in columns_with_types]
            
            if rows and len(rows) > 0:
                print(f"\n   Sample data ({len(rows)} rows):")
                for i, row in enumerate(rows[:2], 1):
                    print(f"   Row {i}:")
                    for key, value in zip(column_names, row):
                        value_str = str(value)[:100]  # Truncate long values
                        print(f"      {key}: {value_str}")
            else:
                print("   No data in table")
        except Exception as e:
            print(f"   Could not get sample data: {e}")
        
        # Get row count
        try:
            count_result = client.client.execute(f"SELECT count() FROM {table}")
            if count_result:
                print(f"\n   Total rows: {count_result[0][0]}")
        except Exception as e:
            print(f"   Could not get row count: {e}")
            
except Exception as e:
    print(f"Could not fetch tables: {e}")
    print("\nTrying alternative queries...")
    
    # Try system tables
    try:
        system_result = client.client.execute("SELECT name FROM system.tables WHERE database = currentDatabase() LIMIT 10")
        if system_result:
            print("Tables from system.tables:")
            for table in system_result:
                print(f"  - {table[0]}")
    except Exception as e2:
        print(f"Alternative query also failed: {e2}")

print("\n" + "=" * 80)
print("DISCOVERY COMPLETE")
print("=" * 80)

print("\nNext steps:")
print("1. Identify the table containing your logs from the list above")
print("2. Set the table name in your environment:")
print("   export CLICKHOUSE_TABLE_NAME='your_table_name'")
print("3. Run the demo: python demo_real_data_pipeline.py")

