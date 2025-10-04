import json
import re
import time
import hashlib
from typing import Dict, List, Optional
from agents.adapters import set_adapter, clear_adapters
from agents.canary import canary_run as canary_run_base
from integrations.clickhouse import insert_signature, find_similar_signature, write_cta_result
from integrations.datadog import (
    send_error_rate_metric, send_latency_metric, send_mttr_metric,
    send_incident_metric, send_canary_metric, send_before_after_comparison,
    send_custom_metric, is_enabled
)
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
        # Send incident metric for failed patch parsing
        if is_enabled():
            send_incident_metric("patch_parse_failed", "failed", run_id)
        return {
            "status": "no_patch",
            "reason": "Could not parse adapter from report",
            "run_id": run_id
        }
    
    set_adapter(adapter_mapping)
    
    # Send incident metric for successful patch application
    if is_enabled():
        send_incident_metric("patch_applied", "success", run_id, 
                           confidence=report.get("confidence", 0.0))
        send_custom_metric("cta.patches.applied", 1.0, 
                          [f"adapter:{json.dumps(adapter_mapping)}"], "counter")
    
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
    
    # Send canary metrics to Datadog
    if is_enabled():
        error_rate = result.get("error_rate", 1.0)
        latency_p95 = result.get("latency_p95_ms", float('inf'))
        passed = error_rate <= MAX_ERROR_RATE and latency_p95 <= MAX_P95_LATENCY_MS
        
        send_canary_metric(passed, error_rate, latency_p95, run_id)
        send_custom_metric("cta.canary.duration_s", result["duration_s"], 
                          [f"passed:{str(passed).lower()}"], "histogram")
    
    return result

def promote_or_rollback(canary_result: dict, thresholds: dict = None, run_id: str = None) -> dict:
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
        # Send promotion metrics to Datadog
        if is_enabled():
            send_incident_metric("fix_promoted", "success", run_id)
            send_custom_metric("cta.promotions.success", 1.0, 
                              [f"error_rate:{error_rate:.3f}", f"latency_p95:{latency_p95:.0f}"], "counter")
        
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
        
        # Send rollback metrics to Datadog
        if is_enabled():
            send_incident_metric("fix_rollback", "failed", run_id)
            send_custom_metric("cta.rollbacks.count", 1.0, 
                              [f"error_rate:{error_rate:.3f}", f"latency_p95:{latency_p95:.0f}"], "counter")
        
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
    
    # Send signature saved metric to Datadog
    if is_enabled():
        send_custom_metric("cta.signatures.saved", 1.0, 
                          [f"cause:{cause_label}", f"confidence:{report.get('confidence', 0.0):.2f}"], "counter")

def execute_cta_workflow(run_id: str, report: dict, before_metrics: Dict[str, float] = None) -> dict:
    """
    Execute the complete CTA workflow with Datadog and ClickHouse integration:
    1. Apply patch
    2. Run canary test
    3. Promote or rollback
    4. Send before/after comparison metrics (Datadog)
    5. Write results to ClickHouse
    6. Save signature for learning
    """
    workflow_start = time.time()
    
    # Step 1: Apply patch
    patch_result = apply_patch(run_id, report)
    if patch_result["status"] != "patched":
        return {
            "status": "failed",
            "reason": "Patch application failed",
            "patch_result": patch_result,
            "run_id": run_id
        }
    
    # Step 2: Run canary test
    canary_result = canary_run_wrapper(run_id, N=20)
    
    # Step 3: Promote or rollback
    decision_result = promote_or_rollback(canary_result, run_id=run_id)
    
    # Calculate before/after metrics
    before_error_rate = before_metrics.get("error_rate", 0.0) if before_metrics else 0.0
    after_error_rate = canary_result.get("error_rate", 1.0)
    
    # Step 4: Send before/after comparison metrics to Datadog
    if is_enabled() and before_metrics:
        after_metrics = {
            "error_rate": after_error_rate,
            "latency_ms": canary_result.get("latency_p95_ms", float('inf'))
        }
        send_before_after_comparison(before_metrics, after_metrics, run_id)
    
    # Step 5: Save signature if promoted
    if decision_result["action"] == "promote":
        save_signature(run_id, report, patch_result)
    
    # Calculate total MTTR
    total_mttr = time.time() - workflow_start
    
    # Step 6: Send MTTR metric to Datadog
    if is_enabled():
        method = report.get("method", "unknown")
        send_mttr_metric(total_mttr, run_id, method)
        send_custom_metric("cta.workflow.duration_s", total_mttr, 
                          [f"action:{decision_result['action']}", f"method:{method}"], "histogram")
    
    # Step 7: Write complete results to ClickHouse
    cta_result = {
        "run_id": run_id,
        "analysis_method": report.get("method", "unknown"),
        "confidence": report.get("confidence", 0.0),
        "primary_cause": report.get("primary_cause_step_id", "unknown"),
        "patch_applied": patch_result.get("adapter", {}),
        "canary_error_rate": canary_result.get("error_rate", 1.0),
        "canary_latency_p95": canary_result.get("latency_p95_ms", 0.0),
        "decision": decision_result["action"],
        "mttr_seconds": total_mttr,
        "before_error_rate": before_error_rate,
        "after_error_rate": after_error_rate
    }
    
    try:
        write_cta_result(cta_result)
    except Exception as e:
        print(f"Warning: Failed to write CTA result to ClickHouse: {e}")
        # Don't fail the workflow if ClickHouse write fails
    
    return {
        "status": "completed",
        "action": decision_result["action"],
        "patch_result": patch_result,
        "canary_result": canary_result,
        "decision_result": decision_result,
        "mttr_seconds": total_mttr,
        "run_id": run_id,
        "clickhouse_written": True  # Indicates attempt was made
    }

