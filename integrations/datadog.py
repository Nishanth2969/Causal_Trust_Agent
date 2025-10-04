import os
import time
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# Make dotenv optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Datadog SDK imports with fallback
DATADOG_AVAILABLE = False
try:
    from datadog import initialize, statsd, api
    from datadog.api import APIClient
    DATADOG_AVAILABLE = True
except ImportError:
    pass

class DatadogClient:
    def __init__(self):
        self.enabled = DATADOG_AVAILABLE and self._initialize_client()
        self.api_key = os.getenv("DATADOG_API_KEY")
        self.app_key = os.getenv("DATADOG_APP_KEY")
        self.site = os.getenv("DATADOG_SITE", "datadoghq.com")
        
    def _initialize_client(self) -> bool:
        """Initialize Datadog client with environment variables"""
        if not DATADOG_AVAILABLE:
            return False
            
        api_key = os.getenv("DATADOG_API_KEY")
        app_key = os.getenv("DATADOG_APP_KEY")
        site = os.getenv("DATADOG_SITE", "datadoghq.com")
        
        if not api_key:
            print("Warning: DATADOG_API_KEY not set, Datadog integration disabled")
            return False
            
        try:
            initialize(
                api_key=api_key,
                app_key=app_key,
                api_host=f"https://api.{site}"
            )
            return True
        except Exception as e:
            print(f"Warning: Failed to initialize Datadog client: {e}")
            return False
    
    def send_error_rate_metric(self, phase: str, error_rate: float, 
                              run_id: Optional[str] = None, 
                              additional_tags: Optional[List[str]] = None) -> bool:
        """Send error rate metric to Datadog with phase tagging"""
        if not self.enabled:
            return False
            
        tags = [
            f"phase:{phase}",
            f"service:cta-agent",
            f"component:autonomous-remediation"
        ]
        
        if run_id:
            tags.append(f"run_id:{run_id}")
            
        if additional_tags:
            tags.extend(additional_tags)
            
        try:
            statsd.gauge(
                'cta.error_rate',
                error_rate,
                tags=tags
            )
            print(f"✓ Sent error_rate metric: {error_rate:.2%} (phase: {phase})")
            return True
        except Exception as e:
            print(f"✗ Failed to send error_rate metric: {e}")
            return False
    
    def send_latency_metric(self, phase: str, latency_ms: float,
                           run_id: Optional[str] = None,
                           additional_tags: Optional[List[str]] = None) -> bool:
        """Send latency metric to Datadog with phase tagging"""
        if not self.enabled:
            return False
            
        tags = [
            f"phase:{phase}",
            f"service:cta-agent",
            f"component:pipeline"
        ]
        
        if run_id:
            tags.append(f"run_id:{run_id}")
            
        if additional_tags:
            tags.extend(additional_tags)
            
        try:
            statsd.gauge(
                'cta.latency_ms',
                latency_ms,
                tags=tags
            )
            print(f"✓ Sent latency metric: {latency_ms:.0f}ms (phase: {phase})")
            return True
        except Exception as e:
            print(f"✗ Failed to send latency metric: {e}")
            return False
    
    def send_mttr_metric(self, mttr_seconds: float, 
                        run_id: Optional[str] = None,
                        method: Optional[str] = None) -> bool:
        """Send Mean Time To Recovery metric to Datadog"""
        if not self.enabled:
            return False
            
        tags = [
            f"service:cta-agent",
            f"component:autonomous-remediation"
        ]
        
        if run_id:
            tags.append(f"run_id:{run_id}")
            
        if method:
            tags.append(f"method:{method}")
            
        try:
            statsd.gauge(
                'cta.mttr_seconds',
                mttr_seconds,
                tags=tags
            )
            print(f"✓ Sent MTTR metric: {mttr_seconds:.1f}s")
            return True
        except Exception as e:
            print(f"✗ Failed to send MTTR metric: {e}")
            return False
    
    def send_incident_metric(self, incident_type: str, status: str,
                            run_id: Optional[str] = None,
                            confidence: Optional[float] = None) -> bool:
        """Send incident detection metric to Datadog"""
        if not self.enabled:
            return False
            
        tags = [
            f"incident_type:{incident_type}",
            f"status:{status}",
            f"service:cta-agent"
        ]
        
        if run_id:
            tags.append(f"run_id:{run_id}")
            
        try:
            statsd.increment(
                'cta.incidents.detected',
                tags=tags
            )
            
            if confidence is not None:
                statsd.gauge(
                    'cta.incidents.confidence',
                    confidence,
                    tags=tags
                )
                
            print(f"✓ Sent incident metric: {incident_type} ({status})")
            return True
        except Exception as e:
            print(f"✗ Failed to send incident metric: {e}")
            return False
    
    def send_canary_metric(self, passed: bool, error_rate: float,
                          latency_p95_ms: float, run_id: Optional[str] = None) -> bool:
        """Send canary test results to Datadog"""
        if not self.enabled:
            return False
            
        tags = [
            f"service:cta-agent",
            f"component:canary-testing",
            f"passed:{str(passed).lower()}"
        ]
        
        if run_id:
            tags.append(f"run_id:{run_id}")
            
        try:
            statsd.gauge(
                'cta.canary.error_rate',
                error_rate,
                tags=tags
            )
            
            statsd.gauge(
                'cta.canary.latency_p95_ms',
                latency_p95_ms,
                tags=tags
            )
            
            statsd.increment(
                'cta.canary.tests',
                tags=tags
            )
            
            print(f"✓ Sent canary metrics: passed={passed}, error_rate={error_rate:.2%}")
            return True
        except Exception as e:
            print(f"✗ Failed to send canary metrics: {e}")
            return False
    
    def create_event_span(self, event_data: Dict[str, Any], 
                          span_type: str = "log_event") -> Optional[str]:
        """Create a span for a log event with trace correlation"""
        if not self.enabled:
            return None
            
        try:
            # Extract trace correlation info
            trace_id = event_data.get("trace_id")
            span_id = event_data.get("span_id")
            
            # Create span tags
            tags = {
                "service": "cta-agent",
                "component": "log-processing",
                "span_type": span_type,
                "event_id": str(event_data.get("LineId", "unknown")),
                "level": event_data.get("Level", event_data.get("level", "unknown")),
                "component": event_data.get("Component", "unknown")
            }
            
            # Add latency if available
            if "latency_ms" in event_data:
                tags["latency_ms"] = str(event_data["latency_ms"])
                
            # Add status if available
            if "status" in event_data:
                tags["status"] = str(event_data["status"])
            
            # Create span using Datadog API
            span_data = {
                "trace_id": trace_id or int(time.time() * 1000000),  # Generate if missing
                "span_id": span_id or int(time.time() * 1000000),
                "operation_name": f"process_{span_type}",
                "start_time": int(time.time() * 1000000000),  # nanoseconds
                "duration": int(event_data.get("latency_ms", 100) * 1000000),  # nanoseconds
                "tags": tags
            }
            
            # Send span to Datadog
            api.Traces.upload([span_data])
            
            print(f"✓ Created span for event {event_data.get('LineId', 'unknown')}")
            return str(span_data["span_id"])
            
        except Exception as e:
            print(f"✗ Failed to create span: {e}")
            return None
    
    def send_before_after_comparison(self, before_metrics: Dict[str, float],
                                   after_metrics: Dict[str, float],
                                   run_id: Optional[str] = None) -> bool:
        """Send before/after comparison metrics to Datadog"""
        if not self.enabled:
            return False
            
        try:
            # Send before metrics
            if "error_rate" in before_metrics:
                self.send_error_rate_metric("before_fix", before_metrics["error_rate"], run_id)
            if "latency_ms" in before_metrics:
                self.send_latency_metric("before_fix", before_metrics["latency_ms"], run_id)
                
            # Send after metrics
            if "error_rate" in after_metrics:
                self.send_error_rate_metric("after_fix", after_metrics["error_rate"], run_id)
            if "latency_ms" in after_metrics:
                self.send_latency_metric("after_fix", after_metrics["latency_ms"], run_id)
                
            # Calculate improvement
            if "error_rate" in before_metrics and "error_rate" in after_metrics:
                improvement = before_metrics["error_rate"] - after_metrics["error_rate"]
                tags = [f"service:cta-agent", f"metric:error_rate"]
                if run_id:
                    tags.append(f"run_id:{run_id}")
                    
                statsd.gauge(
                    'cta.improvement.error_rate',
                    improvement,
                    tags=tags
                )
                
            print(f"✓ Sent before/after comparison metrics")
            return True
            
        except Exception as e:
            print(f"✗ Failed to send before/after comparison: {e}")
            return False
    
    def send_custom_metric(self, metric_name: str, value: float,
                          tags: Optional[List[str]] = None,
                          metric_type: str = "gauge") -> bool:
        """Send custom metric to Datadog"""
        if not self.enabled:
            return False
            
        default_tags = ["service:cta-agent"]
        if tags:
            default_tags.extend(tags)
            
        try:
            if metric_type == "gauge":
                statsd.gauge(metric_name, value, tags=default_tags)
            elif metric_type == "counter":
                statsd.increment(metric_name, value, tags=default_tags)
            elif metric_type == "histogram":
                statsd.histogram(metric_name, value, tags=default_tags)
            else:
                statsd.gauge(metric_name, value, tags=default_tags)
                
            print(f"✓ Sent custom metric: {metric_name}={value}")
            return True
        except Exception as e:
            print(f"✗ Failed to send custom metric: {e}")
            return False

