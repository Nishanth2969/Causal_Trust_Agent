from flask import Flask, render_template, request, redirect, url_for, jsonify
import json
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, list_runs, get_run, load_events
from agents.graph import run_pipeline
from cta.analyze import cta_analyze, cta_patch

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
        return "Run not found", 404
    
    failure_text = run.get('fail_reason', 'Unknown failure')
    report = cta_analyze(run_id, failure_text)
    
    patch_result = cta_patch(run_id, report)
    
    new_run_id = start_run("patched")
    result = run_pipeline(new_run_id, "patched")
    
    return redirect(url_for('view_run', run_id=new_run_id))

if __name__ == '__main__':
    app.run(debug=True)

