import threading
import time
import random
from typing import Optional
from .tools import MERCHANTS
from .failures import get_failure_state
from integrations.clickhouse import insert_event

class StreamProducer:
    def __init__(self, events_per_second: float = 2.0):
        self.events_per_second = events_per_second
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.total_events = 0
        self.lock = threading.Lock()
    
    def _generate_transaction(self) -> dict:
        failure_state = get_failure_state()
        
        tx = {
            "id": f"T{random.randint(1000, 9999)}",
            "currency": "USD",
            "amount": round(random.uniform(5.0, 50.0), 2),
            "timestamp": time.time(),
            "merchant": random.choice(MERCHANTS)
        }
        
        if failure_state["schema_drift"]:
            tx["amt"] = tx.pop("amount")
        
        if failure_state["currency_mix"] and random.random() < 0.3:
            tx["currency"] = random.choice(["EUR", "GBP"])
        
        return tx
    
    def _emit_to_clickhouse(self, tx: dict):
        try:
            insert_event(tx)
        except Exception:
            pass
    
    def _run_loop(self):
        interval = 1.0 / self.events_per_second
        
        while self.running:
            tx = self._generate_transaction()
            self._emit_to_clickhouse(tx)
            
            with self.lock:
                self.total_events += 1
            
            time.sleep(interval)
    
    def start(self):
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._run_loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
            self.thread = None
    
    def get_status(self) -> dict:
        with self.lock:
            return {
                "running": self.running,
                "total_events": self.total_events,
                "events_per_second": self.events_per_second,
                "failure_modes": get_failure_state()
            }

_producer: Optional[StreamProducer] = None

def get_producer() -> StreamProducer:
    global _producer
    if _producer is None:
        _producer = StreamProducer()
    return _producer

def start_stream(events_per_second: float = 2.0):
    producer = get_producer()
    producer.events_per_second = events_per_second
    producer.start()

def stop_stream():
    producer = get_producer()
    producer.stop()

def get_stream_status() -> dict:
    producer = get_producer()
    return producer.get_status()

