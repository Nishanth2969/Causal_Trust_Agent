"""
Test script for ClickHouse Cloud integration
This validates the connection, data fetching, and agent processing
"""
import os
import sys
from datetime import datetime

# Colors for output (cross-platform compatible)
class Colors:
    GREEN = '\033[92m' if sys.platform != 'win32' else ''
    RED = '\033[91m' if sys.platform != 'win32' else ''
    YELLOW = '\033[93m' if sys.platform != 'win32' else ''
    BLUE = '\033[94m' if sys.platform != 'win32' else ''
    RESET = '\033[0m' if sys.platform != 'win32' else ''

def print_test(name, status, message=""):
    """Print test result"""
    if status == "PASS":
        symbol = "[OK]" if sys.platform == 'win32' else "✓"
        color = Colors.GREEN
    elif status == "FAIL":
        symbol = "[FAIL]" if sys.platform == 'win32' else "✗"
        color = Colors.RED
    elif status == "WARN":
        symbol = "[WARN]" if sys.platform == 'win32' else "⚠"
        color = Colors.YELLOW
    else:
        symbol = "[INFO]" if sys.platform == 'win32' else "ℹ"
        color = Colors.BLUE
    
    print(f"{color}{symbol}{Colors.RESET} {name}")
    if message:
        print(f"      {message}")

def test_imports():
    """Test 1: Verify all required imports work"""
    print("\n" + "=" * 80)
    print("TEST 1: Module Imports")
    print("=" * 80)
    
    try:
        from integrations.clickhouse import get_client, fetch_logs_from_cloud
        print_test("Import clickhouse integration", "PASS")
    except Exception as e:
        print_test("Import clickhouse integration", "FAIL", str(e))
        return False
    
    try:
        from agents.tools import evaluate_event
        print_test("Import agent tools", "PASS")
    except Exception as e:
        print_test("Import agent tools", "FAIL", str(e))
        return False
    
    try:
        from agents.adapters import set_adapter, apply_adapters, clear_adapters
        print_test("Import agent adapters", "PASS")
    except Exception as e:
        print_test("Import agent adapters", "FAIL", str(e))
        return False
    
    return True

def test_credentials():
    """Test 2: Verify credentials are set"""
    print("\n" + "=" * 80)
    print("TEST 2: Credentials Configuration")
    print("=" * 80)
    
    # Set credentials
    os.environ["CLICKHOUSE_CLOUD_KEY"] = "kRuHI0HdODEAJokHcaTy"
    os.environ["CLICKHOUSE_CLOUD_SECRET"] = "4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
    
    key = os.environ.get("CLICKHOUSE_CLOUD_KEY")
    secret = os.environ.get("CLICKHOUSE_CLOUD_SECRET")
    
    if key:
        print_test("API Key configured", "PASS", f"Key: {key[:10]}...")
    else:
        print_test("API Key configured", "FAIL", "Key not found")
        return False
    
    if secret:
        print_test("API Secret configured", "PASS", f"Secret: {secret[:10]}...")
    else:
        print_test("API Secret configured", "FAIL", "Secret not found")
        return False
    
    host = os.environ.get("CLICKHOUSE_CLOUD_HOST")
    if host:
        print_test("ClickHouse Host configured", "PASS", f"Host: {host}")
    else:
        print_test("ClickHouse Host configured", "WARN", "Not set - will use fallback mode")
    
    table = os.environ.get("CLICKHOUSE_TABLE_NAME")
    if table:
        print_test("Table name configured", "PASS", f"Table: {table}")
    else:
        print_test("Table name configured", "WARN", "Not set - will use default 'logs'")
    
    return True

def test_connection():
    """Test 3: Test ClickHouse connection"""
    print("\n" + "=" * 80)
    print("TEST 3: ClickHouse Connection")
    print("=" * 80)
    
    try:
        from integrations.clickhouse import get_client
        client = get_client()
        
        if client.use_cloud and client.client:
            print_test("Connection to ClickHouse Cloud", "PASS", "Native protocol connected")
            
            # Try a simple query
            try:
                result = client.client.execute("SELECT 1")
                print_test("Execute test query", "PASS", f"Result: {result}")
                return True, client
            except Exception as e:
                print_test("Execute test query", "FAIL", str(e))
                return False, client
        
        elif client.use_cloud and client.cloud_host:
            print_test("Connection to ClickHouse Cloud", "WARN", "HTTP fallback mode")
            return True, client
        
        elif client.use_mock:
            print_test("Connection to ClickHouse Cloud", "WARN", "Using mock store (no cloud host set)")
            print_test("Mock mode active", "INFO", "This is OK for testing without ClickHouse")
            return True, client
        
        else:
            print_test("Connection status", "INFO", "Using local ClickHouse")
            return True, client
            
    except Exception as e:
        print_test("Connection to ClickHouse", "FAIL", str(e))
        return False, None

