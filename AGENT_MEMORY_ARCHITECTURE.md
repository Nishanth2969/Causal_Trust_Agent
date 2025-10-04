# Agent Memory Architecture

## Overview

The `audit_results` table serves as the **agent's memory** - a persistent knowledge base that the system uses to learn from past evaluations and inform future decisions.

---

## 🧠 Memory Concept

### Traditional Approach (Before)
```
Raw Logs → Agent → Evaluation → Output (lost)
```
Every evaluation was performed in isolation with no memory of past decisions.

### Agent Memory Approach (Now)
```
Raw Logs → Agent → Evaluation → audit_results table
                      ↑                    ↓
                      └────────────────────┘
                    (Retrieves from memory)
```

The agent builds a persistent memory by:
1. **Storing** every evaluation result in `audit_results`
2. **Retrieving** historical evaluations to inform new decisions
3. **Learning** patterns from past anomalies and normal behavior

---

## 📊 Data Flow

### Phase 1: Initial Data Ingestion
```
ClickHouse Cloud (logs table)
         ↓
   Fetch raw logs
         ↓
   Transform to events
         ↓
   Ready for evaluation
```

### Phase 2: Agent Pipeline with Memory
```
┌──────────────────────────────────────────┐
│  INTAKE AGENT                            │
│  - Receives new events                   │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  RETRIEVER AGENT                         │
│  - Fetches from audit_results            │◄─── Agent Memory
│  - Retrieves historical evaluations      │     (audit_results table)
│  - Analyzes patterns                     │
└──────────────┬───────────────────────────┘
               ↓
┌──────────────────────────────────────────┐
│  AUDITOR AGENT                           │
│  - Uses memory to inform decisions       │
│  - Evaluates new events                  │
│  - Saves results back to memory          │─────► Stores in
└──────────────┬───────────────────────────┘      audit_results
               ↓
         New evaluation stored
               ↓
         Memory updated
```

---

## 🗄️ The audit_results Table (Agent Memory)

### What It Stores

| Field | Description | Purpose |
|-------|-------------|---------|
| `timestamp` | When evaluation occurred | Temporal patterns |
| `event_id` | Unique event identifier | Traceability |
| `line_id` | Source log line ID | Reference |
| `component` | Component name | Component health tracking |
| `level` | Log level | Severity analysis |
| `is_anomaly` | Anomaly flag | Pattern learning |
| `reason` | Why flagged/not flagged | Decision explanation |
| `latency_ms` | Request latency | Performance trends |
| `status` | HTTP status | Success/failure patterns |

### Why It's Memory

1. **Historical Context**: Agent knows what it evaluated before
2. **Pattern Recognition**: Identifies recurring issues
3. **Learning**: Improves over time based on past decisions
4. **Anomaly Detection**: Compares current vs. historical patterns
5. **Component Health**: Tracks which components fail most
6. **Performance Trends**: Monitors latency over time

---

## 🔄 How Memory is Used

### 1. Retrieval Phase
```python
# Agent retrieves its memory
retrieved = get_audit_results(limit=10)

# Analyzes historical patterns
anomaly_count = sum(1 for r in retrieved if r['is_anomaly'] == 1)
anomaly_rate = anomaly_count / len(retrieved)
```

### 2. Context-Aware Evaluation
```python
# Agent uses memory to inform decisions
# Example: If component historically has high anomaly rate,
# agent can be more/less sensitive to new events
```

### 3. Memory Update
```python
# After evaluation, agent updates its memory
insert_audit_result(audit_result)
```

---

## 🎯 Benefits of Agent Memory

### 1. Learning from Past
- **Pattern Recognition**: Identifies recurring anomalies
- **Baseline Establishment**: Knows what's "normal"
- **Trend Detection**: Spots gradual degradation

### 2. Intelligent Decision Making
- **Context-Aware**: Uses historical data for decisions
- **Adaptive**: Adjusts sensitivity based on patterns
- **Informed**: Not evaluating in isolation

### 3. Incident Response
- **Faster Detection**: Recognizes known issues instantly
- **Better RCA**: Has historical context for analysis
- **Predictive**: Can anticipate issues based on trends

### 4. Continuous Improvement
- **Self-Learning**: Gets better over time
- **Knowledge Accumulation**: Builds expertise
- **Pattern Library**: Creates catalog of known issues

---

## 📈 Memory Growth Over Time

### First Run
```
audit_results: 0 records
Agent: No memory, baseline evaluation
```

### After 1 Day
```
audit_results: ~1,000 records
Agent: Basic patterns established
```

### After 1 Week
```
audit_results: ~10,000 records
Agent: Strong patterns, component baselines
```

### After 1 Month
```
audit_results: ~50,000 records
Agent: Sophisticated pattern recognition
```

---

## 🔍 Memory Query Examples

### Get Recent Memory
```python
# Last 100 evaluations
recent_memory = get_audit_results(limit=100)
```

