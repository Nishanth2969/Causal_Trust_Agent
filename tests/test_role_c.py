import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cta.actions import (
    apply_patch, 
    canary_run_wrapper, 
    promote_or_rollback,
    check_signature_cache,
    save_signature,
    _parse_adapter_from_report,
    _create_simple_embedding
)
from cta.analyze import cta_analyze
from agents.adapters import get_adapters, clear_adapters, set_adapter
from agents.graph import run_pipeline
from trace.store import start_run, get_run, append_event
from integrations.clickhouse import insert_event

def test_parse_adapter_from_report():
    report1 = {
        "proposed_fix": {
            "tool_schema_patch": "map amt->amount before Auditor"
        }
    }
    adapter = _parse_adapter_from_report(report1)
    assert adapter == {"amt": "amount"}
    
    report2 = {
        "proposed_fix": {
            "tool_schema_patch": "rename 'amt' to 'amount'"
        }
    }
    adapter = _parse_adapter_from_report(report2)
    assert adapter == {"amt": "amount"}
    
    report3 = {
        "proposed_fix": {
            "tool_schema_patch": "Add schema adapter: 'amt' → 'amount'"
        }
    }
    adapter = _parse_adapter_from_report(report3)
    assert adapter == {"amt": "amount"}

def test_apply_patch_creates_adapter():
    clear_adapters()
    
    run_id = start_run("test_patch")
    
    report = {
        "proposed_fix": {
            "tool_schema_patch": "map amt->amount"
        }
    }
    
    result = apply_patch(run_id, report)
    
    assert result["status"] == "patched"
    assert result["adapter"] == {"amt": "amount"}
    
    adapters = get_adapters()
    assert adapters == {"amt": "amount"}
    
    clear_adapters()

def test_apply_patch_handles_unparseable():
    clear_adapters()
    
    run_id = start_run("test_unparseable")
    
    report = {
        "proposed_fix": {
            "tool_schema_patch": "some vague description without clear field names"
        }
    }
    
    result = apply_patch(run_id, report)
    
    assert result["status"] == "no_patch"
    
    clear_adapters()

def test_canary_run_wrapper():
    for i in range(5):
        insert_event({
            "id": f"T{i}",
            "amount": 10.0 + i,
            "currency": "USD",
            "timestamp": time.time()
        })
    
    run_id = start_run("test_canary")
    
    result = canary_run_wrapper(run_id, N=5)
    
    assert "total" in result
    assert "errors" in result
    assert "error_rate" in result
    assert "latency_p95_ms" in result
    assert "passed" in result
    assert "duration_s" in result

def test_promote_on_success():
    canary_result = {
        "total": 20,
        "errors": 0,
        "error_rate": 0.0,
        "latency_p95_ms": 100.0,
        "passed": True,
        "reason": "All checks passed"
    }
    
    decision = promote_or_rollback(canary_result)
    
    assert decision["action"] == "promote"
    assert decision["metrics"]["error_rate"] == 0.0

def test_rollback_on_high_error_rate():
    set_adapter({"amt": "amount"})
    
    canary_result = {
        "total": 20,
        "errors": 5,
        "error_rate": 0.25,
        "latency_p95_ms": 100.0,
        "passed": False,
        "reason": "Error rate too high"
    }
    
    decision = promote_or_rollback(canary_result)
    
    assert decision["action"] == "rollback"
    assert "Error rate" in decision["reason"]
    
    adapters = get_adapters()
    assert adapters == {}

def test_rollback_on_high_latency():
    set_adapter({"amt": "amount"})
    
    canary_result = {
        "total": 20,
        "errors": 0,
        "error_rate": 0.0,
        "latency_p95_ms": 1000.0,
        "passed": False,
        "reason": "Latency too high"
    }
    
    decision = promote_or_rollback(canary_result)
    
    assert decision["action"] == "rollback"
    assert "latency" in decision["reason"]
    
    adapters = get_adapters()
    assert adapters == {}

def test_create_simple_embedding():
    events = [
        {
            "type": "error",
            "context": {
                "tx": {"id": "T1", "amt": 10}
            }
        },
        {
            "type": "tool",
            "output": [{"id": "T2", "amt": 20}]
        }
    ]
    
    embedding = _create_simple_embedding(events)
    
    assert len(embedding) == 32
    assert all(0.0 <= v <= 1.0 for v in embedding)

def test_signature_cache_miss():
    events = [
        {"type": "error", "message": "test", "context": {}}
    ]
    
    cached = check_signature_cache(events)
    
    assert cached is None

def test_end_to_end_action_loop():
    clear_adapters()
    
    run_id = start_run("test_e2e")
    result = run_pipeline(run_id, "flaky", use_adapters=False)
    
    assert result["status"] == "failed"
    
    report = cta_analyze(run_id, "Schema mismatch")
    
    assert report["method"] in ["heuristic", "llm", "cached"]
    assert "proposed_fix" in report
    
    patch_result = apply_patch(run_id, report)
    
    if patch_result["status"] == "patched":
        assert get_adapters() != {}
        
        for i in range(5):
            insert_event({
                "id": f"T{i}",
                "amt": 10.0 + i,
                "currency": "USD",
                "timestamp": time.time()
            })
        
        canary_result = canary_run_wrapper(run_id, N=5)
        
        decision = promote_or_rollback(canary_result)
        
        if decision["action"] == "promote":
            save_signature(run_id, report, patch_result)
            
            new_run_id = start_run("patched")
            patched_result = run_pipeline(new_run_id, "flaky", use_adapters=True)
            
            assert patched_result["status"] == "ok"
    
    clear_adapters()

def test_cached_analysis_on_repeat():
    clear_adapters()
    
    run_id_1 = start_run("test_cache_1")
    result_1 = run_pipeline(run_id_1, "flaky", use_adapters=False)
    
    report_1 = cta_analyze(run_id_1, "Schema mismatch")
    patch_1 = apply_patch(run_id_1, report_1)
    
    if patch_1["status"] == "patched":
        save_signature(run_id_1, report_1, patch_1)
        
        run_id_2 = start_run("test_cache_2")
        result_2 = run_pipeline(run_id_2, "flaky", use_adapters=False)
        
        report_2 = cta_analyze(run_id_2, "Schema mismatch")
        
        if report_2.get("method") == "cached":
            assert report_2["confidence"] == 0.95
            assert "cached_from" in report_2
    
    clear_adapters()

