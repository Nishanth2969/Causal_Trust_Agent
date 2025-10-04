import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run
from agents.graph import run_pipeline
from cta.analyze import cta_analyze, cta_patch

def main():
    print("Seeding demo runs...")
    
    print("\n1. Creating GOOD run...")
    good_run_id = start_run("good")
    good_result = run_pipeline(good_run_id, "good")
    print(f"   Run ID: {good_run_id}")
    print(f"   Status: {good_result['status']}")
    
    print("\n2. Creating FLAKY run...")
    flaky_run_id = start_run("flaky")
    flaky_result = run_pipeline(flaky_run_id, "flaky")
    print(f"   Run ID: {flaky_run_id}")
    print(f"   Status: {flaky_result['status']}")
    print(f"   Failure: {flaky_result.get('fail_reason', 'N/A')}")
    
    print("\n3. Running CTA analysis on flaky run...")
    failure_text = flaky_result.get('fail_reason', 'Unknown failure')
    report = cta_analyze(flaky_run_id, failure_text)
    print(f"   Primary cause: {report.get('primary_cause_step_id')}")
    print(f"   Confidence: {report.get('confidence')}")
    print(f"   Method: {report.get('method')}")
    
    print("\n4. Applying fix and creating PATCHED run...")
    patch_result = cta_patch(flaky_run_id, report)
    print(f"   Patch: {patch_result['description']}")
    
    patched_run_id = start_run("patched")
    patched_result = run_pipeline(patched_run_id, "patched")
    print(f"   Run ID: {patched_run_id}")
    print(f"   Status: {patched_result['status']}")
    
    print("\nSeed complete. Run 'make run' to start the web UI.")
    print(f"\nDemo runs created:")
    print(f"  - Good: {good_run_id}")
    print(f"  - Flaky: {flaky_run_id}")
    print(f"  - Patched: {patched_run_id}")

if __name__ == '__main__':
    main()

