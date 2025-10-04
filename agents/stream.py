import threading
import time
import random
from typing import Optional
from .tools import COMPONENTS, LEVELS, ENDPOINTS
from .failures import get_failure_state
from integrations.clickhouse import insert_event

class StreamProducer:
    def __init__(self, events_per_second: float = 2.0):
        self.events_per_second = events_per_second
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.total_events = 0
        self.lock = threading.Lock()
    
    def _generate_log_event(self) -> dict:
        failure_state = get_failure_state()
        
        latency_ms = random.randint(100, 500)
        level = random.choice(LEVELS)
        component = random.choice(COMPONENTS)
        endpoint = random.choice(ENDPOINTS)
        status = 200 if level != "ERROR" else random.choice([500, 503, 404])
        
        evt = {
            "LineId": random.randint(1000, 9999),
            "Date": "2017-05-16",
            "Time": f"00:00:{random.randint(10,59):02d}.{random.randint(0,999):03d}",
            "Pid": random.randint(2000, 30000),
            "Level": level,
            "Component": component,
            "Content": f'"GET {endpoint} HTTP/1.1" status: {status} len: {random.randint(500,3000)} time: 0.{latency_ms}',
            "latency_ms": latency_ms,
            "status": status,
            "timestamp": time.time()
        }
        
        if failure_state["schema_drift"]:
            evt["level"] = evt.pop("Level")
        
        if failure_state["currency_mix"] and random.random() < 0.3:
            evt["status"] = random.choice([500, 503, 504])
        
        return evt
    
    def _emit_to_clickhouse(self, evt: dict):
        try:
            insert_event(evt)
        except Exception:
            pass
    
    def _run_loop(self):
        interval = 1.0 / self.events_per_second
        
        while self.running:
            evt = self._generate_log_event()
            self._emit_to_clickhouse(evt)
            
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

