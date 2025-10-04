#!/usr/bin/env python3
"""
Test script for Datadog integration
This script tests all the Datadog metrics and spans functionality
"""

import os
import time
import json
from integrations.datadog import (
    get_client, get_status, send_error_rate_metric, send_latency_metric,
    send_mttr_metric, send_incident_metric, send_canary_metric,
    send_before_after_comparison, send_custom_metric, create_event_span,
    is_enabled
)

def test_datadog_status():
    """Test Datadog client status and configuration"""
    print("=" * 80)
    print("DATADOG INTEGRATION STATUS TEST")
    print("=" * 80)
    
    status = get_status()
    print(f"Datadog Available: {status['datadog_available']}")
    print(f"Integration Enabled: {status['enabled']}")
    print(f"API Key Set: {status['api_key_set']}")
    print(f"App Key Set: {status['app_key_set']}")
    print(f"Site: {status['site']}")
    
    if not status['enabled']:
        print("\n⚠️  Datadog integration is disabled.")
        print("To enable, set DATADOG_API_KEY environment variable:")
        print("export DATADOG_API_KEY='your_api_key_here'")
        print("export DATADOG_APP_KEY='your_app_key_here'  # Optional")
        print("export DATADOG_SITE='datadoghq.com'  # Optional")
        return False
    
    print("\n✅ Datadog integration is enabled and ready!")
    return True

def test_metrics():
    """Test sending various metrics to Datadog"""
    print("\n" + "=" * 80)
    print("METRICS SENDING TEST")
    print("=" * 80)
    
    run_id = f"test_run_{int(time.time())}"
    
    # Test error rate metrics
    print("\n1. Testing Error Rate Metrics:")
    send_error_rate_metric("before_fix", 1.0, run_id, ["test:true"])
    send_error_rate_metric("after_fix", 0.0, run_id, ["test:true"])
    
    # Test latency metrics
    print("\n2. Testing Latency Metrics:")
    send_latency_metric("before_fix", 500.0, run_id, ["test:true"])
    send_latency_metric("after_fix", 200.0, run_id, ["test:true"])
    
    # Test MTTR metric
    print("\n3. Testing MTTR Metric:")
    send_mttr_metric(3.2, run_id, "heuristic")
    
    # Test incident metrics
    print("\n4. Testing Incident Metrics:")
    send_incident_metric("schema_drift", "detected", run_id, 0.92)
    send_incident_metric("schema_drift", "fixed", run_id, 0.95)
    
    # Test canary metrics
    print("\n5. Testing Canary Metrics:")
    send_canary_metric(True, 0.0, 250.0, run_id)
    send_canary_metric(False, 0.5, 600.0, run_id)
    
    # Test custom metrics
    print("\n6. Testing Custom Metrics:")
    send_custom_metric("cta.test.custom_gauge", 42.0, ["test:true"], "gauge")
    send_custom_metric("cta.test.custom_counter", 1.0, ["test:true"], "counter")
    send_custom_metric("cta.test.custom_histogram", 150.0, ["test:true"], "histogram")
    
    print(f"\n✅ All metrics sent for run_id: {run_id}")

def test_before_after_comparison():
    """Test before/after comparison metrics"""
    print("\n" + "=" * 80)
    print("BEFORE/AFTER COMPARISON TEST")
    print("=" * 80)
    
    run_id = f"comparison_test_{int(time.time())}"
    
    before_metrics = {
        "error_rate": 1.0,  # 100% error rate
        "latency_ms": 500.0  # 500ms latency
    }
    
    after_metrics = {
        "error_rate": 0.0,  # 0% error rate
        "latency_ms": 200.0  # 200ms latency
    }
    
    print(f"Before: Error Rate {before_metrics['error_rate']:.0%}, Latency {before_metrics['latency_ms']:.0f}ms")
    print(f"After:  Error Rate {after_metrics['error_rate']:.0%}, Latency {after_metrics['latency_ms']:.0f}ms")
    
    success = send_before_after_comparison(before_metrics, after_metrics, run_id)
    
    if success:
        print("✅ Before/after comparison metrics sent successfully")
    else:
        print("❌ Failed to send before/after comparison metrics")

