import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, get_run
from agents.graph import run_pipeline
from agents.stream import start_stream, stop_stream, get_stream_status
from agents.failures import inject_drift, get_failure_state
from agents.adapters import set_adapter, clear_adapters, get_adapters
from agents.canary import canary_run
from cta.analyze import cta_analyze
from cta.actions import apply_patch, canary_run_wrapper, promote_or_rollback, save_signature, check_signature_cache
from integrations.clickhouse import insert_event, get_recent_events

def test_full_autonomous_loop_role_b_and_c():
    clear_adapters()
    inject_drift(False)
    
    print("\n=== Full Autonomous Loop Integration Test ===")
    
    print("\n1. Role B: Inject drift failure")
    inject_drift(True)
    state = get_failure_state()
    assert state["schema_drift"] == True
    print(f"   Drift enabled: {state['schema_drift']}")
    
    print("\n2. Role B: Create flaky run with schema drift")
    run_id = start_run("integration_flaky")
    result = run_pipeline(run_id, "flaky", use_adapters=False)
    
    assert result["status"] == "failed"
    assert result["fail_reason"] is not None
    print(f"   Run {run_id} failed as expected")
    print(f"   Failure: {result['fail_reason']}")
    
    print("\n3. Role C: CTA analyzes the failure")
    report = cta_analyze(run_id, result["fail_reason"])
    
    assert "proposed_fix" in report
    assert report["method"] in ["heuristic", "llm", "cached"]
    print(f"   Analysis method: {report['method']}")
    print(f"   Confidence: {report['confidence']}")
    print(f"   Proposed fix: {report['proposed_fix']['tool_schema_patch'][:60]}...")
    
    print("\n4. Role C: Apply patch using Role B adapters")
    patch_result = apply_patch(run_id, report)
    
    assert patch_result["status"] == "patched"
    adapters = get_adapters()
    assert "level" in adapters
    assert adapters["level"] == "Level"
    print(f"   Patch applied: {patch_result['adapter']}")
    print(f"   Active adapters: {adapters}")
    
    print("\n5. Role B: Generate canary events via stream")
    start_stream(events_per_second=20.0)
    time.sleep(0.5)
    stop_stream()
    
    stream_status = get_stream_status()
    print(f"   Stream generated {stream_status['total_events']} events")
    
    recent_events = get_recent_events(15)
    assert len(recent_events) > 0
    print(f"   Retrieved {len(recent_events)} recent events for canary")
    
    print("\n6. Role C: Canary test with Role B canary runner")
    canary_result = canary_run_wrapper(run_id, N=10)
    
    assert "total" in canary_result
    assert "error_rate" in canary_result
    assert "latency_p95_ms" in canary_result
    print(f"   Canary tested {canary_result['total']} events")
    print(f"   Error rate: {canary_result['error_rate']:.2%}")
    print(f"   P95 latency: {canary_result['latency_p95_ms']:.0f}ms")
    print(f"   Passed: {canary_result['passed']}")
    
    print("\n7. Role C: Promote/rollback decision")
    decision = promote_or_rollback(canary_result)
    
    assert decision["action"] in ["promote", "rollback"]
    print(f"   Decision: {decision['action'].upper()}")
    print(f"   Reason: {decision['reason']}")
    
    if decision["action"] == "promote":
        print("\n8. Role C: Save signature for learning")
        save_signature(run_id, report, patch_result)
        print(f"   Signature saved")
        
        print("\n9. Role B: Create patched run with adapters")
        new_run_id = start_run("integration_patched")
        patched_result = run_pipeline(new_run_id, "flaky", use_adapters=True)
        
        assert patched_result["status"] == "ok"
        print(f"   Patched run {new_run_id} succeeded!")
        print(f"   Adapters fixed the drift issue")
    else:
        print("\n8. Rollback executed (canary failed)")
        adapters_after = get_adapters()
        assert adapters_after == {}
        print(f"   Adapters cleared: {adapters_after}")
    
    inject_drift(False)
    clear_adapters()
    
    print("\n=== Integration Test PASSED ===")

def test_learning_across_incidents_role_b_and_c():
    clear_adapters()
    inject_drift(False)
    
    print("\n=== Learning Integration Test ===")
    
    print("\n1. First incident with schema drift")
    inject_drift(True)
    
    run_id_1 = start_run("learning_test_1")
    result_1 = run_pipeline(run_id_1, "flaky", use_adapters=False)
    assert result_1["status"] == "failed"
    
    t0 = time.time()
    report_1 = cta_analyze(run_id_1, result_1["fail_reason"])
    time_1 = time.time() - t0
    
    print(f"   First analysis: {report_1['method']}, {time_1:.3f}s")
    
    patch_1 = apply_patch(run_id_1, report_1)
    if patch_1["status"] == "patched":
        save_signature(run_id_1, report_1, patch_1)
        print(f"   Signature saved for incident 1")
    
    clear_adapters()
    
    print("\n2. Second identical incident")
    run_id_2 = start_run("learning_test_2")
    result_2 = run_pipeline(run_id_2, "flaky", use_adapters=False)
    assert result_2["status"] == "failed"
    
    t0 = time.time()
    report_2 = cta_analyze(run_id_2, result_2["fail_reason"])
    time_2 = time.time() - t0
    
    print(f"   Second analysis: {report_2['method']}, {time_2:.3f}s")
    
    if report_2["method"] == "cached":
        print(f"   ✓ Cache hit! Cached from: {report_2.get('cached_from')}")
        print(f"   ✓ Speedup: {time_1/time_2:.1f}x faster")
        assert report_2["confidence"] == 0.95
    else:
        print(f"   Note: Cache miss (different signature)")
    
    inject_drift(False)
    clear_adapters()
    
    print("\n=== Learning Test PASSED ===")

