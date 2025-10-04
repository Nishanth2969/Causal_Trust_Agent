import json
import re
import time
import hashlib
from typing import Dict, List, Optional
from agents.adapters import set_adapter, clear_adapters
from agents.canary import canary_run as canary_run_base
from integrations.clickhouse import insert_signature, find_similar_signature
from trace.store import save_metric, get_run

MAX_ERROR_RATE = 0.01
MAX_P95_LATENCY_MS = 500

def _parse_adapter_from_report(report: dict) -> Dict[str, str]:
    tool_schema_patch = report.get("proposed_fix", {}).get("tool_schema_patch", "")
    
    patterns = [
        r"['\"]?(\w+)['\"]?\s*[-→>]+\s*['\"]?(\w+)['\"]?",
        r"rename\s+['\"]?(\w+)['\"]?\s+to\s+['\"]?(\w+)['\"]?",
        r"map\s+['\"]?(\w+)['\"]?\s*[-→>]+\s*['\"]?(\w+)['\"]?",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, tool_schema_patch, re.IGNORECASE)
        if match:
            old_field, new_field = match.groups()
            return {old_field: new_field}
    
    return {}

def apply_patch(run_id: str, report: dict) -> dict:
    adapter_mapping = _parse_adapter_from_report(report)
    
    if not adapter_mapping:
        return {
            "status": "no_patch",
            "reason": "Could not parse adapter from report",
            "run_id": run_id
        }
    
    set_adapter(adapter_mapping)
    
    return {
        "status": "patched",
        "adapter": adapter_mapping,
        "description": f"Applied schema adapter: {' -> '.join(f'{k} -> {v}' for k, v in adapter_mapping.items())}",
        "run_id": run_id
    }

def canary_run_wrapper(run_id: str, N: int = 20) -> dict:
    t0 = time.time()
    
    result = canary_run_base(run_id, N)
    
    result["duration_s"] = time.time() - t0
    
    return result

def promote_or_rollback(canary_result: dict, thresholds: dict = None) -> dict:
    if thresholds is None:
        thresholds = {
            "max_error_rate": MAX_ERROR_RATE,
            "max_p95_latency_ms": MAX_P95_LATENCY_MS
        }
    
    error_rate = canary_result.get("error_rate", 1.0)
    latency_p95 = canary_result.get("latency_p95_ms", float('inf'))
    
    max_error_rate = thresholds.get("max_error_rate", MAX_ERROR_RATE)
    max_p95_latency = thresholds.get("max_p95_latency_ms", MAX_P95_LATENCY_MS)
    
    if error_rate <= max_error_rate and latency_p95 <= max_p95_latency:
        return {
            "action": "promote",
            "reason": canary_result.get("reason", "All checks passed"),
            "metrics": {
                "error_rate": error_rate,
                "latency_p95_ms": latency_p95
            }
        }
    else:
        clear_adapters()
        
        reasons = []
        if error_rate > max_error_rate:
            reasons.append(f"Error rate {error_rate:.2%} exceeds {max_error_rate:.2%}")
        if latency_p95 > max_p95_latency:
            reasons.append(f"P95 latency {latency_p95:.0f}ms exceeds {max_p95_latency}ms")
        
        return {
            "action": "rollback",
            "reason": "; ".join(reasons),
            "metrics": {
                "error_rate": error_rate,
                "latency_p95_ms": latency_p95
            }
        }

def _create_simple_embedding(events: List[dict]) -> List[float]:
    field_names = set()
    event_types = []
    
    for event in events:
        event_types.append(event.get("type", ""))
        
        if event.get("type") == "error":
            context = event.get("context", {})
            if isinstance(context, dict):
                tx = context.get("tx", {})
                if isinstance(tx, dict):
                    field_names.update(tx.keys())
        
        if event.get("type") == "tool":
            output = event.get("output", [])
            if isinstance(output, list) and len(output) > 0:
                if isinstance(output[0], dict):
                    field_names.update(output[0].keys())
    
    signature_string = ",".join(sorted(field_names)) + "|" + ",".join(event_types[:10])
    
    hash_bytes = hashlib.sha256(signature_string.encode()).digest()
    
    embedding = []
    for i in range(32):
        byte_val = hash_bytes[i % len(hash_bytes)]
        embedding.append(float(byte_val) / 255.0)
    
    return embedding

def check_signature_cache(events: List[dict]) -> Optional[dict]:
    embedding = _create_simple_embedding(events)
    
    cached = find_similar_signature(embedding, threshold=0.85)
    
    return cached

def save_signature(run_id: str, report: dict, patch: dict):
    from trace.store import load_events
    
    events = load_events(run_id)
    embedding = _create_simple_embedding(events)
    
    cause_label = report.get("primary_cause_step_id", "unknown")
    patch_text = json.dumps(patch.get("adapter", {}))
    
    signature = {
        "id": f"sig_{run_id}",
        "cause_label": cause_label,
        "embedding": embedding,
        "patch_text": patch_text
    }
    
    insert_signature(signature)

