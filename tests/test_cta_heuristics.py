import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, append_event
from cta.analyze import cta_analyze, _heuristic_analyze

def test_heuristic_detects_schema_drift():
    events = [
        {
            "ts": 1234567890.0,
            "run_id": "test_run",
            "idx": 0,
            "type": "step",
            "agent": "Intake",
            "step_id": "step_0",
            "input": {},
            "output": {"status": "ready"}
        },
        {
            "ts": 1234567891.0,
            "run_id": "test_run",
            "idx": 1,
            "type": "tool",
            "tool": "fetch_transactions",
            "args": {"flaky": True},
            "output": [
                {"id": "T1", "amt": 12.0},
                {"id": "T2", "amt": 5.5}
            ]
        },
        {
            "ts": 1234567892.0,
            "run_id": "test_run",
            "idx": 2,
            "type": "error",
            "message": "KeyError: 'amount'",
            "context": {"agent": "Auditor"}
        }
    ]
    
    report = _heuristic_analyze(events, "Schema mismatch")
    
    assert "amt" in str(report["symptoms"]).lower() or "schema" in str(report["symptoms"]).lower()
    assert report["confidence"] > 0.5
    assert len(report["why_chain"]) == 5
    assert "tool_1" in report["primary_cause_step_id"]

def test_heuristic_identifies_error_events():
    events = [
        {
            "ts": 1234567890.0,
            "run_id": "test_run",
            "idx": 0,
            "type": "error",
            "message": "KeyError: 'amount'",
            "context": {"agent": "Auditor", "tx_id": "T1"}
        }
    ]
    
    report = _heuristic_analyze(events, "KeyError")
    
    assert len(report["evidence"]) > 0
    assert "keyerror" in report["symptoms"][0].lower()

def test_cta_analyze_end_to_end():
    run_id = start_run("test_cta")
    
    append_event(run_id, {
        "ts": 1234567890.0,
        "run_id": run_id,
        "type": "tool",
        "tool": "fetch_transactions",
        "args": {"flaky": True},
        "output": [{"id": "T1", "amt": 12.0}]
    })
    
    append_event(run_id, {
        "ts": 1234567891.0,
        "run_id": run_id,
        "type": "error",
        "message": "KeyError: 'amount'",
        "context": {"agent": "Auditor"}
    })
    
    report = cta_analyze(run_id, "Schema mismatch")
    
    assert report["run_id"] == run_id
    assert "primary_cause_step_id" in report
    assert "confidence" in report
    assert "proposed_fix" in report
    assert report["confidence"] > 0