# Global client instance
_client: Optional[DatadogClient] = None

def get_client() -> DatadogClient:
    """Get global Datadog client instance"""
    global _client
    if _client is None:
        _client = DatadogClient()
    return _client

# Convenience functions for easy integration
def send_error_rate_metric(phase: str, error_rate: float, 
                          run_id: Optional[str] = None, 
                          additional_tags: Optional[List[str]] = None) -> bool:
    """Send error rate metric to Datadog"""
    return get_client().send_error_rate_metric(phase, error_rate, run_id, additional_tags)

def send_latency_metric(phase: str, latency_ms: float,
                       run_id: Optional[str] = None,
                       additional_tags: Optional[List[str]] = None) -> bool:
    """Send latency metric to Datadog"""
    return get_client().send_latency_metric(phase, latency_ms, run_id, additional_tags)

def send_mttr_metric(mttr_seconds: float, 
                    run_id: Optional[str] = None,
                    method: Optional[str] = None) -> bool:
    """Send MTTR metric to Datadog"""
    return get_client().send_mttr_metric(mttr_seconds, run_id, method)

def send_incident_metric(incident_type: str, status: str,
                        run_id: Optional[str] = None,
                        confidence: Optional[float] = None) -> bool:
    """Send incident detection metric to Datadog"""
    return get_client().send_incident_metric(incident_type, status, run_id, confidence)

