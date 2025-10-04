# Quick Start: ClickHouse Cloud Integration

This guide will help you quickly set up and run the demo with your ClickHouse Cloud logs.

## Prerequisites

- Python 3.7+
- ClickHouse Cloud account with logs data
- API credentials (already configured):
  - Key: `kRuHI0HdODEAJokHcaTy`
  - Secret: `4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh`

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

## Step 2: Find Your ClickHouse Host

You need to find your ClickHouse Cloud instance hostname. This is typically in the format:
```
abc123.region.cloud-provider.clickhouse.cloud
```

**Where to find it:**
1. Log in to [ClickHouse Cloud Console](https://clickhouse.cloud/)
2. Go to your service/instance
3. Look for "Connection Details" or "Endpoint"
4. Copy the hostname (without `https://` or port numbers)

**Example:**
- ✅ Good: `abc123.us-east-1.aws.clickhouse.cloud`
- ❌ Bad: `https://abc123.us-east-1.aws.clickhouse.cloud:8443`

## Step 3: Set Environment Variables

### On Windows (PowerShell):
```powershell
$env:CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'
$env:CLICKHOUSE_TABLE_NAME='logs'
```

### On Linux/Mac:
```bash
export CLICKHOUSE_CLOUD_HOST='your-instance.clickhouse.cloud'
export CLICKHOUSE_TABLE_NAME='logs'
```

### On Windows (CMD):
```cmd
set CLICKHOUSE_CLOUD_HOST=your-instance.clickhouse.cloud
set CLICKHOUSE_TABLE_NAME=logs
```

## Step 4: Discover Your Tables

Run the discovery script to see what tables are available:

```bash
python discover_clickhouse_tables.py
```

**This will show:**
- All available databases
- All tables in your current database
- Table structures (columns and types)
- Sample data from each table
- Row counts

**Example output:**
```
[OK] Connected to ClickHouse Cloud

Available tables:
  - application_logs
  - system_metrics
  - user_events

[TABLE] application_logs
   Structure:
      timestamp: DateTime
      level: String
      message: String
      service: String
   
   Sample data (2 rows):
   Row 1:
      timestamp: 2024-10-04 10:30:15
      level: ERROR
      message: Connection timeout
      service: payment-api
```

## Step 5: Configure Table Name

From the discovery output, identify the table containing your logs and set it:

### Windows (PowerShell):
```powershell
$env:CLICKHOUSE_TABLE_NAME='application_logs'
```

### Linux/Mac:
```bash
export CLICKHOUSE_TABLE_NAME='application_logs'
```

## Step 6: Run the Demo

```bash
python demo_real_data_pipeline.py
```

The demo will:
1. ✅ Connect to ClickHouse Cloud
2. ✅ Fetch your real logs
3. ✅ Transform them to the expected format
4. ✅ Process through the CTA agent pipeline
5. ✅ Demonstrate autonomous incident remediation
6. ✅ Show learning and re-application of fixes

## Troubleshooting

### Problem: "Not connected to ClickHouse Cloud"

**Solution:**
- Verify `CLICKHOUSE_CLOUD_HOST` is set correctly
- Check that your hostname doesn't include `https://` or port numbers
- Ensure you can access ClickHouse Cloud from your network

### Problem: "Could not fetch tables"

**Solutions:**
1. Verify your API credentials are correct
2. Check that your ClickHouse instance is running
3. Ensure your firewall allows outbound connections to ClickHouse Cloud
4. Try connecting via the ClickHouse Cloud web console to verify access

### Problem: "No logs found in ClickHouse Cloud"

**Solutions:**
1. Verify the table name is correct (run discovery script)
2. Check that the table actually contains data
3. Try a different table from the discovery output
4. The system will automatically fall back to dummy CSV data if needed

### Problem: "Schema mismatch" or logs not processing correctly

**Solution:**
The system automatically maps common field names. If your logs use different field names:

1. Run the discovery script to see your actual schema
2. Edit `demo_real_data_pipeline.py` around line 98-107
3. Update the field mapping:

```python
event = {
    "LineId": i + 1,
    "timestamp": log.get("your_timestamp_field"),
    "Level": log.get("your_level_field"),
    "Component": log.get("your_service_field"),
    "Content": log.get("your_message_field"),
    "latency_ms": log.get("your_duration_field", 100),
    "status": log.get("your_status_field", 200),
}
```

## What Happens During the Demo

The demo showcases the full CTA (Causal Trust Agent) autonomous remediation workflow:

### Phase 1: Data Ingestion
- Fetches real logs from your ClickHouse Cloud instance
- Transforms them to match the expected event format
- Stores them locally for processing

### Phase 2: Normal Operation
- 3-agent pipeline processes events (Intake → Retriever → Auditor)
- Evaluates each log entry for anomalies
- Reports success metrics

### Phase 3: Incident Injection
- Simulates a schema drift (field name change)
- Shows pipeline failure with 100% error rate
- Demonstrates real-world incident scenario

### Phase 4: Autonomous Remediation
- CTA detects the failure pattern
- Performs root cause analysis
- Generates and applies a fix automatically
- Runs canary tests to verify the fix
- Promotes fix to production

### Phase 5: Validation
- Processes problematic logs with the fix applied
- Shows 100% recovery rate
- Reports Mean Time To Resolution (MTTR)

### Phase 6: Learning
- Saves incident signature for future reference
- Demonstrates instant fix application on repeat incidents
- Shows system learning from every incident

## Advanced Configuration

### Custom Filters

Fetch logs with specific criteria:

```python
from integrations.clickhouse import fetch_logs_from_cloud

logs = fetch_logs_from_cloud(
    table_name="application_logs",
    limit=500,
    filters={
        "level": "ERROR",
        "service": "payment-api"
    }
)
```

### Different Port

If your ClickHouse instance uses a different port:

```bash
# Windows PowerShell
$env:CLICKHOUSE_CLOUD_PORT='8443'

# Linux/Mac
export CLICKHOUSE_CLOUD_PORT='8443'
```

### Multiple Databases

To query a specific database:

```python
logs = fetch_logs_from_cloud(
    table_name="my_database.my_table",
    limit=100
)
```

## Security Best Practices

⚠️ **Important:** The API credentials are currently hardcoded in the demo for convenience. In production:

1. **Use environment variables:**
   ```python
   os.environ["CLICKHOUSE_CLOUD_KEY"] = os.getenv("CLICKHOUSE_KEY")
   os.environ["CLICKHOUSE_CLOUD_SECRET"] = os.getenv("CLICKHOUSE_SECRET")
   ```

2. **Use a `.env` file with `python-dotenv`:**
   ```python
   from dotenv import load_dotenv
   load_dotenv()
   ```

3. **Use a secrets manager** (AWS Secrets Manager, Azure Key Vault, etc.)

4. **Never commit credentials to git** - add to `.gitignore`

## Next Steps

After successfully running the demo:

1. ✅ Explore your logs in the discovery output
2. ✅ Customize field mappings for your schema
3. ✅ Integrate with your production monitoring
4. ✅ Set up alerts for autonomous remediation events
5. ✅ Configure incident signature storage for learning

## Getting Help

If you encounter issues:

1. Check the troubleshooting section above
2. Run the discovery script to inspect your data
3. Review the error messages carefully
4. Check the ClickHouse Cloud console for connectivity

## Additional Resources

- [ClickHouse Cloud Documentation](https://clickhouse.com/docs/en/cloud/overview)
- [Python ClickHouse Driver](https://clickhouse-driver.readthedocs.io/)
- See `CLICKHOUSE_CLOUD_SETUP.md` for detailed API reference

