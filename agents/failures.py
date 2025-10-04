import random

SCHEMA_DRIFT = False
TOOL_AMBIGUITY = False
CURRENCY_MIX = False

FAILURE_SEED = 42

def inject_drift(enabled: bool):
    global SCHEMA_DRIFT
    SCHEMA_DRIFT = enabled

def inject_tool_ambiguity(enabled: bool):
    global TOOL_AMBIGUITY
    TOOL_AMBIGUITY = enabled

def inject_currency_mix(enabled: bool):
    global CURRENCY_MIX
    CURRENCY_MIX = enabled

def get_failure_state() -> dict:
    return {
        "schema_drift": SCHEMA_DRIFT,
        "tool_ambiguity": TOOL_AMBIGUITY,
        "currency_mix": CURRENCY_MIX
    }

random.seed(FAILURE_SEED)