def send_canary_metric(passed: bool, error_rate: float,
                      latency_p95_ms: float, run_id: Optional[str] = None) -> bool:
    """Send canary test results to Datadog"""
    return get_client().send_canary_metric(passed, error_rate, latency_p95_ms, run_id)

def create_event_span(event_data: Dict[str, Any], 
                      span_type: str = "log_event") -> Optional[str]:
    """Create a span for a log event"""
    return get_client().create_event_span(event_data, span_type)

def send_before_after_comparison(before_metrics: Dict[str, float],
                               after_metrics: Dict[str, float],
                               run_id: Optional[str] = None) -> bool:
    """Send before/after comparison metrics"""
    return get_client().send_before_after_comparison(before_metrics, after_metrics, run_id)

def send_custom_metric(metric_name: str, value: float,
                      tags: Optional[List[str]] = None,
                      metric_type: str = "gauge") -> bool:
    """Send custom metric to Datadog"""
    return get_client().send_custom_metric(metric_name, value, tags, metric_type)

def is_enabled() -> bool:
    """Check if Datadog integration is enabled"""
    return get_client().enabled

def get_status() -> Dict[str, Any]:
    """Get Datadog client status"""
    client = get_client()
    return {
        "enabled": client.enabled,
        "datadog_available": DATADOG_AVAILABLE,
        "api_key_set": bool(client.api_key),
        "app_key_set": bool(client.app_key),
        "site": client.site
    }
