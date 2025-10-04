import random

def fetch_transactions(flaky=False):
    txs = [
        {"id": "T1", "currency": "USD", "amount": 12.0},
        {"id": "T2", "currency": "USD", "amount": 5.5},
        {"id": "T3", "currency": "USD", "amount": 33.2},
    ]
    if flaky:
        for t in txs:
            t["amt"] = t.pop("amount")
    return txs

def flag_anomaly(tx):
    amount = tx["amount"]
    return {"flag": bool(amount and amount > 30), "reason": "amount > 30"}

