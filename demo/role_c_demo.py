#!/usr/bin/env python3

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, get_run
from agents.graph import run_pipeline
from agents.adapters import clear_adapters, get_adapters
from agents.stream import start_stream, stop_stream
from cta.analyze import cta_analyze
from cta.actions import apply_patch, canary_run_wrapper, promote_or_rollback, save_signature
from integrations.clickhouse import insert_event

def demo_autonomous_action_loop():
    print("=== Autonomous Action Loop Demo ===\n")
    
    clear_adapters()
    
    print("Step 1: Create flaky run (schema drift)")
    run_id = start_run("flaky")
    result = run_pipeline(run_id, "flaky", use_adapters=False)
    print(f"  Run ID: {run_id}")
    print(f"  Status: {result['status']}")
    print(f"  Failure: {result.get('fail_reason', 'N/A')}")
    
    if result['status'] == 'failed':
        print("\nStep 2: CTA analyzes the failure")
        t0 = time.time()
        report = cta_analyze(run_id, result['fail_reason'])
        analysis_time = time.time() - t0
        
        print(f"  Method: {report.get('method')}")
        print(f"  Confidence: {report.get('confidence'):.2f}")
        print(f"  Analysis time: {analysis_time:.3f}s")
        print(f"  Primary cause: {report.get('primary_cause_step_id')}")
        print(f"  Proposed fix: {report['proposed_fix']['tool_schema_patch'][:60]}...")
        
        print("\nStep 3: Apply patch automatically")
        patch_result = apply_patch(run_id, report)
        print(f"  Status: {patch_result['status']}")
        print(f"  Adapter: {patch_result.get('adapter', {})}")
        print(f"  Active adapters: {get_adapters()}")
        
        if patch_result['status'] == 'patched':
            print("\nStep 4: Generate canary test events")
            start_stream(events_per_second=10.0)
            time.sleep(1)
            stop_stream()
            print(f"  Generated test events")
            
            print("\nStep 5: Run canary test")
            canary_result = canary_run_wrapper(run_id, N=10)
            print(f"  Events tested: {canary_result['total']}")
            print(f"  Errors: {canary_result['errors']}")
            print(f"  Error rate: {canary_result['error_rate']:.2%}")
            print(f"  P95 latency: {canary_result['latency_p95_ms']:.0f}ms")
            print(f"  Passed: {canary_result['passed']}")
            
            print("\nStep 6: Automatic promote/rollback decision")
            decision = promote_or_rollback(canary_result)
            print(f"  Action: {decision['action'].upper()}")
            print(f"  Reason: {decision['reason']}")
            
            if decision['action'] == 'promote':
                print("\nStep 7: Save incident signature (learning)")
                save_signature(run_id, report, patch_result)
                print(f"  Signature saved for instant re-fix")
                
                print("\nStep 8: Create patched run")
                new_run_id = start_run("patched")
                patched_result = run_pipeline(new_run_id, "flaky", use_adapters=True)
                print(f"  New run ID: {new_run_id}")
                print(f"  Status: {patched_result['status']}")
                print(f"  Success! Fix promoted.")
            else:
                print("\n  Rollback executed. Adapters cleared.")
                print(f"  Active adapters: {get_adapters()}")
    
    clear_adapters()
    print("\n=== Demo Complete ===")

def demo_learning_instant_refix():
    print("\n=== Learning & Instant Re-Fix Demo ===\n")
    
    clear_adapters()
    
    print("First incident:")
    run_id_1 = start_run("incident_1")
    result_1 = run_pipeline(run_id_1, "flaky", use_adapters=False)
    
    if result_1['status'] == 'failed':
        t0 = time.time()
        report_1 = cta_analyze(run_id_1, result_1['fail_reason'])
        time_1 = time.time() - t0
        
        print(f"  Method: {report_1['method']}")
        print(f"  Analysis time: {time_1:.3f}s")
        
        patch_1 = apply_patch(run_id_1, report_1)
        if patch_1['status'] == 'patched':
            save_signature(run_id_1, report_1, patch_1)
            print(f"  Signature saved")
    
    print("\nSecond identical incident:")
    run_id_2 = start_run("incident_2")
    result_2 = run_pipeline(run_id_2, "flaky", use_adapters=False)
    
    if result_2['status'] == 'failed':
        t0 = time.time()
        report_2 = cta_analyze(run_id_2, result_2['fail_reason'])
        time_2 = time.time() - t0
        
        print(f"  Method: {report_2['method']}")
        print(f"  Analysis time: {time_2:.3f}s")
        
        if report_2['method'] == 'cached':
            print(f"  Cached from: {report_2.get('cached_from', 'N/A')}")
            speedup = time_1 / time_2 if time_2 > 0 else 0
            print(f"  Speedup: {speedup:.1f}x faster")
            print(f"  Learning works! Instant re-fix applied.")
        else:
            print(f"  Note: Cache miss (signature not similar enough)")
    
    clear_adapters()
    print("\n=== Demo Complete ===")

if __name__ == "__main__":
    print("CTA-ACT Role C Demonstration\n")
    
    demo_autonomous_action_loop()
    
    time.sleep(1)
    
    demo_learning_instant_refix()
    
    print("\n\nRole C delivers:")
    print("  ✓ Autonomous action loop (analyze → patch → canary → promote/rollback)")
    print("  ✓ Signature-based learning (instant re-fix on repeat incidents)")
    print("  ✓ Safe canary validation with automatic rollback")
    print("  ✓ Full integration with Role B adapters and streaming")

