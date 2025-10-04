from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, list_runs, get_run, load_events
from agents.graph import run_pipeline
from agents.stream import start_stream, stop_stream, get_stream_status
from agents.failures import inject_drift, inject_tool_ambiguity, inject_currency_mix, get_failure_state
from agents.adapters import get_adapters, clear_adapters
from cta.analyze import cta_analyze
from cta.actions import apply_patch, canary_run_wrapper, promote_or_rollback, save_signature

app = Flask(__name__)

@app.route('/')
def index():
    runs = list_runs()
    return render_template('index.html', runs=runs)

@app.route('/run', methods=['POST'])
def create_run():
    mode = request.args.get('mode', 'good')
    
    run_id = start_run(mode)
    
    result = run_pipeline(run_id, mode)
    
    return redirect(url_for('view_run', run_id=run_id))

@app.route('/run/<run_id>')
def view_run(run_id):
    run = get_run(run_id)
    if not run:
        return "Run not found", 404
    
    events = load_events(run_id)
    
    step_events = [e for e in events if e["type"] == "step"]
    total_latency = sum(e.get("latency_ms", 0) for e in events)
    
    return render_template('run_view.html', run=run, events=events, 
                         step_count=len(step_events), total_latency=total_latency)

@app.route('/run/<run_id>/cta', methods=['POST'])
def analyze_run(run_id):
    run = get_run(run_id)
    if not run:
        return "Run not found", 404
    
    failure_text = run.get('fail_reason', 'Unknown failure')
    
    report = cta_analyze(run_id, failure_text)
    
    return render_template('cta_panel.html', report=report, run_id=run_id)

@app.route('/run/<run_id>/cta.json')
def get_cta_json(run_id):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    
    failure_text = run.get('fail_reason', 'Unknown failure')
    report = cta_analyze(run_id, failure_text)
    
    return jsonify(report)

@app.route('/run/<run_id>/apply_fix', methods=['POST'])
def apply_fix(run_id):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    
    failure_text = run.get('fail_reason', 'Unknown failure')
    
    report = cta_analyze(run_id, failure_text)
    
    patch_result = apply_patch(run_id, report)
    
    if patch_result.get("status") == "no_patch":
        return jsonify({
            "status": "error",
            "reason": "Could not generate patch from report"
        }), 400
    
    canary_result = canary_run_wrapper(run_id, N=20)
    
    decision = promote_or_rollback(canary_result)
    
    if decision["action"] == "promote":
        save_signature(run_id, report, patch_result)
        
        new_run_id = start_run("patched")
        result = run_pipeline(new_run_id, "patched", use_adapters=True)
        
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "status": "promoted",
                "canary": canary_result,
                "decision": decision,
                "new_run_id": new_run_id,
                "patch": patch_result
            })
        else:
            return redirect(url_for('view_run', run_id=new_run_id))
    else:
        if request.headers.get('Accept') == 'application/json':
            return jsonify({
                "status": "rolled_back",
                "reason": decision["reason"],
                "canary": canary_result,
                "decision": decision
            }), 400
        else:
            return redirect(url_for('view_run', run_id=run_id))

@app.route('/stream/start', methods=['POST'])
def start_stream_endpoint():
    events_per_second = request.json.get('events_per_second', 2.0) if request.is_json else 2.0
    start_stream(events_per_second)
    return jsonify({"status": "started", "events_per_second": events_per_second})

@app.route('/stream/stop', methods=['POST'])
def stop_stream_endpoint():
    stop_stream()
    return jsonify({"status": "stopped"})

@app.route('/stream/status')
def stream_status():
    return jsonify(get_stream_status())

@app.route('/inject_drift', methods=['POST'])
def toggle_drift():
    enabled = request.json.get('enabled', True) if request.is_json else True
    inject_drift(enabled)
    return jsonify({"drift_enabled": enabled, "failure_modes": get_failure_state()})

@app.route('/inject_tool_ambiguity', methods=['POST'])
def toggle_tool_ambiguity():
    enabled = request.json.get('enabled', True) if request.is_json else True
    inject_tool_ambiguity(enabled)
    return jsonify({"tool_ambiguity_enabled": enabled, "failure_modes": get_failure_state()})

@app.route('/inject_currency_mix', methods=['POST'])
def toggle_currency_mix():
    enabled = request.json.get('enabled', True) if request.is_json else True
    inject_currency_mix(enabled)
    return jsonify({"currency_mix_enabled": enabled, "failure_modes": get_failure_state()})

@app.route('/failure_modes')
def failure_modes():
    return jsonify(get_failure_state())

@app.route('/adapters')
def adapters():
    return jsonify(get_adapters())

@app.route('/adapters/clear', methods=['POST'])
def clear_adapters_endpoint():
    clear_adapters()
    return jsonify({"status": "cleared"})

@app.route('/run/<run_id>/canary', methods=['POST'])
def run_canary(run_id):
    run = get_run(run_id)
    if not run:
        return jsonify({"error": "Run not found"}), 404
    
    N = request.json.get('N', 20) if request.is_json else 20
    
    result = canary_run_wrapper(run_id, N)
    
    return jsonify(result)

if __name__ == '__main__':
    app.run(debug=True)