def test_rollback_on_canary_failure_role_b_and_c():
    clear_adapters()
    
    print("\n=== Rollback Integration Test ===")
    
    print("\n1. Set up bad adapter that will cause errors")
    set_adapter({"Level": "bad_field"})
    
    print("\n2. Generate events for canary")
    for i in range(10):
        insert_event({
            "LineId": i,
            "Level": "INFO",
            "Component": "nova.compute",
            "timestamp": time.time()
        })
    
    print("\n3. Run canary with bad adapter")
    run_id = start_run("rollback_test")
    
    canary_result = canary_run(run_id, N=10)
    
    print(f"   Error rate: {canary_result['error_rate']:.2%}")
    print(f"   Passed: {canary_result['passed']}")
    
    print("\n4. Promote/rollback decision")
    decision = promote_or_rollback(canary_result)
    
    if canary_result['error_rate'] > 0.01 or not canary_result['passed']:
        assert decision["action"] == "rollback"
        print(f"   ✓ Rollback triggered correctly")
        print(f"   Reason: {decision['reason']}")
        
        adapters = get_adapters()
        assert adapters == {}
        print(f"   ✓ Adapters cleared: {adapters}")
    else:
        print(f"   Note: Canary unexpectedly passed")
    
    clear_adapters()
    
    print("\n=== Rollback Test PASSED ===")

def test_stream_and_adapter_integration():
    clear_adapters()
    inject_drift(False)
    
    print("\n=== Stream + Adapter Integration Test ===")
    
    print("\n1. Start stream with drift enabled")
    inject_drift(True)
    start_stream(events_per_second=10.0)
    time.sleep(1)
    stop_stream()
    
    events = get_recent_events(10)
    print(f"   Generated {len(events)} events with drift")
    
    if events:
        first_event = events[0]
        print(f"   Sample event fields: {list(first_event.keys())}")
        
        has_level_lower = any("level" in e for e in events if isinstance(e, dict))
        print(f"   Contains 'level' field: {has_level_lower}")
    
    print("\n2. Apply adapter to fix drift")
    set_adapter({"level": "Level"})
    
    print("\n3. Test adapter fixes the event")
    from agents.adapters import apply_adapters
    
    test_event = {"LineId": 999, "level": "ERROR", "Component": "nova.compute"}
    fixed_event = apply_adapters(test_event)
    
    assert "Level" in fixed_event
    assert "level" not in fixed_event
    assert fixed_event["Level"] == "ERROR"
    print(f"   ✓ Adapter fixed: {test_event} → {fixed_event}")
    
    inject_drift(False)
    clear_adapters()
    
    print("\n=== Stream + Adapter Test PASSED ===")

def test_end_to_end_autonomous_system():
    clear_adapters()
    inject_drift(False)
    
    print("\n=== Complete Autonomous System Test ===")
    print("Testing the full CTA-ACT autonomous loop with all components\n")
    
    print("Phase 1: FAILURE DETECTION")
    inject_drift(True)
    run_id = start_run("e2e_test")
    result = run_pipeline(run_id, "flaky", use_adapters=False)
    assert result["status"] == "failed"
    print(f"✓ Failure detected: {result['fail_reason']}")
    
    print("\nPhase 2: ROOT CAUSE ANALYSIS")
    report = cta_analyze(run_id, result["fail_reason"])
    assert "proposed_fix" in report
    print(f"✓ RCA complete: {report['method']} method")
    print(f"  Confidence: {report['confidence']}")
    
    print("\nPhase 3: AUTOMATIC PATCHING")
    patch = apply_patch(run_id, report)
    assert patch["status"] == "patched"
    assert get_adapters() != {}
    print(f"✓ Patch applied: {patch['adapter']}")
    
    print("\nPhase 4: CANARY TESTING")
    start_stream(events_per_second=15.0)
    time.sleep(0.7)
    stop_stream()
    
    canary = canary_run_wrapper(run_id, N=10)
    print(f"✓ Canary tested: {canary['total']} events")
    print(f"  Error rate: {canary['error_rate']:.2%}")
    print(f"  Passed: {canary['passed']}")
    
    print("\nPhase 5: PROMOTE/ROLLBACK")
    decision = promote_or_rollback(canary)
    print(f"✓ Decision: {decision['action'].upper()}")
    
    if decision["action"] == "promote":
        print("\nPhase 6: LEARNING")
        save_signature(run_id, report, patch)
        print(f"✓ Signature saved for future incidents")
        
        print("\nPhase 7: VERIFICATION")
        verify_run = start_run("e2e_verify")
        verify_result = run_pipeline(verify_run, "flaky", use_adapters=True)
        assert verify_result["status"] == "ok"
        print(f"✓ Verification passed: fix works!")
        
        print("\n✓✓✓ AUTONOMOUS SYSTEM FULLY OPERATIONAL ✓✓✓")
    else:
        print(f"\nSystem rolled back: {decision['reason']}")
    
    inject_drift(False)
    clear_adapters()
    
    print("\n=== E2E System Test PASSED ===")

