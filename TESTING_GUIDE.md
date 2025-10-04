# Testing Guide

## Quick Test (Without ClickHouse)

You can test the integration **right now** without any ClickHouse configuration:

```bash
python test_clickhouse_integration.py
```

This will:
- ✅ Validate all imports and dependencies
- ✅ Check credential configuration
- ✅ Test the adapter mechanism
- ✅ Verify agent processing works
- ✅ Use mock data when ClickHouse isn't configured

**Expected Result**: 7/8 tests pass (Table discovery skipped without ClickHouse)

---

## Full Test (With ClickHouse Cloud)

To test with your actual ClickHouse Cloud data:

### Step 1: Set Your Host

```powershell
# Windows
$env:CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'
```

```bash
# Linux/Mac
export CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'
```

### Step 2: Run Test Suite

```bash
python test_clickhouse_integration.py
```

**Expected Result**: 8/8 tests pass

---

## Test Suite Overview

The test suite validates:

| Test | What It Checks | Can Skip? |
|------|----------------|-----------|
| 1. Module Imports | All dependencies installed | ❌ No |
| 2. Credentials | API keys configured | ❌ No |
| 3. Connection | ClickHouse Cloud reachable | ✅ Yes (mock mode) |
| 4. Table Discovery | Can list tables | ✅ Yes (needs cloud) |
| 5. Log Fetching | Can retrieve logs | ✅ Yes (uses samples) |
| 6. Transformation | Log format conversion | ❌ No |
| 7. Agent Processing | Event evaluation | ❌ No |
| 8. Adapters | Schema drift fixes | ❌ No |

---

## Test Outputs Explained

### ✅ [OK] - Test Passed
Everything works as expected.

### ⚠️ [WARN] - Warning
Feature works but needs configuration or uses fallback.

### ❌ [FAIL] - Test Failed
Something is broken and needs fixing.

### ℹ️ [INFO] - Information
Just providing context, not a problem.

---

## Individual Tests

### Test Individual Components

**Test just the connection:**
```bash
python discover_clickhouse_tables.py
```

**Test the full pipeline:**
```bash
python demo_real_data_pipeline.py
```

---

## Troubleshooting Tests

### "Import clickhouse integration FAIL"

**Problem**: Missing dependencies

**Solution**:
```bash
pip install -r requirements.txt
```

### "Connection to ClickHouse Cloud FAIL"

**Problem**: Host not reachable or incorrect

**Solutions**:
1. Verify host format: `abc123.region.provider.clickhouse.cloud`
2. Check network connectivity
3. Verify credentials are correct
4. Test in ClickHouse Cloud console first

### "Fetch logs from cloud FAIL"

**Problem**: Table doesn't exist or no permissions

**Solutions**:
1. Run: `python discover_clickhouse_tables.py`
2. Verify table name is correct
3. Check you have read permissions
4. Try a different table

### "Agent processing FAIL"

**Problem**: Event format mismatch

**Solutions**:
1. Check the log transformation output
2. Verify required fields are present
3. Review field mapping in code

---

## Advanced Testing

### Test with Custom Table

```bash
$env:CLICKHOUSE_TABLE_NAME='my_custom_table'
python test_clickhouse_integration.py
```

### Test with Specific Log Count

Edit `test_clickhouse_integration.py` and change:
```python
logs = fetch_logs_from_cloud(table_name, limit=5)  # Change 5 to your desired count
```

### Test Specific Features

Run Python interactively:

```python
# Test connection only
from integrations.clickhouse import get_client
client = get_client()
print(f"Connected: {client.use_cloud}")

# Test fetching
from integrations.clickhouse import fetch_logs_from_cloud
logs = fetch_logs_from_cloud("your_table", limit=10)
print(f"Fetched {len(logs)} logs")

# Test agent processing
from agents.tools import evaluate_event
result = evaluate_event(logs[0])
print(f"Result: {result}")
```

---

## Continuous Testing

### Before Running Demo

Always run the test suite first:
```bash
python test_clickhouse_integration.py && python demo_real_data_pipeline.py
```

### After Configuration Changes

Re-run tests to ensure nothing broke:
```bash
python test_clickhouse_integration.py
```

---

## Test Results Interpretation

### All Tests Pass (8/8)
🎉 **Perfect!** Everything is configured and working.

**Next**: Run the full demo with `python demo_real_data_pipeline.py`

### Most Tests Pass (6-7/8)
✅ **Good!** Core functionality works, some features need configuration.

**Next**: Follow the "NEXT STEPS" output from the test

### Some Tests Fail (4-5/8)
⚠️ **Warning!** Configuration issues exist.

**Next**: Review failed tests and fix configuration

### Many Tests Fail (<4/8)
❌ **Problem!** Major configuration or installation issues.

**Next**: 
1. Run `pip install -r requirements.txt`
2. Check Python version (3.7+)
3. Review error messages carefully

---

## Quick Reference

```bash
# Test everything
python test_clickhouse_integration.py

# Discover tables
python discover_clickhouse_tables.py

# Run full demo
python demo_real_data_pipeline.py

# Test with verbose output
python -v test_clickhouse_integration.py
```

---

## CI/CD Integration

You can use this test suite in your CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Test ClickHouse Integration
  run: python test_clickhouse_integration.py
  env:
    CLICKHOUSE_CLOUD_HOST: ${{ secrets.CLICKHOUSE_HOST }}
    CLICKHOUSE_TABLE_NAME: logs
```

The test suite returns:
- Exit code 0: Tests passed
- Exit code 1: Tests failed

---

## Getting Help

If tests fail and you can't figure out why:

1. Read the error message carefully
2. Check `SETUP_CLICKHOUSE.md` for detailed setup
3. Review `CLICKHOUSE_INTEGRATION_SUMMARY.md` for technical details
4. Ensure environment variables are set correctly:
   ```bash
   # Windows
   Get-ChildItem Env: | Where-Object { $_.Name -like "*CLICKHOUSE*" }
   
   # Linux/Mac
   env | grep CLICKHOUSE
   ```

---

## What Each Test Does

### Test 1: Module Imports
Ensures all Python dependencies are installed correctly.

### Test 2: Credentials Configuration  
Verifies API keys are set and accessible.

### Test 3: ClickHouse Connection
Attempts to connect to ClickHouse Cloud or falls back to mock mode.

### Test 4: Table Discovery
Lists available tables to help you find the right one.

### Test 5: Log Fetching
Retrieves actual logs from your table or uses samples.

### Test 6: Log Transformation
Converts logs to the format expected by agents.

### Test 7: Agent Processing
Runs logs through the evaluation pipeline.

### Test 8: Adapter Mechanism
Validates schema drift remediation works.

---

**Ready to test? Run:** `python test_clickhouse_integration.py`

