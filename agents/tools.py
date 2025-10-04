import random
import time

MERCHANTS = ["Amazon", "Walmart", "Target", "Best Buy", "Costco", "Apple", "Nike"]

def fetch_transactions(flaky=False, count=3):
    txs = []
    for i in range(count):
        tx = {
            "id": f"T{random.randint(1000, 9999)}",
            "currency": "USD",
            "amount": round(random.uniform(5.0, 50.0), 2),
            "timestamp": time.time(),
            "merchant": random.choice(MERCHANTS)
        }
        txs.append(tx)
    
    if flaky:
        for t in txs:
            t["amt"] = t.pop("amount")
    
    return txs

def flag_anomaly(tx):
    amount = tx["amount"]
    return {"flag": bool(amount and amount > 30), "reason": "amount > 30"}

