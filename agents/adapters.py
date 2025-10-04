import json
import os
from typing import Dict, Any

ADAPTER_CONFIG_PATH = os.path.join("data", "adapter_config.json")

ADAPTERS: Dict[str, str] = {}

def load_adapters():
    global ADAPTERS
    if os.path.exists(ADAPTER_CONFIG_PATH):
        with open(ADAPTER_CONFIG_PATH, 'r') as f:
            ADAPTERS = json.load(f)
    return ADAPTERS

def save_adapters():
    os.makedirs(os.path.dirname(ADAPTER_CONFIG_PATH), exist_ok=True)
    with open(ADAPTER_CONFIG_PATH, 'w') as f:
        json.dump(ADAPTERS, f, indent=2)

def set_adapter(mapping: Dict[str, str]):
    global ADAPTERS
    ADAPTERS.update(mapping)
    save_adapters()

def clear_adapters():
    global ADAPTERS
    ADAPTERS = {}
    if os.path.exists(ADAPTER_CONFIG_PATH):
        os.remove(ADAPTER_CONFIG_PATH)

def apply_adapters(tx: Dict[str, Any]) -> Dict[str, Any]:
    if not ADAPTERS:
        return tx
    
    adapted_tx = tx.copy()
    for old_key, new_key in ADAPTERS.items():
        if old_key in adapted_tx and new_key not in adapted_tx:
            adapted_tx[new_key] = adapted_tx.pop(old_key)
    
    return adapted_tx

def get_adapters() -> Dict[str, str]:
    return ADAPTERS.copy()

load_adapters()

