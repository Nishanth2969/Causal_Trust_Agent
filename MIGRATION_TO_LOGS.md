# Migration from Finance Transactions to OpenStack Log Events

## Summary

Successfully migrated the CTA-ACT system from synthetic finance transaction data to OpenStack-style log event data, aligning with the original project vision of agent incident detection and remediation.

## Data Model Changes

### Before (Finance Transactions)
```python
{
    "id": "T1234",
    "currency": "USD",
    "amount": 42.5,
    "timestamp": 1733345678.123,
    "merchant": "Amazon"
}
```

### After (OpenStack Log Events)
```python
{
    "LineId": 1234,
    "Date": "2017-05-16",
    "Time": "00:00:45.123",
    "Pid": 25746,
    "Level": "INFO",
    "Component": "nova.compute.manager",
    "Content": '"GET /v2/servers/detail HTTP/1.1" status: 200 len: 1893 time: 0.247',
    "latency_ms": 247,
    "status": 200,
    "timestamp": 1733345678.123
}
```

## Schema Drift Change

### Before
- Normal: `amount` field
- Flaky: `amt` field (renamed)
- Adapter: `{"amt": "amount"}`

### After
- Normal: `Level` field (uppercase)
- Flaky: `level` field (lowercase)
- Adapter: `{"level": "Level"}`

## Files Modified

### Core Agent Files
1. **agents/tools.py**
   - Renamed `fetch_transactions` → `fetch_log_events`
   - Renamed `flag_anomaly` → `evaluate_event`
   - Changed to generate OpenStack log-like events
   - Updated schema drift logic

2. **agents/graph.py**
   - Updated imports and function calls
   - Changed variable names: `transactions/txs` → `events/evts`
   - Updated field references: `id` → `LineId`

3. **agents/stream.py**
   - Renamed `_generate_transaction` → `_generate_log_event`
   - Updated to generate log events instead of transactions

4. **agents/canary.py**
   - Updated variable names for consistency

### CTA Analysis Files
5. **cta/analyze.py**
   - Updated heuristic detection from `amt/amount` to `level/Level`
   - Changed tool name check to `fetch_log_events`
   - Updated why-chain and proposed fix messages

### Test Files
6. **tests/test_role_b.py**
   - Updated all test data to use log event structure
   - Changed adapter assertions

7. **tests/test_role_c.py**
   - Updated adapter parsing tests
   - Changed event structures in all tests

8. **tests/test_integration_b_c.py**
   - Updated integration test data
   - Changed adapter expectations

9. **tests/test_cta_heuristics.py**
   - Updated all test events to log format
   - Changed field assertions

## Verification

Tested basic functionality:
```bash
python -c "from agents.tools import fetch_log_events, evaluate_event; 
events = fetch_log_events(flaky=False, count=3); 
print('Fields:', list(events[0].keys()))"
```

Output confirms:
- Good events have `Level` field (uppercase)
- Flaky events have `level` field (lowercase)
- Adapter correctly transforms `level` → `Level`

## Behavioral Consistency

The autonomous action loop remains unchanged:
1. Detect failure (KeyError on missing 'Level')
2. RCA identifies schema drift (level vs Level)
3. Apply adapter patch
4. Canary test on recent events
5. Promote or rollback based on results
6. Learn and cache the fix

## Next Steps for Role A (Observability)

Role A should emit OpenTelemetry/Datadog spans using these fields:
- `resource`: Component (e.g., nova.compute.manager)
- `tags.level`: INFO/WARNING/ERROR
- `tags.status`: HTTP status code
- `span.duration`: latency_ms
- `error`: when Level=ERROR or status>=500

See ROLE_A_DATA_INGESTION.md for detailed guidance.

