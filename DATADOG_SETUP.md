# Datadog Integration Setup Guide

## ✅ Issues Fixed

### 1. **Test Script Import Error - FIXED**
**Problem**: `ModuleNotFoundError: No module named 'dotenv'`

**Solution**: Made `python-dotenv` optional in `integrations/datadog.py`

```python
# Make dotenv optional
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass
```

### 2. **Dashboard Import Error - FIXED**
**Problem**: "Unable to import dashboard with different layout type"

**Solution**: Created properly formatted dashboard JSON with `ordered` layout type using modern Datadog API format

## 🎯 Current Status

✅ **Test Script**: Now runs successfully without errors
✅ **Dashboard JSON**: Properly formatted for Datadog import
✅ **Integration Module**: Graceful fallback when SDK unavailable

## 📋 How to Use

### 1. Install Datadog SDK (Optional but Recommended)

```bash
# Activate virtual environment
source env/bin/activate

# Install datadog package
pip install datadog
```

### 2. Configure Environment Variables

```bash
export DATADOG_API_KEY='your_api_key_here'
export DATADOG_APP_KEY='your_app_key_here'  # Optional
export DATADOG_SITE='datadoghq.com'  # or datadoghq.eu
```

### 3. Test the Integration

```bash
python3 test_datadog_integration.py
```

**Expected Output (without SDK)**:
```
Datadog Available: False
Integration Enabled: False
⚠️  Datadog integration is disabled.
```

**Expected Output (with SDK)**:
```
Datadog Available: True
Integration Enabled: True
✓ Sent error_rate metric: 100.00% (phase: before_fix)
✓ Sent error_rate metric: 0.00% (phase: after_fix)
...
```

### 4. Import Dashboard to Datadog

1. Open Datadog in your browser
2. Go to **Dashboards** → **New Dashboard** → **Import Dashboard JSON**
3. Upload `dashboards/cta_dashboard.json`
4. Click **Import**

The dashboard will be created with 10 widgets tracking:
- Error Rate (Before vs After)
- Latency (Before vs After)
- MTTR by Method
- Incidents Detected
- Canary Tests
- Fix Promotion Success Rate
- Analysis Method Distribution
- Cached Fix Hit Rate
- Workflow Duration
- Error Rate Improvement

## 🔧 Integration Behavior

### Without Datadog SDK
- ✅ System works normally
- ❌ No metrics sent
- ⚠️  Warnings in logs (can be ignored)
- 🎯 Use for: Local development, testing

### With Datadog SDK
- ✅ Full observability
- ✅ Metrics sent to Datadog
- ✅ Before/after tracking
- ✅ Dashboard visualization
- 🎯 Use for: Production, demos

## 📊 Dashboard Features

### Modern API Format
The dashboard now uses Datadog's modern API format with:
- **Formulas**: For metric calculations
- **Response Format**: Properly typed (timeseries/scalar)
- **Data Source**: Explicit metrics specification
- **Ordered Layout**: Automatic widget stacking

### Widgets Included

1. **Error Rate Comparison**
   - Before fix (red)
   - After fix (green)
   - Shows improvement over time

2. **Latency Comparison**
   - Before fix (red)
   - After fix (green)
   - Tracks performance improvement

3. **MTTR Tracking**
   - By analysis method (heuristic/llm/cached)
   - Shows autonomous recovery speed

4. **Incidents Counter**
   - Total incidents detected
   - Single value widget

5. **Canary Test Results**
   - Passed tests (green bars)
   - Failed tests (red bars)
   - Over time visualization

6. **Promotion Success Rate**
   - Percentage calculation
   - Formula: `promotions / (promotions + rollbacks) * 100`

7. **Method Distribution**
   - Sunburst chart
   - Shows heuristic vs llm vs cached

8. **Cached Fix Hit Rate**
   - Percentage calculation
   - Learning effectiveness metric

9. **Workflow Duration**
   - By action (promote/rollback)
   - Bar chart visualization

10. **Error Rate Improvement**
    - Calculated improvement metric
    - Shows fix effectiveness

## 🐛 Troubleshooting

### Test Script Issues

**Issue**: `ModuleNotFoundError`
```bash
# Solution: Install missing package
pip install datadog python-dotenv
```

**Issue**: Integration disabled
```bash
# Solution: Set environment variables
export DATADOG_API_KEY='your_key'
```

### Dashboard Import Issues

**Issue**: "Unable to import dashboard"
```
# Solution: Use the fixed cta_dashboard.json file
# It now uses ordered layout with modern API format
```

**Issue**: Widgets show "No data"
```bash
# Solution: Send test metrics first
python3 test_datadog_integration.py
```

**Issue**: Query syntax errors
```
# Solution: The new dashboard uses proper formula syntax
# No manual fixes needed - use the provided JSON
```

## 📝 Usage in Code

### Basic Integration

```python
from integrations.datadog import send_error_rate_metric, is_enabled

if is_enabled():
    # Send before metrics
    send_error_rate_metric("before_fix", 1.0, run_id)
    
    # ... apply fix ...
    
    # Send after metrics
    send_error_rate_metric("after_fix", 0.0, run_id)
```

### Complete Workflow

```python
from cta.actions import execute_cta_workflow

# Measure before state
before_metrics = {
    "error_rate": 1.0,
    "latency_ms": 500.0
}

# Execute CTA workflow with Datadog integration
result = execute_cta_workflow(run_id, report, before_metrics)

# Metrics automatically sent to Datadog:
# - Incident detection
# - Analysis completion
# - Patch application
# - Canary results
# - Promotion decision
# - Before/after comparison
# - MTTR tracking
```

## 🎉 Success Indicators

When everything is working correctly, you should see:

1. **Test Script**: 
   - ✅ No import errors
   - ✅ Runs to completion
   - ✅ Shows integration status

2. **Dashboard**:
   - ✅ Imports without errors
   - ✅ Shows 10 widgets
   - ✅ No query syntax errors

3. **Runtime** (with SDK):
   - ✅ Metrics in Datadog UI
   - ✅ Dashboard shows data
   - ✅ Before/after comparison visible

4. **Runtime** (without SDK):
   - ✅ System works normally
   - ⚠️  Warnings about disabled integration
   - ❌ No metrics sent (expected)

## 🚀 Next Steps

1. **Install SDK**: `pip install datadog`
2. **Set API Keys**: Export environment variables
3. **Run Test**: `python3 test_datadog_integration.py`
4. **Import Dashboard**: Upload `cta_dashboard.json`
5. **Generate Metrics**: Run demo or real pipeline
6. **View Dashboard**: See before/after comparisons

## 📚 Additional Resources

- **Full Documentation**: `DATADOG_INTEGRATION.md`
- **Test Script**: `test_datadog_integration.py`
- **Dashboard JSON**: `dashboards/cta_dashboard.json`
- **Integration Module**: `integrations/datadog.py`

---

**Status**: ✅ All issues resolved and ready for use!
