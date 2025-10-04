import time
import uuid
from .store import append_event

def trace_step(agent_name):
    def deco(fn):
        def wrapper(run_id, *a, **kw):
            t0 = time.time()
            out = fn(run_id, *a, **kw)
            evt = {
                "ts": time.time(),
                "run_id": run_id,
                "type": "step",
                "agent": agent_name,
                "step_id": str(uuid.uuid4()),
                "input": kw if kw else a,
                "output": out,
                "latency_ms": int((time.time() - t0) * 1000)
            }
            append_event(run_id, evt)
            return out
        return wrapper
    return deco

def trace_tool(tool_name):
    def deco(fn):
        def wrapper(*a, **kw):
            if len(a) > 0:
                run_id = a[0]
                tool_args = a[1:]
            else:
                raise ValueError("trace_tool wrapper requires run_id as first argument")
            
            t0 = time.time()
            out = fn(*tool_args, **kw)
            evt = {
                "ts": time.time(),
                "run_id": run_id,
                "type": "tool",
                "tool": tool_name,
                "args": kw if kw else list(tool_args),
                "output": out,
                "latency_ms": int((time.time() - t0) * 1000)
            }
            append_event(run_id, evt)
            return out
        return wrapper
    return deco

def trace_error(run_id, message, context):
    evt = {
        "ts": time.time(),
        "run_id": run_id,
        "type": "error",
        "message": message,
        "context": context
    }
    append_event(run_id, evt)

