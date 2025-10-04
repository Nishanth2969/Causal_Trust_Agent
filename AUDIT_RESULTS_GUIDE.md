# Audit Results Storage Guide

## Overview

The system now automatically saves all audit results to ClickHouse Cloud after evaluating each event. This provides a complete audit trail and enables historical analysis of anomalies and system behavior.

---

## 🎯 What Gets Saved

After each event is evaluated by the audit agent, the following information is saved to ClickHouse:

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | DateTime | When the audit was performed |
| `event_id` | String | Unique identifier for the event |
| `line_id` | UInt32 | Original log line ID |
| `component` | String | Component that generated the log |
| `level` | String | Log level (INFO, WARNING, ERROR) |
| `is_anomaly` | UInt8 | 1 if anomaly detected, 0 if normal |
| `reason` | String | Why it was flagged (or not) |
| `latency_ms` | UInt32 | Request latency in milliseconds |
| `status` | UInt16 | HTTP status code |

---

## 🚀 Quick Start

### 1. Create the Audit Table

```bash
python setup_audit_table.py
```

This creates the `audit_results` table in your ClickHouse Cloud instance.

### 2. Run the Demo

```bash
# Set environment variables
$env:CLICKHOUSE_SERVICE_ID='a8f1540f-ad53-4e96-bc82-17c8dbf33c7e'
$env:CLICKHOUSE_TABLE_NAME='logs'

# Run demo - audit results will be saved automatically
python demo_real_data_pipeline.py
```

### 3. Query Audit Results

```bash
python query_audit_results.py
```

---

## 📊 Usage Examples

### Save Audit Result (Automatic)

This happens automatically in the demo, but here's how it works:

```python
from integrations.clickhouse import insert_audit_result
from agents.tools import evaluate_event
from datetime import datetime
import time

# Evaluate an event
event = {
    "LineId": 123,
    "Level": "INFO",
    "Component": "nova.api",
    "Content": "Request processed",
    "latency_ms": 150,
    "status": 200
}

result = evaluate_event(event)

# Save the audit result
audit_result = {
    "timestamp": datetime.now().isoformat(),
    "event_id": f"evt_{event['LineId']}_{int(time.time())}",
    "line_id": event['LineId'],
    "component": event['Component'],
    "level": event['Level'],
    "is_anomaly": result['flag'],
    "reason": result['reason'],
    "latency_ms": event['latency_ms'],
    "status": event['status']
}

insert_audit_result(audit_result)
```

### Query All Audit Results

```python
from integrations.clickhouse import get_audit_results

# Get last 100 audits
results = get_audit_results(limit=100)

print(f"Found {len(results)} audit results")
for result in results[:5]:
    print(f"  LineId {result['line_id']}: {result['reason']}")
```

### Query Only Anomalies

```python
from integrations.clickhouse import get_audit_results

# Get only anomalies
anomalies = get_audit_results(limit=50, filters={"is_anomaly": 1})

print(f"Found {len(anomalies)} anomalies")
for anomaly in anomalies:
    print(f"  {anomaly['component']}: {anomaly['reason']}")
```

### Query by Component

```python
# Get audits for specific component
results = get_audit_results(
    limit=100, 
    filters={"component": "nova.osapi_compute.wsgi.server"}
)
```

---

## 📈 Analytics & Insights

### Anomaly Rate Over Time

Query audit results to calculate anomaly rates:

```python
from integrations.clickhouse import get_audit_results

results = get_audit_results(limit=1000)

total = len(results)
anomalies = sum(1 for r in results if r['is_anomaly'] == 1)

print(f"Anomaly Rate: {anomalies/total*100:.2f}%")
```

### Component Health

See which components have the most issues:

```python
from integrations.clickhouse import get_audit_results

results = get_audit_results(limit=1000)

component_anomalies = {}
for r in results:
    if r['is_anomaly'] == 1:
        comp = r['component']
        component_anomalies[comp] = component_anomalies.get(comp, 0) + 1

# Sort by anomaly count
sorted_comps = sorted(component_anomalies.items(), key=lambda x: x[1], reverse=True)

print("Components with most anomalies:")
for comp, count in sorted_comps[:5]:
    print(f"  {comp}: {count} anomalies")
```

### Average Latency

```python
results = get_audit_results(limit=1000)

latencies = [r['latency_ms'] for r in results]
avg_latency = sum(latencies) / len(latencies)

print(f"Average Latency: {avg_latency:.2f}ms")
```

---

## 🔍 Direct ClickHouse Queries

You can also query directly using SQL:

### Get Latest Anomalies

```sql
SELECT * FROM audit_results 
WHERE is_anomaly = 1 
ORDER BY timestamp DESC 
LIMIT 10
```

### Count by Component

```sql
SELECT component, COUNT(*) as total,
       SUM(is_anomaly) as anomalies
FROM audit_results
GROUP BY component
ORDER BY anomalies DESC
```

### Anomaly Rate by Hour

```sql
SELECT 
    toStartOfHour(timestamp) as hour,
    COUNT(*) as total,
    SUM(is_anomaly) as anomalies,
    (SUM(is_anomaly) * 100.0 / COUNT(*)) as anomaly_rate
FROM audit_results
GROUP BY hour
ORDER BY hour DESC
LIMIT 24
```