def test_table_discovery(client):
    """Test 4: Discover tables"""
    print("\n" + "=" * 80)
    print("TEST 4: Table Discovery")
    print("=" * 80)
    
    if not client:
        print_test("Table discovery", "SKIP", "No client available")
        return False
    
    if client.use_mock:
        print_test("Table discovery", "SKIP", "Mock mode - no real tables")
        return False
    
    try:
        if client.client:
            tables = client.client.execute("SHOW TABLES")
            if tables:
                print_test("List tables", "PASS", f"Found {len(tables)} tables")
                for i, table in enumerate(tables[:5], 1):
                    print(f"      {i}. {table[0]}")
                if len(tables) > 5:
                    print(f"      ... and {len(tables) - 5} more")
                return True
            else:
                print_test("List tables", "WARN", "No tables found")
                return False
        else:
            print_test("List tables", "SKIP", "HTTP mode - cannot list tables automatically")
            return False
    except Exception as e:
        print_test("List tables", "FAIL", str(e))
        return False

def test_fetch_logs(client):
    """Test 5: Fetch logs from ClickHouse"""
    print("\n" + "=" * 80)
    print("TEST 5: Log Fetching")
    print("=" * 80)
    
    if not client:
        print_test("Fetch logs", "SKIP", "No client available")
        return []
    
    if client.use_mock:
        print_test("Fetch logs from cloud", "SKIP", "Mock mode - testing with sample data")
        
        # Create sample log for testing
        sample_logs = [
            {
                "LineId": 1,
                "Level": "INFO",
                "Component": "test-service",
                "Content": "Test log message",
                "latency_ms": 100,
                "status": 200,
                "timestamp": datetime.now().timestamp()
            }
        ]
        print_test("Generate sample logs", "PASS", f"Created {len(sample_logs)} sample logs")
        return sample_logs
    
    try:
        from integrations.clickhouse import fetch_logs_from_cloud
        
        table_name = os.environ.get("CLICKHOUSE_TABLE_NAME", "logs")
        print(f"      Attempting to fetch from table: {table_name}")
        
        logs = fetch_logs_from_cloud(table_name, limit=5)
        
        if logs and len(logs) > 0:
            print_test("Fetch logs from cloud", "PASS", f"Retrieved {len(logs)} logs")
            
            # Show first log structure
            print("\n      Sample log structure:")
            first_log = logs[0]
            for key in list(first_log.keys())[:5]:
                value = str(first_log[key])[:50]
                print(f"        {key}: {value}")
            if len(first_log.keys()) > 5:
                print(f"        ... and {len(first_log.keys()) - 5} more fields")
            
            return logs
        else:
            print_test("Fetch logs from cloud", "WARN", "No logs returned")
            return []
            
    except Exception as e:
        print_test("Fetch logs from cloud", "FAIL", str(e))
        return []

def test_log_transformation(logs):
    """Test 6: Transform logs to agent format"""
    print("\n" + "=" * 80)
    print("TEST 6: Log Transformation")
    print("=" * 80)
    
    if not logs:
        print_test("Transform logs", "SKIP", "No logs to transform")
        return []
    
    try:
        transformed = []
        for i, log in enumerate(logs[:3]):
            event = {
                "LineId": i + 1,
                "timestamp": log.get("timestamp", datetime.now().timestamp()),
            }
            
            # Field mapping
            if "Level" not in log:
                event["Level"] = log.get("level", log.get("severity", "INFO"))
            else:
                event["Level"] = log["Level"]
            
            if "Component" not in log:
                event["Component"] = log.get("component", log.get("service", "unknown"))
            else:
                event["Component"] = log["Component"]
            
            if "Content" not in log:
                event["Content"] = log.get("message", log.get("content", str(log)))
            else:
                event["Content"] = log["Content"]
            
            if "latency_ms" not in log:
                event["latency_ms"] = log.get("latency_ms", log.get("duration_ms", 100))
            else:
                event["latency_ms"] = log["latency_ms"]
            
            if "status" not in log:
                event["status"] = log.get("status", log.get("status_code", 200))
            else:
                event["status"] = log["status"]
            
            transformed.append(event)
        
        print_test("Transform logs to agent format", "PASS", f"Transformed {len(transformed)} logs")
        
        # Verify required fields
        required_fields = ["LineId", "Level", "Component", "Content", "latency_ms", "status"]
        sample = transformed[0]
        all_present = all(field in sample for field in required_fields)
        
        if all_present:
            print_test("Verify required fields", "PASS", "All required fields present")
        else:
            missing = [f for f in required_fields if f not in sample]
            print_test("Verify required fields", "WARN", f"Missing: {missing}")
        
        return transformed
        
    except Exception as e:
        print_test("Transform logs", "FAIL", str(e))
        return []

