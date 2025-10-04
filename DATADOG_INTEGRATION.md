# Datadog Integration for CTA Autonomous Remediation

This document describes the Datadog integration for the Causal Trust Agent (CTA) autonomous remediation system.

## Overview

The Datadog integration provides comprehensive observability for the CTA system, including:

- **Metrics**: Error rates, latency, MTTR, incident detection
- **Spans**: Trace correlation for log events
- **Dashboards**: Before/after comparison visualizations
- **Alerts**: Automated notifications for incidents

## Setup

### 1. Install Dependencies

```bash
pip install datadog
```

### 2. Configure Environment Variables

```bash
# Required
export DATADOG_API_KEY="your_datadog_api_key"

# Optional
export DATADOG_APP_KEY="your_datadog_app_key"  # For enhanced features
export DATADOG_SITE="datadoghq.com"  # or "datadoghq.eu" for EU
```

### 3. Import and Use

```python
from integrations.datadog import (
    send_error_rate_metric, send_latency_metric, send_mttr_metric,
    send_incident_metric, send_canary_metric, send_before_after_comparison,
    create_event_span, is_enabled
)

# Check if integration is enabled
if is_enabled():
    send_error_rate_metric("before_fix", 1.0, run_id)
```

## Metrics

### Core Metrics

| Metric Name | Type | Description | Tags |
|-------------|------|-------------|------|
| `cta.error_rate` | Gauge | Error rate percentage | `phase`, `service`, `run_id` |
| `cta.latency_ms` | Gauge | Latency in milliseconds | `phase`, `service`, `run_id` |
| `cta.mttr_seconds` | Gauge | Mean Time To Recovery | `service`, `method`, `run_id` |
| `cta.incidents.detected` | Counter | Incident detection events | `incident_type`, `status`, `run_id` |

### Workflow Metrics

| Metric Name | Type | Description | Tags |
|-------------|------|-------------|------|
| `cta.analysis.started` | Counter | Analysis workflow started | `run_id` |
| `cta.analysis.completed` | Counter | Analysis workflow completed | `method`, `cause`, `confidence` |
| `cta.patches.applied` | Counter | Patches applied successfully | `adapter` |
| `cta.canary.tests` | Counter | Canary test executions | `passed`, `run_id` |
| `cta.promotions.success` | Counter | Successful fix promotions | `error_rate`, `latency_p95` |
| `cta.rollbacks.count` | Counter | Fix rollbacks | `error_rate`, `latency_p95` |
| `cta.signatures.saved` | Counter | Learning signatures saved | `cause`, `confidence` |

### Phase Tracking

The system uses phase tags to track before/after states:

- `phase:before_fix` - Metrics before applying the fix
- `phase:after_fix` - Metrics after applying the fix

## Spans

### Event Spans

Each log event can be traced as a span:

```python
event_data = {
    "LineId": 1001,
    "Level": "INFO",
    "Component": "nova.compute.manager",
    "latency_ms": 250,
    "status": 200,
    "trace_id": 1234567890,
    "span_id": 1234567891
}

span_id = create_event_span(event_data, "log_event")
```

### Span Tags

Spans include the following tags:
- `service:cta-agent`
- `component:log-processing`
- `span_type:log_event`
- `event_id`: LineId from the event
- `level`: Log level (Level or level field)
- `component`: Component name
- `latency_ms`: Event latency
- `status`: HTTP status code

## Dashboard

### Import Dashboard

1. Go to Datadog Dashboard
2. Click "Import Dashboard"
3. Upload `dashboards/cta_dashboard.json`

### Dashboard Widgets

1. **Error Rate: Before vs After Fix**
   - Shows error rate improvement over time
   - Red line: before_fix phase
   - Green line: after_fix phase

2. **Latency: Before vs After Fix**
   - Shows latency improvement over time
   - Red line: before_fix phase
   - Green line: after_fix phase

3. **Mean Time To Recovery (MTTR)**
   - Shows MTTR by analysis method
   - Tracks autonomous recovery speed

4. **Incident Detection Rate**
   - Shows incidents detected by status
   - Tracks detection effectiveness

5. **Canary Test Results**
   - Shows canary test pass/fail rates
   - Green: passed tests
   - Red: failed tests

