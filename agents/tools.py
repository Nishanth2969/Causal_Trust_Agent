import random
import time

COMPONENTS = ["nova.compute.manager", "nova.osapi_compute.wsgi.server", "nova.virt.libvirt.imagecache", 
              "nova.scheduler.manager", "nova.network.manager"]
LEVELS = ["INFO", "WARNING", "ERROR"]
ENDPOINTS = ["/v2/servers/detail", "/v2/servers", "/v2/images", "/v2/flavors", "/v2/os-hypervisors"]

def fetch_log_events(flaky=False, count=3):
    events = []
    for i in range(count):
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
            "status": status
        }
        events.append(evt)
    
    if flaky:
        for evt in events:
            evt["level"] = evt.pop("Level")
    
    return events

def evaluate_event(evt):
    level = evt["Level"]
    latency_ms = evt.get("latency_ms", 0)
    is_anomaly = level == "ERROR" or latency_ms > 400
    reason = f"Level={level}" if level == "ERROR" else f"latency={latency_ms}ms"
    return {"flag": is_anomaly, "reason": reason}

