# Datadog Dashboard Import - Complete Guide

## 🎯 **3 Ways to Create the Dashboard**

### **Method 1: Simple JSON Import** (Recommended for beginners)
Use the simplified dashboard JSON that's guaranteed to work.

**File**: `dashboards/cta_dashboard_simple.json`

**Steps**:
1. Open Datadog in your browser
2. Go to **Dashboards** → **Dashboard List**
3. Click **New Dashboard** → **Import Dashboard JSON**
4. Drag and drop `cta_dashboard_simple.json` or paste the contents
5. Click **Import**

✅ **Pros**: Simplest method, no code needed
❌ **Cons**: Manual import each time

---

### **Method 2: Python Script** (Recommended for automation)
Use the Python script to programmatically create the dashboard.

**File**: `create_datadog_dashboard.py`

**Steps**:
```bash
# 1. Install datadog package
pip install datadog

# 2. Set environment variables
export DATADOG_API_KEY='your_api_key_here'
export DATADOG_APP_KEY='your_app_key_here'

# 3. Run the script
python3 create_datadog_dashboard.py
```

✅ **Pros**: Automated, repeatable, version controlled
✅ **Pros**: Better error messages
❌ **Cons**: Requires API keys

---

### **Method 3: Datadog API (curl)**
Use direct API call for maximum control.

```bash
export DD_API_KEY='your_api_key'
export DD_APP_KEY='your_app_key'

curl -X POST "https://api.datadoghq.com/api/v1/dashboard" \
  -H "Content-Type: application/json" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -d @dashboards/cta_dashboard_simple.json
```

✅ **Pros**: No Python dependencies
❌ **Cons**: More complex, harder to debug

---

## 🐛 **Common Import Errors & Solutions**

### **Error 1: "Unable to import dashboard with different layout type"**

**Cause**: Using `free` layout with missing or incorrect `layout` sections

**Solution**: Use the `ordered` layout type instead
```json
{
  "layout_type": "ordered",
  "widgets": [...]
}
```

✅ **Fixed in**: `cta_dashboard_simple.json`

---

### **Error 2: "Invalid query syntax"**

**Cause**: Using old query format or incorrect metric names

**Solution**: Use simple query format with `.as_count()` for counters
```json
{
  "q": "sum:cta.incidents.detected{*}.as_count()",
  "aggregator": "sum"
}
```

✅ **Fixed in**: `cta_dashboard_simple.json`

---

### **Error 3: "Widget definition is invalid"**

**Cause**: Missing required fields or incorrect widget structure

**Solution**: Ensure all required fields are present:
```json
{
  "definition": {
    "title": "Widget Title",
    "type": "timeseries",
    "requests": [...]
  }
}
```

✅ **Fixed in**: `cta_dashboard_simple.json`

---

### **Error 4: "Formula syntax error"**

**Cause**: Using complex formula syntax that Datadog can't parse

**Solution**: Use simple queries without formulas
```json
// ❌ Complex (can fail):
{
  "formulas": [{
    "formula": "query1 / query2 * 100"
  }]
}

// ✅ Simple (works):
{
  "q": "sum:cta.promotions.success{*}.as_count()",
  "aggregator": "sum"
}
```

✅ **Fixed in**: `cta_dashboard_simple.json`

---

### **Error 5: "Authentication failed"**

**Cause**: Invalid or missing API keys

**Solution**: 
```bash
# Check if keys are set
echo $DATADOG_API_KEY
echo $DATADOG_APP_KEY

# Get keys from Datadog:
# 1. Go to Datadog → Organization Settings → API Keys
# 2. Copy your API key
# 3. Go to Application Keys
# 4. Create or copy an app key

# Set keys
export DATADOG_API_KEY='paste_your_api_key'
export DATADOG_APP_KEY='paste_your_app_key'
```

---

### **Error 6: "No data available"**

**Cause**: Dashboard created but no metrics sent yet

**Solution**: Send test metrics
```bash
# Run the test script
python3 test_datadog_integration.py

# Or send custom metrics
from integrations.datadog import send_error_rate_metric
send_error_rate_metric("before_fix", 1.0, "test_run")
```

---

## 📋 **Step-by-Step Troubleshooting**

### **Step 1: Verify File Exists**
```bash
ls -la dashboards/cta_dashboard_simple.json
# Should show the file
```

### **Step 2: Validate JSON**
```bash
python3 -m json.tool dashboards/cta_dashboard_simple.json > /dev/null
# No output = valid JSON
# Error = invalid JSON
```

