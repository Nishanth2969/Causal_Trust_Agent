import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from trace.store import start_run, append_event, load_events
from trace.constants import EVENT_TYPES
from agents.graph import run_pipeline

def test_event_has_required_fields():
    run_id = start_run("test")
    
    result = run_pipeline(run_id, "good")
    
    events = load_events(run_id)
    
    assert len(events) > 0, "Pipeline should generate events"
    
    for event in events:
        assert "ts" in event, "Event must have timestamp"
        assert "run_id" in event, "Event must have run_id"
        assert "idx" in event, "Event must have idx"
        assert "type" in event, "Event must have type"
        assert event["type"] in EVENT_TYPES, f"Invalid event type: {event['type']}"
        assert event["run_id"] == run_id, "Event run_id must match"

def test_step_event_fields():
    run_id = start_run("test")
    
    run_pipeline(run_id, "good")
    
    events = load_events(run_id)
    step_events = [e for e in events if e["type"] == "step"]
    
    assert len(step_events) > 0, "Should have step events"
    
    for event in step_events:
        assert "agent" in event, "Step must have agent"
        assert "step_id" in event, "Step must have step_id"
        assert "input" in event, "Step must have input"
        assert "output" in event, "Step must have output"

def test_tool_event_fields():
    run_id = start_run("test")
    
    run_pipeline(run_id, "good")
    
    events = load_events(run_id)
    tool_events = [e for e in events if e["type"] == "tool"]
    
    assert len(tool_events) > 0, "Should have tool events"
    
    for event in tool_events:
        assert "tool" in event, "Tool event must have tool name"
        assert "args" in event, "Tool event must have args"
        assert "output" in event, "Tool event must have output"

def test_error_event_on_flaky_run():
    run_id = start_run("test_flaky")
    
    result = run_pipeline(run_id, "flaky")
    
    events = load_events(run_id)
    error_events = [e for e in events if e["type"] == "error"]
    
    assert len(error_events) > 0, "Flaky run should generate error events"
    
    for event in error_events:
        assert "message" in event, "Error must have message"
        assert "context" in event, "Error must have context"

