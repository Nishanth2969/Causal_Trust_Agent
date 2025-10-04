import time
import statistics
from typing import Dict, List
from integrations.clickhouse import get_recent_events
from trace.store import start_run

MAX_ERROR_RATE = 0.01
MAX_P95_LATENCY_MS = 500

def run_pipeline_on_event(event: dict, use_adapters: bool = True) -> Dict:
    from .graph import intake_agent, retriever_agent, auditor_agent
    from .adapters import apply_adapters
    from trace.sdk import trace_error
    
    run_id = f"canary_{int(time.time() * 1000)}"
    
    try:
        t0 = time.time()
        
        intake_result = intake_agent(run_id, "canary")
        
        txs = [event]
        
        if use_adapters:
            txs = [apply_adapters(tx) for tx in txs]
        
        auditor_result = auditor_agent(run_id, txs)
        
        latency_ms = int((time.time() - t0) * 1000)
        
        return {
            "success": not auditor_result.get("error_occurred", False),
            "latency_ms": latency_ms,
            "error": None
        }
    
    except Exception as e:
        latency_ms = int((time.time() - t0) * 1000)
        trace_error(run_id, str(e), {"event": event})
        return {
            "success": False,
            "latency_ms": latency_ms,
            "error": str(e)
        }

def canary_run(run_id: str, N: int = 20) -> Dict:
    events = get_recent_events(N)
    
    if not events:
        return {
            "total": 0,
            "errors": 0,
            "error_rate": 0.0,
            "latency_p95_ms": 0.0,
            "passed": False,
            "reason": "No events to test"
        }
    
    results = []
    errors = 0
    latencies = []
    
    for event in events:
        result = run_pipeline_on_event(event, use_adapters=True)
        results.append(result)
        
        if not result["success"]:
            errors += 1
        
        latencies.append(result["latency_ms"])
    
    total = len(results)
    error_rate = errors / total if total > 0 else 0.0
    
    latencies.sort()
    p95_index = int(0.95 * len(latencies))
    latency_p95_ms = latencies[p95_index] if latencies else 0.0
    
    passed = error_rate <= MAX_ERROR_RATE and latency_p95_ms <= MAX_P95_LATENCY_MS
    
    reason = "All checks passed"
    if error_rate > MAX_ERROR_RATE:
        reason = f"Error rate {error_rate:.2%} exceeds threshold {MAX_ERROR_RATE:.2%}"
    elif latency_p95_ms > MAX_P95_LATENCY_MS:
        reason = f"P95 latency {latency_p95_ms}ms exceeds threshold {MAX_P95_LATENCY_MS}ms"
    
    return {
        "total": total,
        "errors": errors,
        "error_rate": error_rate,
        "latency_p95_ms": latency_p95_ms,
        "passed": passed,
        "reason": reason
    }

def get_recent_events_for_canary(N: int = 20) -> List[Dict]:
    return get_recent_events(N)

