# Testing Agent Memory - Complete Guide

## 🧪 Test Suite Overview

Test the agent memory functionality to verify it stores, retrieves, and uses past evaluations.

---

## 🚀 Quick Test (3 Steps)

### Step 1: Check Current Memory
```bash
python test_memory_growth.py
```
**Expected**: Shows current memory state (might be empty first time)

### Step 2: Build Memory (Run Demo)
```bash
$env:CLICKHOUSE_SERVICE_ID='a8f1540f-ad53-4e96-bc82-17c8dbf33c7e'
$env:CLICKHOUSE_TABLE_NAME='logs'
python demo_real_data_pipeline.py
```
**Expected**: "Audit results saved: 6"

### Step 3: Verify Memory Growth
```bash
python test_memory_growth.py
```
**Expected**: Shows increased memory count

---

## 📋 Complete Test Sequence

### Test 1: Verify Memory Table Exists

```bash
python setup_audit_table.py
```

**✅ Expected Output:**
```
[OK] Table 'audit_results' created successfully!
[OK] Table structure verified
[OK] Test data inserted
```

---

### Test 2: Check Initial Memory State

```bash
python test_memory_growth.py
```

**✅ Expected Output (First Run):**
```
AGENT MEMORY GROWTH TEST
===============================================================================

Fetching agent's current memory...

[INFO] Agent has no memory yet (empty)
[INFO] Run the demo to build memory:
       python demo_real_data_pipeline.py
```

**OR (If Memory Exists):**
```
[OK] Agent has 16 memories stored

[STATISTICS]
  Total memories: 16
  Anomalies: 0
  Normal: 16
  Anomaly rate: 0.0%

[COMPONENTS IN MEMORY]
  nova.osapi_compute.wsgi.server: 12 evaluations
  test.component: 4 evaluations
```

---

### Test 3: Run Demo to Build Memory

```bash
$env:CLICKHOUSE_SERVICE_ID='a8f1540f-ad53-4e96-bc82-17c8dbf33c7e'
$env:CLICKHOUSE_TABLE_NAME='logs'
python demo_real_data_pipeline.py
```

**✅ Key Output to Look For:**

```
2.2 Retriever Agent: Fetch from ClickHouse
   Fetching from audit_results table (agent memory)...
[OK] Retrieved 10 audit results from memory

   Agent Memory Summary:
     Historical audits: 10
     Past anomalies: 0
     Anomaly rate: 0.0%
     Components monitored: 2

2.3 Auditor Agent: Evaluate events
   Using historical memory to inform evaluations...

[OK] Pipeline Status: SUCCESS
   Total events: 6
   Success rate: 100.0%
   Audit results saved: 6          ← Memory increased by 6!
```

---

### Test 4: Verify Memory Growth

```bash
python test_memory_growth.py
```

**✅ Expected:** Memory count increased

**Example:**
```
[OK] Agent has 22 memories stored    ← Was 16, now 16+6=22

[STATISTICS]
  Total memories: 22
  Anomalies: 0
  Normal: 22
  Anomaly rate: 0.0%
```

---

### Test 5: Query Memory Details

```bash
python query_audit_results.py
```

**✅ Expected Output:**
```
[OK] Found 22 audit result(s)

[STATISTICS]
  Total audits: 22
  Anomalies: 0 (0.0%)
  Normal: 22 (100.0%)

[COMPONENT BREAKDOWN]
  nova.osapi_compute.wsgi.server: 18 audit(s)
  test.component: 4 audit(s)

[LEVEL BREAKDOWN]
  INFO: 22 audit(s)

[MOST RECENT MEMORIES]
  ... (shows recent evaluations)
```

---

### Test 6: Verify Memory Persistence

Run the demo multiple times and check memory grows:

```bash
# Run 1
python demo_real_data_pipeline.py
python test_memory_growth.py    # Shows: 22 memories

# Run 2
python demo_real_data_pipeline.py
python test_memory_growth.py    # Shows: 28 memories (22+6)

# Run 3
python demo_real_data_pipeline.py
python test_memory_growth.py    # Shows: 34 memories (28+6)
```

**✅ Expected:** Memory persists and grows with each run

---

## 🔍 What Each Test Validates

| Test | Validates |
|------|-----------|
| **Test 1** | Table exists and is queryable |
| **Test 2** | Can read current memory state |
| **Test 3** | Agent retrieves and uses memory |
| **Test 4** | Memory grows after evaluations |
| **Test 5** | Can query and analyze memory |
| **Test 6** | Memory persists across runs |

---

## 📊 Expected Demo Output Flow

### 1. Memory Retrieval
```
2.2 Retriever Agent: Fetch from ClickHouse
   Fetching from audit_results table (agent memory)...
[OK] Retrieved X audit results from memory

   Agent Memory Summary:
     Historical audits: X
     Past anomalies: Y
     Anomaly rate: Z%
     Components monitored: N
```
✅ **Validates**: Agent is reading from memory

### 2. Memory-Informed Processing
```
2.3 Auditor Agent: Evaluate events
   Using historical memory to inform evaluations...
```
✅ **Validates**: Agent uses memory for context

### 3. Memory Update
```
[OK] Pipeline Status: SUCCESS
   Total events: 6
   Success rate: 100.0%
   Audit results saved: 6
```
✅ **Validates**: New memories are saved

