#!/usr/bin/env python3
"""
Create Datadog dashboard programmatically using the API
This is more reliable than importing JSON
"""

import os
from dotenv import load_dotenv

load_dotenv()

try:
    from datadog import initialize, api
    DATADOG_AVAILABLE = True
except ImportError:
    print("❌ Error: datadog package not installed")
    print("Install with: pip3 install datadog")
    exit(1)

# Initialize Datadog
API_KEY = os.getenv("DATADOG_API_KEY")
APP_KEY = os.getenv("DATADOG_APP_KEY")

if not API_KEY or not APP_KEY:
    print("❌ Error: DATADOG_API_KEY or DATADOG_APP_KEY not set in .env")
    exit(1)

print("=" * 80)
print("CREATE DATADOG DASHBOARD")
print("=" * 80)
print(f"\nAPI Key: {API_KEY[:10]}...")
print(f"APP Key: {APP_KEY[:10]}...")

initialize(api_key=API_KEY, app_key=APP_KEY)

# Dashboard definition
dashboard = {
    "title": "ClickHouse Logs & Audit Comparison",
    "description": "Comparison dashboard showing raw logs from ClickHouse vs audited results with anomaly detection",
    "widgets": [
        # Row 1: Key Metrics
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.logs.total{*}"}],
                "title": "Total Logs",
                "precision": 0
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.audit.total_evaluated{*}"}],
                "title": "Audited Logs",
                "precision": 0
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.comparison.audit_coverage{*}"}],
                "title": "Audit Coverage %",
                "precision": 1,
                "custom_unit": "%"
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.audit.anomaly_rate{*}"}],
                "title": "Anomaly Rate %",
                "precision": 2,
                "custom_unit": "%"
            }
        },
        # Row 2: Volume Trends
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:clickhouse.logs.total{*}",
                        "display_type": "line"
                    }
                ],
                "title": "Log Volume Over Time",
                "show_legend": True
            }
        },
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:clickhouse.audit.total_evaluated{*}",
                        "display_type": "line"
                    }
                ],
                "title": "Audit Volume Over Time",
                "show_legend": True
            }
        },
        # Row 3: Anomalies
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:clickhouse.audit.anomalies_detected{*}",
                        "display_type": "bars"
                    }
                ],
                "title": "Anomaly Detection Timeline",
                "show_legend": True
            }
        },
        {
            "definition": {
                "type": "toplist",
                "requests": [
                    {
                        "q": "top(avg:clickhouse.logs.by_component{*} by {component}, 10, 'mean', 'desc')"
                    }
                ],
                "title": "Top Components by Log Count"
            }
        },
        # Row 4: Latency Metrics
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.audit.latency_avg{*}"}],
                "title": "Avg Latency (ms)",
                "precision": 1,
                "custom_unit": "ms"
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.audit.latency_p95{*}"}],
                "title": "P95 Latency (ms)",
                "precision": 1,
                "custom_unit": "ms"
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.audit.latency_p99{*}"}],
                "title": "P99 Latency (ms)",
                "precision": 1,
                "custom_unit": "ms"
            }
        },
        # Row 5: Status Codes
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:clickhouse.audit.status_4xx{*}",
                        "display_type": "bars"
                    },
                    {
                        "q": "avg:clickhouse.audit.status_5xx{*}",
                        "display_type": "bars"
                    }
                ],
                "title": "HTTP Status Errors (4xx & 5xx)",
                "show_legend": True
            }
        },
        # Row 6: Component Health
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.comparison.healthy_components{*}"}],
                "title": "Healthy Components",
                "precision": 0
            }
        },
        {
            "definition": {
                "type": "query_value",
                "requests": [{"q": "avg:clickhouse.comparison.unhealthy_components{*}"}],
                "title": "Unhealthy Components",
                "precision": 0
            }
        },
        # Row 7: Error Rate Comparison
        {
            "definition": {
                "type": "timeseries",
                "requests": [
                    {
                        "q": "avg:clickhouse.logs.error_rate{*}",
                        "display_type": "line"
                    },
                    {
                        "q": "avg:clickhouse.audit.error_rate{*}",
                        "display_type": "line"
                    }
                ],
                "title": "Error Rate Comparison (Logs vs Audit)",
                "show_legend": True
            }
        },
        # Info Note
        {
            "definition": {
                "type": "note",
                "content": "## ClickHouse Logs & Audit Comparison Dashboard\n\nThis dashboard compares:\n- **Raw Logs** from `logs` table\n- **Audit Results** from `audit_results` table\n\n### Key Metrics:\n- **Audit Coverage**: % of logs that were audited\n- **Anomaly Rate**: % of audited logs flagged as anomalies\n- **Detection Rate**: Effectiveness of anomaly detection\n\n### Data Sources:\n- ClickHouse Cloud\n- Synced every 5 minutes via `sync_clickhouse_to_datadog.py`",
                "background_color": "blue",
                "font_size": "14",
                "text_align": "left"
            }
        }
    ],
    "layout_type": "ordered",
    "is_read_only": False,
    "notify_list": [],
    "template_variables": []
}

print("\nCreating dashboard...")

try:
    result = api.Dashboard.create(**dashboard)
    
    if result:
        print("\n✅ Dashboard created successfully!")
        print(f"\nDashboard ID: {result.get('id', 'N/A')}")
        print(f"Dashboard URL: {result.get('url', 'N/A')}")
        print(f"\nYou can now view your dashboard in Datadog!")
    else:
        print("\n❌ Failed to create dashboard (no result returned)")
        
except Exception as e:
    print(f"\n❌ Error creating dashboard: {e}")
    print("\nTroubleshooting:")
    print("1. Check your API and APP keys are correct")
    print("2. Ensure you have permission to create dashboards")
    print("3. Try importing the JSON manually instead")
    exit(1)

print("\n" + "=" * 80)
print("DASHBOARD CREATION COMPLETE")
print("=" * 80)

