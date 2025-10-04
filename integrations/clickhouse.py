import json
import os
from datetime import datetime
from typing import List, Dict, Any
import requests
from requests.auth import HTTPBasicAuth

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
        self.use_cloud = False
        self.cloud_host = None
        self.cloud_auth = None
        
        # Check for ClickHouse Cloud credentials
        cloud_key = os.getenv("CLICKHOUSE_CLOUD_KEY")
        cloud_secret = os.getenv("CLICKHOUSE_CLOUD_SECRET")
        cloud_host = os.getenv("CLICKHOUSE_CLOUD_HOST")
        cloud_service_id = os.getenv("CLICKHOUSE_SERVICE_ID")
        cloud_port = int(os.getenv("CLICKHOUSE_CLOUD_PORT", "9440"))
        
        # Check if using ClickHouse Cloud Query API (REST endpoint)
        if cloud_key and cloud_secret and cloud_service_id:
            # Use ClickHouse Cloud Query API
            self.use_cloud = True
            self.use_mock = False
            self.cloud_host = f"https://queries.clickhouse.cloud/service/{cloud_service_id}/run"
            self.cloud_auth = HTTPBasicAuth(cloud_key, cloud_secret)
            print("[OK] Connected to ClickHouse Cloud (Query API)")
        elif cloud_key and cloud_secret and cloud_host:
            # Use ClickHouse Cloud with native protocol
            try:
                self.client = Client(
                    host=cloud_host,
                    port=cloud_port,
                    user=cloud_key,
                    password=cloud_secret,
                    secure=True,
                    verify=True
                )
                # Test connection
                self.client.execute("SELECT 1")
                self.use_cloud = True
                self.use_mock = False
                print("[OK] Connected to ClickHouse Cloud")
            except Exception as e:
                print(f"Failed to connect to ClickHouse Cloud: {e}")
                print("Will try HTTP interface...")
                # Fallback to HTTP interface
                self.use_cloud = True
                self.use_mock = False
                self.cloud_host = f"https://{cloud_host}:8443" if not cloud_host.startswith("http") else cloud_host
                self.cloud_auth = HTTPBasicAuth(cloud_key, cloud_secret)
        elif not self.use_mock:
            # Use local ClickHouse
            host = os.getenv("CLICKHOUSE_HOST", "localhost")
            port = int(os.getenv("CLICKHOUSE_PORT", "9000"))
            try:
                self.client = Client(host=host, port=port)
                self._init_tables()
            except Exception as e:
                print(f"Could not connect to local ClickHouse: {e}")
                self.use_mock = True
    
    def _execute_cloud_query(self, query: str, format: str = "JSONEachRow"):
        """Execute query on ClickHouse Cloud via HTTP API"""
        if not self.use_cloud or not self.cloud_host:
            return None
        
        try:
            # ClickHouse Cloud Query API format
            url = f"{self.cloud_host}?format={format}"
            payload = {"sql": query}
            headers = {"Content-Type": "application/json"}
            
            response = requests.post(
                url,
                auth=self.cloud_auth,
                headers=headers,
                json=payload
            )
            response.raise_for_status()
            
            # INSERT/CREATE queries return empty response on success
            if not response.text.strip():
                return []
            
            if format == "JSONEachRow":
                lines = response.text.strip().split('\n')
                return [json.loads(line) for line in lines if line]
            return response.text
        except Exception as e:
            # Don't print errors for INSERT queries (they return empty)
            if "INSERT" not in query and "CREATE" not in query:
                print(f"ClickHouse Cloud query error: {e}")
            return None
    
    def _init_tables(self):
        if self.use_mock or self.use_cloud:
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
    
    def insert_audit_result(self, audit_result: Dict[str, Any]):
        """Insert audit result into ClickHouse"""
        if self.use_cloud and self.cloud_host and not self.client:
            # Use HTTP Query API to insert into audit_results table
            try:
                # Prepare audit result data
                timestamp = audit_result.get("timestamp", datetime.now().isoformat())
                event_id = audit_result.get("event_id", "")
                line_id = audit_result.get("line_id", 0)
                component = audit_result.get("component", "")
                level = audit_result.get("level", "")
                is_anomaly = 1 if audit_result.get("is_anomaly", False) else 0
                reason = audit_result.get("reason", "")
                latency_ms = audit_result.get("latency_ms", 0)
                status = audit_result.get("status", 200)
                
                # Create INSERT query
                query = f"""
                INSERT INTO audit_results 
                (timestamp, event_id, line_id, component, level, is_anomaly, reason, latency_ms, status)
                VALUES 
                ('{timestamp}', '{event_id}', {line_id}, '{component}', '{level}', {is_anomaly}, '{reason}', {latency_ms}, {status})
                """
                
                result = self._execute_cloud_query(query)
                # INSERT queries return empty response on success
                # Only print debug for successful saves (no exception thrown)
                    
            except Exception as e:
                print(f"[WARN] Could not save audit result: {e}")
        
        elif self.client:
            # Use native client
            try:
                timestamp = audit_result.get("timestamp", datetime.now())
                self.client.execute(
                    """INSERT INTO audit_results 
                    (timestamp, event_id, line_id, component, level, is_anomaly, reason, latency_ms, status) 
                    VALUES""",
                    [(
                        timestamp,
                        audit_result.get("event_id", ""),
                        audit_result.get("line_id", 0),
                        audit_result.get("component", ""),
                        audit_result.get("level", ""),
                        1 if audit_result.get("is_anomaly", False) else 0,
                        audit_result.get("reason", ""),
                        audit_result.get("latency_ms", 0),
                        audit_result.get("status", 200)
                    )]
                )
            except Exception as e:
                print(f"[WARN] Could not save audit result to native client: {e}")
    
    def get_audit_results(self, limit: int = 100, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fetch audit results from ClickHouse"""
        if self.use_cloud and self.cloud_host and not self.client:
            query = "SELECT * FROM audit_results"
            
            if filters:
                conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        conditions.append(f"{key} = '{value}'")
                    else:
                        conditions.append(f"{key} = {value}")
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            result = self._execute_cloud_query(query)
            return result if result else []
        
        elif self.client:
            try:
                query = f"SELECT * FROM audit_results LIMIT {limit}"
                result = self.client.execute(query, with_column_types=True)
                rows, columns_with_types = result[0], result[1]
                column_names = [col[0] for col in columns_with_types]
                return [dict(zip(column_names, row)) for row in rows]
            except Exception as e:
                print(f"[WARN] Could not fetch audit results: {e}")
                return []
        
        return []
    
    def get_recent_events(self, limit: int = 20, table_name: str = None) -> List[Dict[str, Any]]:
        global MOCK_EVENTS_STORE
        
        if self.use_mock:
            recent = MOCK_EVENTS_STORE[-limit:]
            return [json.loads(e["payload"]) for e in recent]
        
        # Prioritize HTTP API if cloud_host is set (Query API)
        if self.use_cloud and self.cloud_host and not self.client:
            # Use HTTP Query API
            if not table_name:
                tables_query = "SHOW TABLES"
                result = self._execute_cloud_query(tables_query, format="TabSeparated")
                if result:
                    print(f"Available tables: {result}")
                return []
            
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = self._execute_cloud_query(query)
            return result if result else []
        
        elif self.use_cloud and self.client:
            # Use native client for cloud
            if not table_name:
                try:
                    tables = self.client.execute("SHOW TABLES")
                    print(f"Available tables: {[t[0] for t in tables]}")
                except Exception as e:
                    print(f"Could not list tables: {e}")
                return []
            
            try:
                query = f"SELECT * FROM {table_name} LIMIT {limit}"
                result = self.client.execute(query, with_column_types=True)
                
                # Convert to list of dicts
                rows, columns_with_types = result[0], result[1]
                column_names = [col[0] for col in columns_with_types]
                
                return [dict(zip(column_names, row)) for row in rows]
            except Exception as e:
                print(f"Error fetching from cloud: {e}")
                return []
        elif self.use_cloud and self.cloud_host:
            # Fallback to HTTP interface
            if not table_name:
                tables_query = "SHOW TABLES"
                result = self._execute_cloud_query(tables_query, format="TabSeparated")
                if result:
                    print(f"Available tables: {result}")
                return []
            
            query = f"SELECT * FROM {table_name} LIMIT {limit}"
            result = self._execute_cloud_query(query)
            return result if result else []
        
        try:
            result = self.client.execute(
                f"SELECT payload FROM events ORDER BY ts DESC LIMIT {limit}"
            )
            return [json.loads(row[0]) for row in result]
        except Exception:
            return []
    
    def fetch_logs_from_cloud(self, table_name: str, limit: int = 100, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Fetch logs from ClickHouse Cloud with optional filters"""
        if not self.use_cloud:
            print("Not connected to ClickHouse Cloud")
            return []
        
        query = f"SELECT * FROM {table_name}"
        
        if filters:
            conditions = []
            for key, value in filters.items():
                if isinstance(value, str):
                    conditions.append(f"{key} = '{value}'")
                else:
                    conditions.append(f"{key} = {value}")
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
        
        # Try to order by timestamp if it exists, otherwise just limit
        query += f" LIMIT {limit}"
        
        # Prioritize HTTP Query API
        if self.cloud_host and not self.client:
            result = self._execute_cloud_query(query)
            return result if result else []
        elif self.client:
            # Use native client
            try:
                result = self.client.execute(query, with_column_types=True)
                rows, columns_with_types = result[0], result[1]
                column_names = [col[0] for col in columns_with_types]
                return [dict(zip(column_names, row)) for row in rows]
            except Exception as e:
                print(f"Error fetching logs: {e}")
                return []
        else:
            # Use HTTP interface
            result = self._execute_cloud_query(query)
            return result if result else []
    
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

def insert_audit_result(audit_result: Dict[str, Any]):
    """Insert audit result into ClickHouse"""
    get_client().insert_audit_result(audit_result)

def get_audit_results(limit: int = 100, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Fetch audit results from ClickHouse"""
    return get_client().get_audit_results(limit, filters)

def get_recent_events(limit: int = 20, table_name: str = None) -> List[Dict[str, Any]]:
    return get_client().get_recent_events(limit, table_name)

def fetch_logs_from_cloud(table_name: str, limit: int = 100, filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    return get_client().fetch_logs_from_cloud(table_name, limit, filters)

def insert_signature(signature: Dict[str, Any]):
    get_client().insert_signature(signature)

def find_similar_signature(embedding: List[float], threshold: float = 0.85) -> Dict[str, Any]:
    return get_client().find_similar_signature(embedding, threshold)

