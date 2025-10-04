#!/usr/bin/env python3

import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.stream import start_stream, stop_stream, get_stream_status
from agents.failures import inject_drift, get_failure_state
from agents.adapters import set_adapter, apply_adapters, get_adapters, clear_adapters
from agents.canary import canary_run
from integrations.clickhouse import get_recent_events

def demo_stream_producer():
    print("=== Stream Producer Demo ===")
    print("Starting stream at 5 events/sec...")
    start_stream(events_per_second=5.0)
    
    time.sleep(2)
    status = get_stream_status()
    print(f"Status: {status}")
    print(f"Generated {status['total_events']} events in 2 seconds")
    
    print("\nStopping stream...")
    stop_stream()
    time.sleep(0.5)
    print("Stream stopped")
    print()

def demo_failure_injection():
    print("=== Failure Injection Demo ===")
    print("Initial state:", get_failure_state())
    
    print("\nInjecting schema drift...")
    inject_drift(True)
    print("State after drift:", get_failure_state())
    
    print("\nDisabling drift...")
    inject_drift(False)
    print("State after disable:", get_failure_state())
    print()

def demo_adapters():
    print("=== Adapter Mechanism Demo ===")
    clear_adapters()
    
    tx_broken = {"id": "T1", "amt": 12.0, "currency": "USD"}
    print(f"Broken transaction: {tx_broken}")
    
    print("\nSetting adapter: amt -> amount")
    set_adapter({"amt": "amount"})
    print(f"Active adapters: {get_adapters()}")
    
    tx_fixed = apply_adapters(tx_broken)
    print(f"Fixed transaction: {tx_fixed}")
    
    clear_adapters()
    print("\nAdapters cleared")
    print()

def demo_canary():
    print("=== Canary Runner Demo ===")
    
    print("Starting stream to generate test events...")
    start_stream(events_per_second=10.0)
    time.sleep(2)
    stop_stream()
    
    events = get_recent_events(20)
    print(f"Found {len(events)} recent events")
    
    if events:
        print("\nRunning canary test...")
        from trace.store import start_run
        run_id = start_run("canary_demo")
        
        result = canary_run(run_id, N=min(10, len(events)))
        
        print(f"Total events tested: {result['total']}")
        print(f"Errors: {result['errors']}")
        print(f"Error rate: {result['error_rate']:.2%}")
        print(f"P95 latency: {result['latency_p95_ms']:.0f}ms")
        print(f"Passed: {result['passed']}")
        print(f"Reason: {result['reason']}")
    else:
        print("No events available for canary test")
    print()

def demo_full_flow():
    print("=== Full Flow Demo: Drift -> Adapter -> Canary ===")
    
    clear_adapters()
    inject_drift(False)
    
    print("Step 1: Start stream WITHOUT drift")
    start_stream(events_per_second=10.0)
    time.sleep(1)
    stop_stream()
    print(f"Generated {get_stream_status()['total_events']} good events")
    
    print("\nStep 2: Inject drift and generate bad events")
    inject_drift(True)
    start_stream(events_per_second=10.0)
    time.sleep(1)
    stop_stream()
    print("Generated events with schema drift (amt instead of amount)")
    
    print("\nStep 3: Apply adapter to fix schema")
    set_adapter({"amt": "amount"})
    print(f"Adapter set: {get_adapters()}")
    
    print("\nStep 4: Run canary with adapter")
    from trace.store import start_run
    run_id = start_run("full_flow_demo")
    result = canary_run(run_id, N=10)
    
    print(f"Canary result: {result['passed']}")
    print(f"Error rate: {result['error_rate']:.2%}")
    
    if result['passed']:
        print("\nSuccess! Adapter fixed the drift issue.")
    
    clear_adapters()
    inject_drift(False)
    print()

if __name__ == "__main__":
    print("CTA-ACT Role B Demonstration\n")
    
    demo_stream_producer()
    demo_failure_injection()
    demo_adapters()
    demo_canary()
    demo_full_flow()
    
    print("Demo complete!")