### High Latency Events

```sql
SELECT * FROM audit_results 
WHERE latency_ms > 300 
ORDER BY latency_ms DESC 
LIMIT 20
```

---

## 🗂️ Table Schema

The `audit_results` table has the following schema:

```sql
CREATE TABLE audit_results (
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
```

**Ordering Key**: `(timestamp, line_id)` - Optimized for time-based queries

---

## 📁 Files

| File | Purpose |
|------|---------|
| `setup_audit_table.py` | Creates the audit_results table |
| `query_audit_results.py` | Query and analyze audit results |
| `demo_real_data_pipeline.py` | Automatically saves audits |
| `integrations/clickhouse.py` | Core audit storage functions |

---

## 🔧 Configuration

Required environment variables:

```bash
# Windows PowerShell
$env:CLICKHOUSE_CLOUD_KEY='kRuHI0HdODEAJokHcaTy'
$env:CLICKHOUSE_CLOUD_SECRET='4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh'
$env:CLICKHOUSE_SERVICE_ID='a8f1540f-ad53-4e96-bc82-17c8dbf33c7e'

# Linux/Mac
export CLICKHOUSE_CLOUD_KEY='kRuHI0HdODEAJokHcaTy'
export CLICKHOUSE_CLOUD_SECRET='4b1dXAP2m2VaW6vYROdsTDJwMk80Cle9ABGhgAEMlh'
export CLICKHOUSE_SERVICE_ID='a8f1540f-ad53-4e96-bc82-17c8dbf33c7e'
```

---

## 🎯 Use Cases

### 1. Incident Investigation

Query audit results to understand what happened during an incident:

```python
# Get anomalies from specific time window
results = get_audit_results(limit=1000)
incident_time_audits = [
    r for r in results 
    if "2025-10-04 15:00" in str(r['timestamp'])
]
```

### 2. System Health Monitoring

Track anomaly rates over time to monitor system health.

### 3. Component Performance

Identify which components generate the most anomalies or have highest latencies.

### 4. Audit Trail

Maintain complete audit trail for compliance and debugging.

### 5. ML Training Data

Use historical audit results to train anomaly detection models.

---

## 🔄 Integration with Demo

The demo (`demo_real_data_pipeline.py`) automatically:

1. **Fetches logs** from ClickHouse Cloud
2. **Evaluates each event** using the audit agent
3. **Saves audit result** to `audit_results` table
4. **Reports statistics** at the end

**Output Example:**
```
2.3 Auditor Agent: Evaluate events
   Event 1: ANOMALY - Level=ERROR

[OK] Pipeline Status: SUCCESS
   Total events: 6
   Success rate: 100.0%
   Audit results saved: 6
```

---

## 📊 Viewing Results

### In Code

```bash
python query_audit_results.py
```

### In ClickHouse Cloud Console

1. Go to https://clickhouse.cloud/
2. Open your service
3. Go to SQL Console
4. Run: `SELECT * FROM audit_results ORDER BY timestamp DESC LIMIT 10`

---

## 🐛 Troubleshooting

### No Audit Results Saved

**Check:**
1. Table exists: `python setup_audit_table.py`
2. Environment variables set correctly
3. ClickHouse connection working: `python test_clickhouse_connection.py`

### Can't Query Audit Results

**Check:**
1. Table exists: Run `SHOW TABLES` in ClickHouse
2. Connection established: Check `query_audit_results.py` output
3. Try direct SQL query in ClickHouse console

### Warnings During Save

Small warnings are normal - INSERT queries return empty responses on success.

---

## 🚀 Next Steps

1. ✅ Create audit_results table
2. ✅ Run demo to generate audit data
3. ✅ Query and analyze results
4. Build dashboards using audit data
5. Set up alerts for high anomaly rates
6. Export data for ML training

---

## 📖 API Reference

### `insert_audit_result(audit_result)`

Save an audit result to ClickHouse.

**Parameters:**
- `audit_result` (dict): Audit result with required fields

**Example:**
```python
insert_audit_result({
    "timestamp": "2025-10-04T15:00:00",
    "event_id": "evt_123",
    "line_id": 123,
    "component": "api.server",
    "level": "ERROR",
    "is_anomaly": True,
    "reason": "High latency",
    "latency_ms": 450,
    "status": 500
})
```

### `get_audit_results(limit=100, filters=None)`

Fetch audit results from ClickHouse.

**Parameters:**
- `limit` (int): Maximum results to return
- `filters` (dict): Optional WHERE clause filters

**Returns:** List of audit result dictionaries

**Example:**
```python
# Get all anomalies
anomalies = get_audit_results(limit=50, filters={"is_anomaly": 1})

# Get specific component
results = get_audit_results(filters={"component": "nova.api"})
```

---

## ✅ Summary

- ✅ **Automatic Saving**: Audit results saved after every evaluation
- ✅ **Complete Trail**: All evaluations stored for analysis
- ✅ **Easy Querying**: Python API and SQL access
- ✅ **Analytics Ready**: Query for insights and monitoring
- ✅ **Production Ready**: Scalable ClickHouse storage

**The audit system is fully operational and ready for production use!**