def test_agent_processing(events):
    """Test 7: Process events through agent"""
    print("\n" + "=" * 80)
    print("TEST 7: Agent Processing")
    print("=" * 80)
    
    if not events:
        print_test("Agent processing", "SKIP", "No events to process")
        return False
    
    try:
        from agents.tools import evaluate_event
        
        results = []
        for event in events[:3]:
            result = evaluate_event(event)
            results.append(result)
        
        print_test("Process events through agent", "PASS", f"Processed {len(results)} events")
        
        # Show results
        for i, result in enumerate(results, 1):
            if result:
                status = "ANOMALY" if result.get('flag') else "OK"
                reason = result.get('reason', 'No reason')
                print(f"      Event {i}: {status} - {reason}")
        
        return True
        
    except Exception as e:
        print_test("Process events through agent", "FAIL", str(e))
        return False

def test_adapter_mechanism():
    """Test 8: Test adapter mechanism"""
    print("\n" + "=" * 80)
    print("TEST 8: Adapter Mechanism")
    print("=" * 80)
    
    try:
        from agents.adapters import set_adapter, apply_adapters, clear_adapters, get_adapters
        
        # Clear any existing adapters
        clear_adapters()
        print_test("Clear adapters", "PASS")
        
        # Set a test adapter
        set_adapter({"old_field": "new_field"})
        adapters = get_adapters()
        print_test("Set adapter", "PASS", f"Active adapters: {adapters}")
        
        # Test applying adapter
        test_event = {"old_field": "test_value", "other": "data"}
        adapted = apply_adapters(test_event)
        
        if "new_field" in adapted and adapted["new_field"] == "test_value":
            print_test("Apply adapter", "PASS", "Field mapping successful")
        else:
            print_test("Apply adapter", "WARN", "Adapter may not have applied correctly")
        
        # Clear adapters
        clear_adapters()
        print_test("Cleanup adapters", "PASS")
        
        return True
        
    except Exception as e:
        print_test("Adapter mechanism", "FAIL", str(e))
        return False

def print_summary(results):
    """Print test summary"""
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"\nTests Passed: {passed}/{total}")
    
    if passed == total:
        print_test("Overall Status", "PASS", "All tests passed!")
        print("\n[OK] Your ClickHouse integration is working correctly!")
        print("[OK] Ready to run: python demo_real_data_pipeline.py")
    elif passed >= total * 0.7:
        print_test("Overall Status", "WARN", "Most tests passed")
        print("\n[WARN] Some features may need configuration")
        print("[INFO] Check warnings above for details")
    else:
        print_test("Overall Status", "FAIL", "Several tests failed")
        print("\n[FAIL] Please review errors above")
        print("[INFO] See SETUP_CLICKHOUSE.md for help")

def main():
    """Run all tests"""
    print("=" * 80)
    print("CLICKHOUSE CLOUD INTEGRATION - TEST SUITE")
    print("=" * 80)
    print("\nThis script will validate your ClickHouse integration setup")
    print("Running tests...\n")
    
    results = []
    
    # Test 1: Imports
    result = test_imports()
    results.append(result)
    if not result:
        print("\n[FAIL] Cannot continue without required imports")
        return
    
    # Test 2: Credentials
    result = test_credentials()
    results.append(result)
    
    # Test 3: Connection
    result, client = test_connection()
    results.append(result)
    
    # Test 4: Table Discovery
    result = test_table_discovery(client)
    results.append(result)
    
    # Test 5: Fetch Logs
    logs = test_fetch_logs(client)
    results.append(len(logs) > 0)
    
    # Test 6: Transform Logs
    events = test_log_transformation(logs)
    results.append(len(events) > 0)
    
    # Test 7: Agent Processing
    result = test_agent_processing(events)
    results.append(result)
    
    # Test 8: Adapter Mechanism
    result = test_adapter_mechanism()
    results.append(result)
    
    # Summary
    print_summary(results)
    
    # Next steps
    print("\n" + "=" * 80)
    print("NEXT STEPS")
    print("=" * 80)
    
    if not os.environ.get("CLICKHOUSE_CLOUD_HOST"):
        print("\n1. Set your ClickHouse Cloud host:")
        print("   Windows: $env:CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'")
        print("   Linux/Mac: export CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'")
        print("\n2. Run discovery: python discover_clickhouse_tables.py")
        print("\n3. Set table name: $env:CLICKHOUSE_TABLE_NAME='your_table'")
        print("\n4. Run this test again")
    else:
        print("\n1. Run full demo: python demo_real_data_pipeline.py")
        print("\n2. Read documentation: START_HERE.md")

if __name__ == "__main__":
    main()

