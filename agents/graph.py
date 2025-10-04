from trace.sdk import trace_step, trace_error
from trace.store import save_metric, append_event
from .tools import fetch_log_events, evaluate_event
import time

def trace_tool_call(run_id, tool_name, args, fn):
    t0 = time.time()
    output = fn()
    evt = {
        "ts": time.time(),
        "run_id": run_id,
        "type": "tool",
        "tool": tool_name,
        "args": args,
        "output": output,
        "latency_ms": int((time.time() - t0) * 1000)
    }
    append_event(run_id, evt)
    return output

@trace_step("Intake")
def intake_agent(run_id, mode):
    return {"status": "ready", "mode": mode}

@trace_step("Retriever")
def retriever_agent(run_id, mode):
    flaky = (mode == "flaky")
    events = trace_tool_call(
        run_id, 
        "fetch_log_events", 
        [flaky], 
        lambda: fetch_log_events(flaky=flaky)
    )
    return {"events": events, "count": len(events)}

@trace_step("Auditor")
def auditor_agent(run_id, events, use_adapters=True):
    from .adapters import apply_adapters
    
    if use_adapters:
        events = [apply_adapters(evt) for evt in events]
    
    results = []
    error_occurred = False
    
    for evt in events:
        try:
            result = trace_tool_call(
                run_id,
                "evaluate_event",
                [evt],
                lambda: evaluate_event(evt)
            )
            results.append({
                "event_id": evt.get("LineId"),
                "flagged": result["flag"],
                "reason": result["reason"]
            })
        except Exception as e:
            error_occurred = True
            trace_error(run_id, str(e), {
                "agent": "Auditor",
                "event_id": evt.get("LineId"),
                "event": evt
            })
            results.append({
                "event_id": evt.get("LineId"),
                "error": str(e)
            })
    
    return {
        "results": results,
        "error_occurred": error_occurred
    }

def run_pipeline(run_id, mode: str, use_adapters: bool = True) -> dict:
    intake_result = intake_agent(run_id, mode)
    
    retriever_result = retriever_agent(run_id, mode)
    
    auditor_result = auditor_agent(run_id, retriever_result["events"], use_adapters=use_adapters)
    
    if auditor_result["error_occurred"]:
        status = "failed"
        fail_reason = "Schema mismatch in Auditor agent"
        save_metric(run_id, "status", status)
        save_metric(run_id, "fail_reason", fail_reason)
        
        return {
            "status": status,
            "fail_reason": fail_reason,
            "counts": {
                "events": retriever_result["count"],
                "flagged": sum(1 for r in auditor_result["results"] if r.get("flagged")),
                "errors": sum(1 for r in auditor_result["results"] if "error" in r)
            }
        }
    
    status = "ok"
    save_metric(run_id, "status", status)
    
    return {
        "status": status,
        "fail_reason": None,
        "counts": {
            "events": retriever_result["count"],
            "flagged": sum(1 for r in auditor_result["results"] if r.get("flagged")),
            "errors": 0
        }
    }

