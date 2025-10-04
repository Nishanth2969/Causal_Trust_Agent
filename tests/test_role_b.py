import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.adapters import set_adapter, apply_adapters, clear_adapters, get_adapters
from agents.failures import inject_drift, get_failure_state
from agents.tools import fetch_transactions
from agents.stream import StreamProducer, get_stream_status
from integrations.clickhouse import insert_event, get_recent_events

def test_adapter_mechanism():
    clear_adapters()
    
    tx_broken = {"id": "T1", "amt": 12.0, "currency": "USD"}
    tx_normal = {"id": "T2", "amount": 15.0, "currency": "USD"}
    
    assert apply_adapters(tx_broken) == tx_broken
    assert apply_adapters(tx_normal) == tx_normal
    
    set_adapter({"amt": "amount"})
    
    tx_fixed = apply_adapters(tx_broken)
    assert "amount" in tx_fixed
    assert "amt" not in tx_fixed
    assert tx_fixed["amount"] == 12.0
    
    adapters = get_adapters()
    assert adapters == {"amt": "amount"}
    
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
    txs = fetch_transactions(flaky=False, count=5)
    assert len(txs) == 5
    for tx in txs:
        assert "amount" in tx
        assert "id" in tx
        assert "currency" in tx
        assert "merchant" in tx
    
    txs_flaky = fetch_transactions(flaky=True, count=3)
    assert len(txs_flaky) == 3
    for tx in txs_flaky:
        assert "amt" in tx
        assert "amount" not in tx

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
        "id": "T123",
        "amount": 25.0,
        "currency": "USD",
        "timestamp": time.time()
    }
    
    insert_event(event)
    
    recent = get_recent_events(limit=10)
    assert len(recent) > 0
    
    found = any(e.get("id") == "T123" for e in recent)
    assert found

def test_adapter_with_pipeline_integration():
    from agents.graph import run_pipeline
    from trace.store import start_run, get_run
    
    clear_adapters()
    set_adapter({"amt": "amount"})
    
    run_id = start_run("test_adapter")
    result = run_pipeline(run_id, "flaky", use_adapters=True)
    
    assert result["status"] == "ok"
    
    clear_adapters()

