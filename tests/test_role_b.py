import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.adapters import set_adapter, apply_adapters, clear_adapters, get_adapters
from agents.failures import inject_drift, get_failure_state
from agents.tools import fetch_log_events, evaluate_event
from agents.stream import StreamProducer, get_stream_status
from integrations.clickhouse import insert_event, get_recent_events

def test_adapter_mechanism():
    clear_adapters()
    
    evt_broken = {"LineId": 1, "level": "INFO", "Component": "nova.compute"}
    evt_normal = {"LineId": 2, "Level": "INFO", "Component": "nova.compute"}
    
    assert apply_adapters(evt_broken) == evt_broken
    assert apply_adapters(evt_normal) == evt_normal
    
    set_adapter({"level": "Level"})
    
    evt_fixed = apply_adapters(evt_broken)
    assert "Level" in evt_fixed
    assert "level" not in evt_fixed
    assert evt_fixed["Level"] == "INFO"
    
    adapters = get_adapters()
    assert adapters == {"level": "Level"}
    
    clear_adapters()

def test_failure_injection():
    inject_drift(False)
    state = get_failure_state()
    assert state["schema_drift"] == False
    
    inject_drift(True)
    state = get_failure_state()
    assert state["schema_drift"] == True
    
    inject_drift(False)

def test_enhanced_tools():
    events = fetch_log_events(flaky=False, count=5)
    assert len(events) == 5
    for evt in events:
        assert "Level" in evt
        assert "LineId" in evt
        assert "Component" in evt
        assert "Content" in evt
    
    events_flaky = fetch_log_events(flaky=True, count=3)
    assert len(events_flaky) == 3
    for evt in events_flaky:
        assert "level" in evt
        assert "Level" not in evt

def test_stream_producer():
    producer = StreamProducer(events_per_second=10.0)
    
    status = producer.get_status()
    assert status["running"] == False
    assert status["total_events"] == 0
    
    producer.start()
    time.sleep(0.5)
    
    status = producer.get_status()
    assert status["running"] == True
    assert status["total_events"] > 0
    
    producer.stop()
    time.sleep(0.1)
    
    status = producer.get_status()
    assert status["running"] == False

def test_clickhouse_mock():
    event = {
        "LineId": 123,
        "Level": "INFO",
        "Component": "nova.compute.manager",
        "timestamp": time.time()
    }
    
    insert_event(event)
    
    recent = get_recent_events(limit=10)
    assert len(recent) > 0
    
    found = any(e.get("LineId") == 123 for e in recent)
    assert found

def test_adapter_with_pipeline_integration():
    clear_adapters()
    set_adapter({"level": "Level"})
    
    flaky_events = fetch_log_events(flaky=True, count=3)
    assert all("level" in e for e in flaky_events)
    assert all("Level" not in e for e in flaky_events)
    
    fixed_events = [apply_adapters(e) for e in flaky_events]
    
    for fixed in fixed_events:
        assert "Level" in fixed
        assert "level" not in fixed
        result = evaluate_event(fixed)
        assert result is not None
        assert "flag" in result
    
    print(f"   Pipeline integration: {len(fixed_events)} flaky events fixed and evaluated successfully")
    
    clear_adapters()