def test_span_creation():
    """Test span creation for log events"""
    print("\n" + "=" * 80)
    print("SPAN CREATION TEST")
    print("=" * 80)
    
    # Create sample log events
    sample_events = [
        {
            "LineId": 1001,
            "Level": "INFO",
            "Component": "nova.compute.manager",
            "latency_ms": 250,
            "status": 200,
            "trace_id": int(time.time() * 1000000),
            "span_id": int(time.time() * 1000000) + 1
        },
        {
            "LineId": 1002,
            "level": "ERROR",  # Schema drift: lowercase 'level'
            "Component": "nova.api",
            "latency_ms": 500,
            "status": 500,
            "trace_id": int(time.time() * 1000000),
            "span_id": int(time.time() * 1000000) + 2
        }
    ]
    
    print("Creating spans for sample events:")
    for i, event in enumerate(sample_events, 1):
        span_id = create_event_span(event, f"log_event_{i}")
        if span_id:
            print(f"  Event {event['LineId']}: Span created with ID {span_id}")
        else:
            print(f"  Event {event['LineId']}: Failed to create span")
    
    print("✅ Span creation test completed")

def test_cta_workflow_simulation():
    """Simulate a complete CTA workflow with Datadog metrics"""
    print("\n" + "=" * 80)
    print("CTA WORKFLOW SIMULATION")
    print("=" * 80)
    
    run_id = f"cta_simulation_{int(time.time())}"
    
    print(f"Simulating CTA workflow for run_id: {run_id}")
    
    # Step 1: Incident Detection
    print("\n1. Incident Detection:")
    send_incident_metric("schema_drift", "detected", run_id, 0.92)
    send_custom_metric("cta.analysis.started", 1.0, [f"run_id:{run_id}"], "counter")
    
    # Step 2: Analysis
    print("2. Root Cause Analysis:")
    time.sleep(0.1)  # Simulate analysis time
    send_incident_metric("analysis_completed", "success", run_id, 0.92)
    send_custom_metric("cta.analysis.completed", 1.0, 
                      ["method:heuristic", "cause:schema_drift", "confidence:0.92"], "counter")
    
    # Step 3: Patch Application
    print("3. Patch Application:")
    send_incident_metric("patch_applied", "success", run_id, 0.92)
    send_custom_metric("cta.patches.applied", 1.0, 
                      ['adapter:{"level": "Level"}'], "counter")
    
    # Step 4: Canary Testing
    print("4. Canary Testing:")
    send_canary_metric(True, 0.0, 250.0, run_id)
    send_custom_metric("cta.canary.duration_s", 2.1, ["passed:true"], "histogram")
    
    # Step 5: Promotion Decision
    print("5. Promotion Decision:")
    send_incident_metric("fix_promoted", "success", run_id)
    send_custom_metric("cta.promotions.success", 1.0, 
                      ["error_rate:0.000", "latency_p95:250"], "counter")
    
    # Step 6: Before/After Comparison
    print("6. Before/After Comparison:")
    before_metrics = {"error_rate": 1.0, "latency_ms": 500.0}
    after_metrics = {"error_rate": 0.0, "latency_ms": 250.0}
    send_before_after_comparison(before_metrics, after_metrics, run_id)
    
    # Step 7: Learning
    print("7. Signature Learning:")
    send_custom_metric("cta.signatures.saved", 1.0, 
                      ["cause:schema_drift", "confidence:0.92"], "counter")
    
    # Step 8: MTTR
    print("8. MTTR Calculation:")
    send_mttr_metric(3.2, run_id, "heuristic")
    send_custom_metric("cta.workflow.duration_s", 3.2, 
                      ["action:promote", "method:heuristic"], "histogram")
    
    print(f"\n✅ Complete CTA workflow simulation completed for run_id: {run_id}")

def main():
    """Run all Datadog integration tests"""
    print("🚀 Starting Datadog Integration Tests")
    print("=" * 80)
    
    # Test 1: Check status
    if not test_datadog_status():
        print("\n⚠️  Skipping other tests due to disabled integration")
        return
    
    # Test 2: Basic metrics
    test_metrics()
    
    # Test 3: Before/after comparison
    test_before_after_comparison()
    
    # Test 4: Span creation
    test_span_creation()
    
    # Test 5: Complete CTA workflow simulation
    test_cta_workflow_simulation()
    
    print("\n" + "=" * 80)
    print("🎉 ALL DATADOG INTEGRATION TESTS COMPLETED")
    print("=" * 80)
    print("\nNext steps:")
    print("1. Check your Datadog dashboard for the test metrics")
    print("2. Look for metrics with 'cta.' prefix and 'test:true' tags")
    print("3. Verify before/after comparison graphs are working")
    print("4. Check trace correlation in APM section")

if __name__ == "__main__":
    main()
