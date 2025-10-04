# Agent Memory - Quick Reference

## 🧠 Key Concept

**`audit_results` table = Agent's Memory**

The agent retrieves from this table to inform decisions and stores back to it after evaluations.

---

## 🔄 Data Flow

```
┌─────────────────┐
│   Raw Logs      │
│  (logs table)   │
└────────┬────────┘
         ↓
    Fetch & Transform
         ↓
┌─────────────────┐
│  Intake Agent   │
└────────┬────────┘
         ↓
┌─────────────────┐     ┌──────────────────┐
│ Retriever Agent │────→│  audit_results   │
│                 │     │  (Agent Memory)  │
└────────┬────────┘     └──────────────────┘
         ↓                        ↑
┌─────────────────┐              │
│  Auditor Agent  │──────────────┘
│  (evaluates &   │   Stores results
│   saves)        │
└─────────────────┘
```

---

## 📊 What You See in Demo

### Memory Retrieval
```
2.2 Retriever Agent: Fetch from ClickHouse
   Fetching from audit_results table (agent memory)...
[OK] Retrieved 10 audit results from memory

   Agent Memory Summary:
     Historical audits: 10
     Past anomalies: 0
     Anomaly rate: 0.0%
     Components monitored: 2
```

### Memory-Informed Evaluation
```
2.3 Auditor Agent: Evaluate events
   Using historical memory to inform evaluations...
```

### Memory Update
```
[OK] Pipeline Status: SUCCESS
   Total events: 6
   Success rate: 100.0%
   Audit results saved: 6      ← New memories created
```

---

## 💡 Why This Matters

### Before (Stateless)
❌ Agent forgets after each run  
❌ No learning from past  
❌ Evaluates in isolation  
❌ No historical context  

### After (With Memory)
✅ Agent remembers all evaluations  
✅ Learns from historical patterns  
✅ Context-aware decisions  
✅ Tracks component health over time  

---

## 🎯 Memory Functions

### Retrieve Memory
```python
from integrations.clickhouse import get_audit_results

# Get recent memory
memory = get_audit_results(limit=100)

# Get anomalies only
anomalies = get_audit_results(filters={"is_anomaly": 1})

# Get specific component
comp_memory = get_audit_results(filters={"component": "nova.api"})
```

### Save to Memory
```python
from integrations.clickhouse import insert_audit_result

# Save evaluation result
insert_audit_result({
    "timestamp": datetime.now().isoformat(),
    "event_id": "evt_123",
    "line_id": 123,
    "component": "nova.api",
    "level": "INFO",
    "is_anomaly": False,
    "reason": "latency=100ms",
    "latency_ms": 100,
    "status": 200
})
```

---

## 📈 Memory Analytics

### Check Memory Size
```python
memory = get_audit_results(limit=10000)
print(f"Agent has {len(memory)} memories")
```

### Anomaly Rate
```python
anomalies = sum(1 for m in memory if m['is_anomaly'] == 1)
rate = anomalies / len(memory) * 100
print(f"Historical anomaly rate: {rate:.1f}%")
```

### Component Health
```python
components = {}
for m in memory:
    comp = m['component']
    components[comp] = components.get(comp, 0) + 1
    
print("Components in memory:")
for comp, count in components.items():
    print(f"  {comp}: {count} evaluations")
```

---

## 🗄️ Memory Schema

```
audit_results (Agent Memory)
├── timestamp       (When evaluated)
├── event_id        (Unique ID)
├── line_id         (Source log ID)
├── component       (Component name)
├── level           (Log level)
├── is_anomaly      (0 or 1)
├── reason          (Why flagged)
├── latency_ms      (Performance)
└── status          (HTTP status)
```

---

## 🚀 Quick Commands

```bash
# Create memory table
python setup_audit_table.py

# Run agent (builds memory)
python demo_real_data_pipeline.py

# Query memory
python query_audit_results.py

# View memory in ClickHouse
# SQL: SELECT * FROM audit_results ORDER BY timestamp DESC LIMIT 10
```

---

## ✅ Verification

After running the demo, you should see:

1. ✅ "Fetching from audit_results table (agent memory)..."
2. ✅ "Retrieved X audit results from memory"
3. ✅ Agent Memory Summary with statistics
4. ✅ "Using historical memory to inform evaluations..."
5. ✅ "Audit results saved: X"

---

## 📚 Full Documentation

- **Architecture**: `AGENT_MEMORY_ARCHITECTURE.md`
- **Audit Guide**: `AUDIT_RESULTS_GUIDE.md`
- **This Reference**: `MEMORY_QUICK_REFERENCE.md`

---

## 💡 Key Insight

**The agent is no longer stateless!**

Every evaluation becomes part of the agent's growing knowledge base, enabling it to learn, adapt, and make better decisions over time.

---

**Memory = Learning = Intelligence** 🧠

