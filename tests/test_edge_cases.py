import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.adapters import set_adapter, apply_adapters, clear_adapters, get_adapters
from agents.tools import evaluate_event


def test_adapter_no_overwrite_existing_target_key():
    clear_adapters()
    set_adapter({"level": "Level"})
    evt = {"LineId": 1, "level": "INFO", "Level": "ERROR", "latency_ms": 100}
    fixed = apply_adapters(evt)
    assert fixed["Level"] == "ERROR"
    assert "level" in fixed  # source key remains if target exists


def test_adapter_idempotent_application():
    clear_adapters()
    set_adapter({"level": "Level"})
    evt = {"LineId": 2, "level": "WARNING", "latency_ms": 120}
    once = apply_adapters(evt)
    twice = apply_adapters(once)
    assert once == twice


def test_adapter_multiple_mappings_do_not_conflict():
    clear_adapters()
    set_adapter({"level": "Level", "comp": "Component"})
    evt = {"LineId": 3, "level": "INFO", "comp": "nova.compute"}
    fixed = apply_adapters(evt)
    assert fixed["Level"] == "INFO"
    assert fixed["Component"] == "nova.compute"


def test_evaluate_event_missing_level_raises():
    evt = {"LineId": 4, "latency_ms": 450}
    try:
        evaluate_event(evt)
        assert False, "Expected KeyError for missing 'Level'"
    except KeyError:
        pass


def test_evaluate_event_latency_thresholds():
    evt1 = {"LineId": 5, "Level": "INFO", "latency_ms": 399}
    evt2 = {"LineId": 6, "Level": "INFO", "latency_ms": 400}
    evt3 = {"LineId": 7, "Level": "INFO", "latency_ms": 401}
    assert evaluate_event(evt1)["flag"] is False
    assert evaluate_event(evt2)["flag"] is False
    assert evaluate_event(evt3)["flag"] is True


def test_evaluate_event_error_level_overrides_latency():
    evt = {"LineId": 8, "Level": "ERROR", "latency_ms": 50}
    out = evaluate_event(evt)
    assert out["flag"] is True
    assert out["reason"] == "Level=ERROR"


def test_adapter_clear_resets_state():
    clear_adapters()
    set_adapter({"level": "Level"})
    assert get_adapters() == {"level": "Level"}
    clear_adapters()
    assert get_adapters() == {}
