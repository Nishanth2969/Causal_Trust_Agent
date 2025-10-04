# ClickHouse Cloud Integration Guide

This guide explains how to integrate your ClickHouse Cloud logs with the Causal Trust Agent pipeline.

## Overview

The system now fetches real logs from ClickHouse Cloud instead of using dummy CSV data. The agent processes these logs and applies autonomous remediation when issues are detected.

## Setup

### 1. Credentials

Your ClickHouse Cloud credentials are already configured in the code:

```bash
CLICKHOUSE_CLOUD_KEY="kRuHI0HdODEAJokHcaTy"
CLICKHOUSE_CLOUD_SECRET="4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh"
```

These are automatically set when running `demo_real_data_pipeline.py`.

### 2. Discover Your Tables

Before running the main demo, you should discover what tables are available in your ClickHouse Cloud instance:

```bash
python discover_clickhouse_tables.py
```

This script will:
- List all available databases
- Show all tables in your current database
- Display the structure (schema) of each table
- Show sample data from each table
- Count total rows in each table

**Example Output:**
```
Available tables:
logs
events
system_metrics

📊 Table: logs
   Structure:
   timestamp DateTime
   level String
   message String
   service String
   ...
   
   Sample data (2 rows):
   Row 1:
      timestamp: 2024-10-04 10:30:15
      level: INFO
      message: Request processed successfully
      service: api-gateway
```

### 3. Configure Table Name

Once you've identified your logs table, set it as an environment variable:

```bash
# On Linux/Mac
export CLICKHOUSE_TABLE_NAME="your_table_name"

# On Windows (PowerShell)
$env:CLICKHOUSE_TABLE_NAME="your_table_name"

# On Windows (CMD)
set CLICKHOUSE_TABLE_NAME=your_table_name
```

Or modify it directly in `demo_real_data_pipeline.py`:
```python
TABLE_NAME = os.getenv("CLICKHOUSE_TABLE_NAME", "your_table_name_here")
```

### 4. Run the Demo

```bash
python demo_real_data_pipeline.py
```

The demo will:
1. **Fetch logs** from ClickHouse Cloud
2. **Transform** them to match the expected format
3. **Process** them through the agent pipeline
4. **Detect** and remediate issues automatically
5. **Learn** from incidents for faster resolution next time

## How It Works

### Data Flow

```
ClickHouse Cloud → fetch_logs_from_cloud() → Transform to standard format → Agent Pipeline
```

### Log Transformation

The system automatically maps common log field names to the expected format:

| Expected Field | Alternative Names Checked |
|---------------|--------------------------|
| `Level` | `level`, `severity` |
| `Component` | `component`, `service` |
| `Content` | `message`, `content` |
| `latency_ms` | `latency_ms`, `duration_ms` |
| `status` | `status`, `status_code` |

### Fallback Mechanism

If ClickHouse Cloud is unavailable or no logs are found, the system automatically falls back to the dummy CSV data to ensure the demo can still run.

## Integration in Your Own Code

### Basic Usage

```python
import os
from integrations.clickhouse import fetch_logs_from_cloud

# Set credentials
os.environ["CLICKHOUSE_CLOUD_KEY"] = "your_key"
os.environ["CLICKHOUSE_CLOUD_SECRET"] = "your_secret"

# Fetch logs
logs = fetch_logs_from_cloud(
    table_name="logs",
    limit=100,
    filters={"level": "ERROR"}  # Optional filters
)

# Process logs
for log in logs:
    print(f"Log: {log}")
```

### Advanced Usage with Filters

```python
# Fetch logs with multiple filters
logs = fetch_logs_from_cloud(
    table_name="application_logs",
    limit=500,
    filters={
        "level": "ERROR",
        "service": "payment-service"
    }
)
```

### Integration with Agent Pipeline

```python
from agents.tools import evaluate_event
from agents.adapters import apply_adapters

# Fetch and process
logs = fetch_logs_from_cloud("logs", limit=100)

for log in logs:
    # Transform log to event format
    event = {
        "Level": log.get("level", "INFO"),
        "Component": log.get("service", "unknown"),
        "Content": log.get("message", ""),
        "latency_ms": log.get("duration_ms", 100),
        "status": log.get("status_code", 200),
        "timestamp": log.get("timestamp", time.time())
    }
    
    # Apply any active adapters (for schema drift fixes)
    fixed_event = apply_adapters(event)
    
    # Evaluate with agent
    result = evaluate_event(fixed_event)
    
    if result['flag']:
        print(f"Anomaly detected: {result['reason']}")
```

## API Reference

### `fetch_logs_from_cloud(table_name, limit=100, filters=None)`

Fetch logs from ClickHouse Cloud.

**Parameters:**
- `table_name` (str): Name of the table containing logs
- `limit` (int): Maximum number of logs to fetch (default: 100)
- `filters` (dict): Optional key-value pairs for WHERE clause filtering

**Returns:**
- List[Dict]: List of log records as dictionaries

**Example:**
```python
logs = fetch_logs_from_cloud(
    table_name="application_logs",
    limit=200,
    filters={"severity": "ERROR", "component": "api"}
)
```

### `get_recent_events(limit=20, table_name=None)`

Get recent events from storage (ClickHouse Cloud or local cache).

**Parameters:**
- `limit` (int): Maximum number of events to retrieve
- `table_name` (str): Table name (required for cloud queries)

**Returns:**
- List[Dict]: List of events

## Troubleshooting

### Connection Issues

If you see "Not connected to ClickHouse Cloud":
1. Verify your credentials are correct
2. Check network connectivity
3. Ensure the ClickHouse Cloud host URL is correct

### No Tables Found

If no tables are listed:
1. Verify you're using the correct credentials
2. Check that your ClickHouse instance has data
3. Try accessing the ClickHouse Cloud UI to verify table existence

### Schema Mismatch

If logs don't process correctly:
1. Run `discover_clickhouse_tables.py` to see the actual schema
2. Update the field mapping in `demo_real_data_pipeline.py`
3. Add custom transformations for your specific log format

### Sample Custom Transformation

```python
# In demo_real_data_pipeline.py
for i, log in enumerate(cloud_logs):
    event = {
        "LineId": i + 1,
        "timestamp": log.get("event_time"),  # Custom field name
        "Level": log.get("log_level"),       # Custom field name
        "Component": log.get("app_name"),    # Custom field name
        "Content": log.get("msg"),           # Custom field name
        "latency_ms": log.get("response_time", 100),
        "status": log.get("http_status", 200),
    }
    events.append(event)
```

## Security Notes

- Credentials are currently hardcoded for demo purposes
- In production, use environment variables or secure secret management
- Never commit credentials to version control
- Consider using `.env` files with `python-dotenv` for local development

## Next Steps

1. ✅ Set up ClickHouse Cloud credentials (done)
2. ✅ Discover your tables with `discover_clickhouse_tables.py`
3. ✅ Configure the table name
4. ✅ Run the demo with real data
5. Monitor the autonomous remediation in action
6. Customize field mappings for your specific log format
7. Integrate with your production monitoring pipeline

## Support

For issues or questions:
- Check the logs output from the discovery script
- Review the field mapping in the demo script
- Ensure your ClickHouse table has the required fields or add custom mappings

