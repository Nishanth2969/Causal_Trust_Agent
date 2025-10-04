import json
import os
from datetime import datetime
from typing import List, Dict, Any

CLICKHOUSE_AVAILABLE = False
try:
    from clickhouse_driver import Client
    CLICKHOUSE_AVAILABLE = True
except ImportError:
    pass

MOCK_EVENTS_STORE = []

class ClickHouseClient:
    def __init__(self):
        self.use_mock = not CLICKHOUSE_AVAILABLE
        self.client = None
        
        if not self.use_mock:
            host = os.getenv("CLICKHOUSE_HOST", "localhost")
            port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
            try:
                self.client = Client(host=host, port=port)
                self._init_tables()
            except Exception:
                self.use_mock = True
    
    def _init_tables(self):
        if self.use_mock:
            return
        
        try:
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    ts DateTime,
                    id String,
                    payload String
                ) ENGINE = MergeTree()
                ORDER BY ts
            """)
            
            self.client.execute("""
                CREATE TABLE IF NOT EXISTS signatures (
                    id String,
                    cause_label String,
                    embedding Array(Float32),
                    patch_text String
                ) ENGINE = MergeTree()
                ORDER BY id
            """)
        except Exception:
            self.use_mock = True
    
    def insert_event(self, event: Dict[str, Any]):
        global MOCK_EVENTS_STORE
        
        if self.use_mock:
            MOCK_EVENTS_STORE.append({
                "ts": datetime.fromtimestamp(event.get("timestamp", event.get("ts", datetime.now().timestamp()))),
                "id": event.get("id", ""),
                "payload": json.dumps(event)
            })
            if len(MOCK_EVENTS_STORE) > 1000:
                MOCK_EVENTS_STORE = MOCK_EVENTS_STORE[-1000:]
        else:
            try:
                ts = datetime.fromtimestamp(event.get("timestamp", event.get("ts", datetime.now().timestamp())))
                self.client.execute(
                    "INSERT INTO events (ts, id, payload) VALUES",
                    [(ts, event.get("id", ""), json.dumps(event))]
                )
            except Exception:
                pass
    
    def get_recent_events(self, limit: int = 20) -> List[Dict[str, Any]]:
        global MOCK_EVENTS_STORE
        
        if self.use_mock:
            recent = MOCK_EVENTS_STORE[-limit:]
            return [json.loads(e["payload"]) for e in recent]
        
        try:
            result = self.client.execute(
                f"SELECT payload FROM events ORDER BY ts DESC LIMIT {limit}"
            )
            return [json.loads(row[0]) for row in result]
        except Exception:
            return []
    
    def insert_signature(self, signature: Dict[str, Any]):
        if self.use_mock:
            return
        
        try:
            self.client.execute(
                "INSERT INTO signatures (id, cause_label, embedding, patch_text) VALUES",
                [(
                    signature["id"],
                    signature["cause_label"],
                    signature["embedding"],
                    signature["patch_text"]
                )]
            )
        except Exception:
            pass
    
    def find_similar_signature(self, embedding: List[float], threshold: float = 0.85) -> Dict[str, Any]:
        if self.use_mock:
            return None
        
        try:
            result = self.client.execute("""
                SELECT id, cause_label, patch_text,
                       cosineDistance(embedding, %(emb)s) as distance
                FROM signatures
                WHERE distance < %(threshold)s
                ORDER BY distance
                LIMIT 1
            """, {"emb": embedding, "threshold": 1 - threshold})
            
            if result:
                return {
                    "id": result[0][0],
                    "cause_label": result[0][1],
                    "patch_text": result[0][2],
                    "similarity": 1 - result[0][3]
                }
        except Exception:
            pass
        
        return None

_client = None

def get_client() -> ClickHouseClient:
    global _client
    if _client is None:
        _client = ClickHouseClient()
    return _client

def insert_event(event: Dict[str, Any]):
    get_client().insert_event(event)

def get_recent_events(limit: int = 20) -> List[Dict[str, Any]]:
    return get_client().get_recent_events(limit)

def insert_signature(signature: Dict[str, Any]):
    get_client().insert_signature(signature)

def find_similar_signature(embedding: List[float], threshold: float = 0.85) -> Dict[str, Any]:
    return get_client().find_similar_signature(embedding, threshold)