### Query Anomaly History
```python
# Past anomalies for pattern analysis
anomalies = get_audit_results(limit=500, filters={"is_anomaly": 1})
```

### Component-Specific Memory
```python
# Memory for specific component
component_memory = get_audit_results(
    filters={"component": "nova.api"}
)
```

### Performance Trends
```python
# High latency events in memory
slow_events = get_audit_results(
    filters={"latency_ms": ">300"}
)
```

---

## 🧪 Demo Output

### Phase 2: Memory Retrieval
```
2.2 Retriever Agent: Fetch from ClickHouse
   Fetching from audit_results table (agent memory)...
[OK] Retrieved 7 audit results from memory

   Agent Memory Summary:
     Historical audits: 7
     Past anomalies: 0
     Anomaly rate: 0.0%
     Components monitored: 2
```

### Phase 2: Memory-Informed Evaluation
```
2.3 Auditor Agent: Evaluate events
   Using historical memory to inform evaluations...
```

---

## 🏗️ Architecture Principles

### 1. Persistent Memory
- **Not ephemeral**: Survives restarts
- **ClickHouse**: Scalable, production-ready storage
- **Queryable**: Easy to access and analyze

### 2. Write-Through Cache
- **Every evaluation saved**: No data loss
- **Immediate availability**: Memory updated in real-time
- **Consistent**: What's evaluated is what's remembered

### 3. Temporal Awareness
- **Timestamp ordering**: Recent memory prioritized
- **Historical analysis**: Can look back in time
- **Trend detection**: Monitors changes over time

### 4. Component Isolation
- **Per-component memory**: Tracks each component separately
- **Isolated baselines**: Each component has own "normal"
- **Targeted queries**: Filter by component for analysis

---

## 🔄 Memory Lifecycle

### 1. Creation
```python
# Event evaluated → Result saved
insert_audit_result(audit_result)
```

### 2. Retrieval
```python
# Agent fetches memory
memory = get_audit_results(limit=100)
```

### 3. Analysis
```python
# Agent analyzes patterns
anomaly_rate = calculate_anomaly_rate(memory)
component_health = analyze_components(memory)
```

### 4. Decision
```python
# Agent uses memory to inform new evaluations
result = evaluate_event(event, context=memory)
```

### 5. Update
```python
# New evaluation added to memory
insert_audit_result(new_result)
```

---

## 📊 Memory Analytics

### Anomaly Rate Over Time
```sql
SELECT 
    toStartOfHour(timestamp) as hour,
    (SUM(is_anomaly) * 100.0 / COUNT(*)) as anomaly_rate
FROM audit_results
GROUP BY hour
ORDER BY hour DESC
```

### Component Health Score
```sql
SELECT 
    component,
    COUNT(*) as total_audits,
    SUM(is_anomaly) as anomalies,
    (SUM(is_anomaly) * 100.0 / COUNT(*)) as anomaly_rate,
    AVG(latency_ms) as avg_latency
FROM audit_results
GROUP BY component
ORDER BY anomaly_rate DESC
```

### Recent Memory Snapshot
```sql
SELECT * FROM audit_results 
ORDER BY timestamp DESC 
LIMIT 10
```

---

## 🎯 Use Cases

### 1. Baseline Learning
Agent establishes what "normal" looks like for each component.

### 2. Anomaly Detection
Compares current behavior against historical memory to detect anomalies.

### 3. Root Cause Analysis
Uses memory to identify patterns leading to incidents.

### 4. Predictive Monitoring
Detects gradual degradation before complete failure.

### 5. Autonomous Remediation
Learns from past fixes to apply them faster in future.

---

## ✅ Implementation Details

### In Code
```python
# demo_real_data_pipeline.py

# Retriever fetches from memory
retrieved = get_audit_results(limit=10)

# Auditor uses memory context
print("Using historical memory to inform evaluations...")

# After evaluation, update memory
insert_audit_result(audit_result)
```

### In ClickHouse
```
audit_results table = Agent's persistent memory
- Every evaluation stored
- Queryable by time, component, anomaly status
- Scales to millions of records
```

---

## 🚀 Getting Started

### 1. Create Memory Table
```bash
python setup_audit_table.py
```

### 2. Run Agent (Builds Memory)
```bash
python demo_real_data_pipeline.py
```

### 3. Query Memory
```bash
python query_audit_results.py
```

### 4. Analyze Patterns
```python
from integrations.clickhouse import get_audit_results

memory = get_audit_results(limit=1000)
# Analyze patterns, trends, anomalies
```

---

## 📖 Summary

**The `audit_results` table is the agent's memory:**

✅ **Persistent**: Survives across runs  
✅ **Queryable**: Easy to retrieve and analyze  
✅ **Learning**: Agent improves over time  
✅ **Context**: Informs every new evaluation  
✅ **Scalable**: Handles millions of records  
✅ **Production-Ready**: Built on ClickHouse  

**The agent is no longer stateless - it has memory and learns from experience!**