### **Step 3: Check File Size**
```bash
wc -l dashboards/cta_dashboard_simple.json
# Should be around 100-200 lines
```

### **Step 4: Try Python Script Method**
```bash
python3 create_datadog_dashboard.py
# Better error messages than JSON import
```

### **Step 5: Check Datadog Status**
```bash
# Visit https://status.datadoghq.com/
# Ensure Datadog is operational
```

---

## 🔍 **Debugging Import Issues**

### **Enable Debug Mode**

**In Python Script**:
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Then run
python3 create_datadog_dashboard.py
```

**In curl**:
```bash
curl -v -X POST "https://api.datadoghq.com/api/v1/dashboard" \
  -H "Content-Type: application/json" \
  -H "DD-API-KEY: ${DD_API_KEY}" \
  -H "DD-APPLICATION-KEY: ${DD_APP_KEY}" \
  -d @dashboards/cta_dashboard_simple.json
```

---

## 📊 **Dashboard Widget Reference**

### **Supported Widget Types**

1. **timeseries** - Line/bar charts ✅
2. **query_value** - Single number ✅
3. **toplist** - Top N values ✅
4. **hostmap** - Infrastructure map ❌ (not used)
5. **heatmap** - Heatmap visualization ❌ (not used)

### **Simple Dashboard Structure**

```json
{
  "title": "Dashboard Name",
  "layout_type": "ordered",
  "widgets": [
    {
      "definition": {
        "title": "Widget Title",
        "type": "timeseries",
        "requests": [
          {
            "q": "avg:metric.name{*}",
            "display_type": "line"
          }
        ]
      }
    }
  ]
}
```

---

## 🎯 **Recommended Approach**

### **For Quick Testing**:
1. Use `cta_dashboard_simple.json`
2. Import via Datadog UI
3. Send test metrics
4. Verify dashboard shows data

### **For Production**:
1. Use `create_datadog_dashboard.py`
2. Set API keys in environment
3. Run script to create dashboard
4. Automate with CI/CD

### **For Customization**:
1. Start with `cta_dashboard_simple.json`
2. Modify widgets as needed
3. Test with `python3 -m json.tool`
4. Import to Datadog
5. Iterate based on feedback

---

## 🆘 **Still Having Issues?**

### **Check These Common Mistakes**:

1. ❌ **Wrong file**: Using `cta_dashboard.json` instead of `cta_dashboard_simple.json`
2. ❌ **Syntax error**: JSON has trailing commas or quotes
3. ❌ **Wrong keys**: API key or app key is invalid
4. ❌ **Permissions**: Account doesn't have dashboard creation rights
5. ❌ **Region**: Using wrong Datadog site (US vs EU)

### **Get Help**:

1. **Check JSON validity**:
   ```bash
   python3 -m json.tool dashboards/cta_dashboard_simple.json
   ```

2. **Use Python script** (better errors):
   ```bash
   python3 create_datadog_dashboard.py
   ```

3. **Check Datadog docs**:
   - https://docs.datadoghq.com/api/latest/dashboards/
   - https://docs.datadoghq.com/dashboards/

4. **Test with minimal dashboard**:
   ```json
   {
     "title": "Test Dashboard",
     "layout_type": "ordered",
     "widgets": [
       {
         "definition": {
           "title": "Test Widget",
           "type": "query_value",
           "requests": [{"q": "avg:system.cpu.user{*}"}],
           "autoscale": true
         }
       }
     ]
   }
   ```

---

## ✅ **Success Checklist**

- [ ] File `cta_dashboard_simple.json` exists
- [ ] JSON is valid (no syntax errors)
- [ ] API keys are set (for script method)
- [ ] Datadog account is active
- [ ] Import method chosen
- [ ] Dashboard imported successfully
- [ ] Dashboard appears in Datadog UI
- [ ] Test metrics sent
- [ ] Widgets show data

---

## 📝 **Quick Reference**

| File | Purpose | When to Use |
|------|---------|-------------|
| `cta_dashboard_simple.json` | Simplified dashboard | Manual import |
| `cta_dashboard.json` | Full featured dashboard | Advanced users |
| `create_datadog_dashboard.py` | Python script | Automation |
| `test_datadog_integration.py` | Send test metrics | Testing |

---

**Last Updated**: After fixing all import issues
**Status**: ✅ All methods tested and working
