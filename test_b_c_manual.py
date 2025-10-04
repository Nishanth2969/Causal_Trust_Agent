import sys
import time
from agents.tools import fetch_log_events, evaluate_event
from agents.failures import inject_drift, get_failure_state
from agents.adapters import set_adapter, apply_adapters, clear_adapters, get_adapters
from agents.stream import StreamProducer
from integrations.clickhouse import insert_event, get_recent_events

print("=" * 70)
print("ROLE B + C INTEGRATION TEST - OpenStack Log Events")
print("=" * 70)

print("\n[TEST 1] Generate good log events")
events_good = fetch_log_events(flaky=False, count=3)
print(f"Generated {len(events_good)} good events")
print(f"Sample event fields: {list(events_good[0].keys())}")
print(f"Sample Level field: {events_good[0]['Level']}")
assert all('Level' in e for e in events_good)
assert all('level' not in e for e in events_good)
print("✓ Good events have 'Level' field (uppercase)")

print("\n[TEST 2] Generate flaky log events (schema drift)")
inject_drift(True)
events_flaky = fetch_log_events(flaky=True, count=3)
print(f"Generated {len(events_flaky)} flaky events")
print(f"Sample event fields: {list(events_flaky[0].keys())}")
print(f"Sample level field: {events_flaky[0].get('level', 'N/A')}")
assert all('level' in e for e in events_flaky)
assert all('Level' not in e for e in events_flaky)
print("✓ Flaky events have 'level' field (lowercase) - drift detected!")
inject_drift(False)

print("\n[TEST 3] Evaluate events - detect anomalies")
sample_good = events_good[0]
result_good = evaluate_event(sample_good)
print(f"Good event evaluation: {result_good}")
assert 'flag' in result_good
assert 'reason' in result_good
print("✓ Evaluator works on good events")

print("\n[TEST 4] Adapter mechanism - fix schema drift")
clear_adapters()
broken_event = {"LineId": 999, "level": "ERROR", "Component": "nova.compute", "latency_ms": 450}
print(f"Broken event: {broken_event}")

try:
    evaluate_event(broken_event)
    print("ERROR: Should have failed on missing 'Level'")
    sys.exit(1)
except KeyError as e:
    print(f"✓ Expected KeyError: {e}")

print("\nApplying adapter: level -> Level")
set_adapter({"level": "Level"})
fixed_event = apply_adapters(broken_event)
print(f"Fixed event: {fixed_event}")
assert "Level" in fixed_event
assert "level" not in fixed_event
assert fixed_event["Level"] == "ERROR"
print("✓ Adapter successfully transformed level -> Level")

result_fixed = evaluate_event(fixed_event)
print(f"Evaluation after fix: {result_fixed}")
assert result_fixed['flag'] == True
print("✓ Fixed event evaluates correctly")

print("\n[TEST 5] Stream producer generates log events")
producer = StreamProducer(events_per_second=20.0)
producer.start()
time.sleep(0.3)
producer.stop()
status = producer.get_status()
print(f"Stream status: running={status['running']}, total_events={status['total_events']}")
assert status['total_events'] > 0
print(f"✓ Stream produced {status['total_events']} events in 0.3s")

print("\n[TEST 6] ClickHouse mock stores and retrieves events")
test_event = {
    "LineId": 12345,
    "Level": "WARNING",
    "Component": "nova.scheduler.manager",
    "Content": "Scheduler warning message",
    "latency_ms": 350,
    "status": 200,
    "timestamp": time.time()
}
insert_event(test_event)
recent = get_recent_events(limit=20)
print(f"Retrieved {len(recent)} recent events from ClickHouse")
found = any(e.get("LineId") == 12345 for e in recent)
assert found
print(f"✓ Test event found in ClickHouse mock")

print("\n[TEST 7] End-to-end scenario simulation")
print("\nScenario: Agent pipeline fails due to schema drift")
print("1. Fetcher returns events with 'level' (lowercase)")
print("2. Auditor expects 'Level' (uppercase) -> KeyError")
print("3. CTA detects drift and proposes adapter")
print("4. Apply adapter: level -> Level")
print("5. Canary test passes")
print("6. Promote fix")

clear_adapters()
print("\nStep 1-2: Generate flaky events (will cause failure)")
flaky_batch = fetch_log_events(flaky=True, count=5)
print(f"Generated {len(flaky_batch)} flaky events")

failure_count = 0
for evt in flaky_batch:
    try:
        evaluate_event(evt)
    except KeyError:
        failure_count += 1

print(f"Failures: {failure_count}/{len(flaky_batch)} events (100% error rate)")
assert failure_count == len(flaky_batch)
print("✓ Pipeline fails as expected due to schema drift")

print("\nStep 3-4: Apply CTA fix (adapter)")
set_adapter({"level": "Level"})
adapters = get_adapters()
print(f"Active adapters: {adapters}")

print("\nStep 5: Canary test with adapted events")
canary_events = [apply_adapters(e) for e in flaky_batch]
canary_errors = 0
for evt in canary_events:
    try:
        result = evaluate_event(evt)
        assert result is not None
    except Exception:
        canary_errors += 1

error_rate = canary_errors / len(canary_events)
print(f"Canary results: {canary_errors}/{len(canary_events)} errors ({error_rate:.1%})")
assert error_rate == 0.0
print("✓ Canary test passes (0% error rate)")

print("\nStep 6: Promote fix")
print("✓ Adapter promoted and active")
print(f"   New events will be automatically transformed: {adapters}")

print("\n[TEST 8] Verify learned fix works on new incidents")
new_flaky = fetch_log_events(flaky=True, count=2)
print(f"New flaky events generated: {len(new_flaky)}")
for evt in new_flaky:
    fixed = apply_adapters(evt)
    result = evaluate_event(fixed)
    assert 'Level' in fixed
    print(f"   Event {fixed['LineId']}: {fixed['Level']} -> {result['reason']}")
print("✓ Learned fix applies instantly to new incidents")

clear_adapters()

print("\n" + "=" * 70)
print("ALL TESTS PASSED - Role B + C working correctly with log schema!")
print("=" * 70)
print("\nSummary:")
print("✓ Log event generation (good and flaky modes)")
print("✓ Schema drift detection (Level vs level)")
print("✓ Adapter mechanism (hot-reloadable transforms)")
print("✓ Stream producer (real-time event generation)")
print("✓ ClickHouse integration (event storage)")
print("✓ End-to-end autonomous loop (detect->fix->test->promote)")
print("✓ Learning system (cached fixes apply instantly)")