---

## 🧪 Manual Verification

### Check Memory in ClickHouse Console

1. Go to https://clickhouse.cloud/
2. Open your service
3. Go to SQL Console
4. Run:

```sql
SELECT COUNT(*) FROM audit_results;
```

**✅ Expected:** Shows total memory count

```sql
SELECT * FROM audit_results 
ORDER BY timestamp DESC 
LIMIT 10;
```

**✅ Expected:** Shows recent memories

---

## 🎯 Test Scenarios

### Scenario 1: Fresh Start (No Memory)

**Steps:**
1. Fresh database or cleared table
2. Run `test_memory_growth.py` → Shows "no memory"
3. Run `demo_real_data_pipeline.py` → Builds memory
4. Run `test_memory_growth.py` → Shows 6 memories

**✅ Pass Criteria:** Memory grows from 0 to 6

---

### Scenario 2: Memory Growth

**Steps:**
1. Start with some memory (e.g., 10 memories)
2. Run `test_memory_growth.py` → Shows 10
3. Run demo → Saves 6 more
4. Run `test_memory_growth.py` → Shows 16

**✅ Pass Criteria:** Memory increases by 6 each run

---

### Scenario 3: Memory Retrieval

**Steps:**
1. Build memory (run demo once)
2. Run demo again
3. Check output shows "Retrieved X audit results"

**✅ Pass Criteria:** Retriever fetches from audit_results table

---

### Scenario 4: Memory Persistence

**Steps:**
1. Run demo → Memory = 6
2. Close terminal
3. Open new terminal, run test
4. Memory still = 6

**✅ Pass Criteria:** Memory survives restarts

---

## ⚠️ Troubleshooting

### "Agent has no memory yet"

**Solution:**
```bash
# Create table if missing
python setup_audit_table.py

# Run demo to build memory
python demo_real_data_pipeline.py
```

---

### "Retrieved 0 audit results"

**Possible causes:**
1. Table empty → Run demo first
2. Table doesn't exist → Run setup script
3. Wrong table name → Check environment variables

**Solution:**
```bash
python setup_audit_table.py
python demo_real_data_pipeline.py
```

---

### Memory not growing

**Check:**
1. Demo completed successfully?
2. See "Audit results saved: 6" in output?
3. No errors during save?

**Debug:**
```bash
# Check if saves are working
python query_audit_results.py

# If empty, check ClickHouse connection
python test_clickhouse_connection.py
```

---

## 📈 Performance Test

Test memory with large datasets:

```bash
# Run demo 10 times
for i in {1..10}; do
  python demo_real_data_pipeline.py
  python test_memory_growth.py | grep "Total memories"
done
```

**✅ Expected:** Memory grows linearly (6 per run)

```
Total memories: 6
Total memories: 12
Total memories: 18
Total memories: 24
...
```

---

## ✅ Success Criteria

Your agent memory is working correctly if:

- ✅ Memory table exists and is queryable
- ✅ Demo shows "Fetching from audit_results table"
- ✅ Demo shows memory summary with statistics
- ✅ Demo shows "Audit results saved: 6"
- ✅ Memory count increases after each run
- ✅ Memory persists across sessions
- ✅ Can query memory with filters
- ✅ Recent memories are visible

---

## 🎓 Advanced Tests

### Test Memory Analytics

```python
from integrations.clickhouse import get_audit_results

# Get all memory
memory = get_audit_results(limit=1000)

# Calculate metrics
anomaly_rate = sum(1 for m in memory if m['is_anomaly']) / len(memory)
avg_latency = sum(m['latency_ms'] for m in memory) / len(memory)

print(f"Anomaly Rate: {anomaly_rate*100:.1f}%")
print(f"Avg Latency: {avg_latency:.0f}ms")
```

---

### Test Memory Filtering

```python
# Get only anomalies
anomalies = get_audit_results(filters={"is_anomaly": 1})
print(f"Found {len(anomalies)} anomalous memories")

# Get specific component
component_memory = get_audit_results(
    filters={"component": "nova.osapi_compute.wsgi.server"}
)
print(f"Component has {len(component_memory)} memories")
```

---

## 📝 Test Checklist

- [ ] Memory table created
- [ ] Can check memory state
- [ ] Demo retrieves from memory
- [ ] Demo shows memory summary
- [ ] Demo saves new memories
- [ ] Memory count increases
- [ ] Memory persists
- [ ] Can query with filters
- [ ] Can analyze patterns
- [ ] No errors in output

---

## 🎯 Quick Command Reference

```bash
# Setup
python setup_audit_table.py

# Check memory
python test_memory_growth.py

# Build memory
python demo_real_data_pipeline.py

# Query memory
python query_audit_results.py

# Test connection
python test_clickhouse_connection.py
```

---

## 📚 Documentation

- **This Guide**: `TEST_MEMORY_GUIDE.md`
- **Architecture**: `AGENT_MEMORY_ARCHITECTURE.md`
- **Quick Reference**: `MEMORY_QUICK_REFERENCE.md`
- **Audit Guide**: `AUDIT_RESULTS_GUIDE.md`

---

**Ready to test? Start with:** `python test_memory_growth.py`