6. **Fix Promotion Success Rate**
   - Percentage of successful promotions
   - Key success metric

7. **Analysis Method Distribution**
   - Pie chart of analysis methods used
   - heuristic, llm, cached

8. **Cached Fix Hit Rate**
   - Percentage of cached fixes used
   - Learning effectiveness metric

9. **Workflow Duration Distribution**
   - Histogram of workflow durations
   - Performance tracking

10. **Improvement Metrics**
    - Shows error rate improvement over time
    - Quantifies fix effectiveness

11. **Recent Incidents Timeline**
    - Event timeline of incidents
    - Chronological incident tracking

## Testing

### Run Integration Tests

```bash
python test_datadog_integration.py
```

This will test:
- Datadog client status
- Metric sending
- Before/after comparison
- Span creation
- Complete CTA workflow simulation

### Test Output

The test script will:
1. Check if Datadog integration is enabled
2. Send test metrics with `test:true` tags
3. Verify all metric types work
4. Simulate a complete CTA workflow
5. Provide instructions for dashboard verification

## Integration Points

### CTA Analysis (`cta/analyze.py`)

```python
# Incident detection
send_incident_metric("incident_detected", "analyzing", run_id)

# Analysis completion
send_incident_metric("analysis_completed", "success", run_id, confidence)

# Cached fix found
send_incident_metric("cached_fix_found", "success", run_id, confidence=0.95)
```

### CTA Actions (`cta/actions.py`)

```python
# Patch application
send_incident_metric("patch_applied", "success", run_id, confidence)

# Canary testing
send_canary_metric(passed, error_rate, latency_p95, run_id)

# Promotion/rollback
send_incident_metric("fix_promoted", "success", run_id)
send_incident_metric("fix_rollback", "failed", run_id)

# Before/after comparison
send_before_after_comparison(before_metrics, after_metrics, run_id)

# MTTR tracking
send_mttr_metric(total_mttr, run_id, method)
```

### Complete Workflow

Use the `execute_cta_workflow()` function for complete integration:

```python
from cta.actions import execute_cta_workflow

# Execute complete workflow with Datadog integration
result = execute_cta_workflow(run_id, report, before_metrics)
```

## Alerts

### Recommended Alerts

1. **High Error Rate**
   ```
   avg(last_5m):avg:cta.error_rate{phase:before_fix} > 0.1
   ```

2. **Slow MTTR**
   ```
   avg(last_10m):avg:cta.mttr_seconds > 30
   ```

3. **Canary Test Failures**
   ```
   sum(last_5m):sum:cta.canary.tests{passed:false} > 0
   ```

4. **Low Promotion Success Rate**
   ```
   avg(last_1h):sum:cta.promotions.success / (sum:cta.promotions.success + sum:cta.rollbacks.count) < 0.8
   ```

## Troubleshooting

### Common Issues

1. **Integration Disabled**
   - Check `DATADOG_API_KEY` environment variable
   - Verify API key is valid
   - Check network connectivity

2. **Metrics Not Appearing**
   - Verify metric names match dashboard queries
   - Check tag formatting
   - Ensure metrics are being sent (check logs)

3. **Spans Not Correlating**
   - Verify trace_id and span_id are set
   - Check span timing (start_time, duration)
   - Ensure proper span hierarchy

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Status Check

```python
from integrations.datadog import get_status
print(get_status())
```

## Best Practices

1. **Consistent Tagging**
   - Use consistent tag names across metrics
   - Include run_id for traceability
   - Use phase tags for before/after tracking

2. **Metric Granularity**
   - Send metrics at appropriate intervals
   - Don't overwhelm with too many metrics
   - Focus on key performance indicators

3. **Error Handling**
   - Always check `is_enabled()` before sending metrics
   - Handle exceptions gracefully
   - Log failures for debugging

4. **Dashboard Maintenance**
   - Regularly review dashboard queries
   - Update thresholds based on performance
   - Add new metrics as needed

## Future Enhancements

1. **Custom Dashboards**
   - Create team-specific dashboards
   - Add business-specific metrics
   - Include SLA tracking

2. **Advanced Alerting**
   - Machine learning-based anomaly detection
   - Predictive alerting
   - Escalation policies

3. **Integration Expansion**
   - Slack notifications
   - PagerDuty integration
   - Custom webhook support
