import time

def print_box(title, content, color="blue"):
    colors = {
        "blue": "\033[94m",
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "cyan": "\033[96m",
        "reset": "\033[0m"
    }
    
    c = colors.get(color, colors["blue"])
    reset = colors["reset"]
    
    width = 80
    print(f"\n{c}{'═' * width}{reset}")
    print(f"{c}║ {title.center(width-4)} ║{reset}")
    print(f"{c}{'═' * width}{reset}")
    for line in content.split('\n'):
        if line.strip():
            print(f"{c}║{reset} {line.ljust(width-3)} {c}║{reset}")
    print(f"{c}{'═' * width}{reset}\n")

def print_event(event, label=""):
    print(f"  {label}")
    print(f"  {event}")
    print()

def pause():
    time.sleep(1.5)

print("\n\n")
print("╔" + "═" * 78 + "╗")
print("║" + " CAUSAL TRUST AGENT (CTA) - AUTONOMOUS REMEDIATION DEMO ".center(78) + "║")
print("╚" + "═" * 78 + "╝")

print("\n\n📊 EXAMPLE: OpenStack Nova Log Processing\n")
pause()

print_box("STEP 1: NORMAL OPERATION", """
3-Agent Pipeline Processing Log Events:
  Intake → Retriever → Auditor

Sample Input Event (LineId: 1):
  {
    "LineId": 1,
    "Level": "INFO",           ← Uppercase (correct)
    "Component": "nova.compute.manager",
    "Content": "GET /v2/servers status: 200 time: 0.247",
    "latency_ms": 247
  }
""", "green")
pause()

print("🔄 Pipeline Flow:")
print()
print("  ┌─────────┐      ┌───────────┐      ┌──────────┐")
print("  │ Intake  │ ───> │ Retriever │ ───> │ Auditor  │")
print("  └─────────┘      └───────────┘      └──────────┘")
print("      │                  │                  │")
print("      │                  │                  │")
print("      └──────────────────┴──────────────────┘")
print("                         │")
print("                    ✅ SUCCESS")
print()
pause()

print("  Auditor checks:")
print("    evt['Level'] == 'INFO'  ✓")
print("    evt['latency_ms'] == 247  ✓ (< 400ms threshold)")
print("    Result: {'flag': False, 'reason': 'latency=247ms'}")
print()
pause()

print_box("STEP 2: INCIDENT - UPSTREAM SCHEMA CHANGES", """
⚠️  Upstream service changes field name: Level → level

New Event (LineId: 2):
  {
    "LineId": 2,
    "level": "WARNING",        ← Lowercase (WRONG!)
    "Component": "nova.compute.manager",
    "Content": "GET /v2/servers status: 200 time: 0.258",
    "latency_ms": 258
  }

Missing: "Level" (uppercase)
""", "yellow")
pause()

print("🔄 Pipeline Flow:")
print()
print("  ┌─────────┐      ┌───────────┐      ┌──────────┐")
print("  │ Intake  │ ───> │ Retriever │ ───> │ Auditor  │")
print("  └─────────┘      └───────────┘      └──────────┘")
print("      ✓                 ✓                  ✗")
print("                                           │")
print("                                    KeyError: 'Level'")
print()
pause()

print("  Auditor tries:")
print("    evt['Level']  ✗ KeyError: 'Level'")
print()
print("  Python Exception Raised:")
print("    Traceback (most recent call last):")
print("      File 'agents/tools.py', line 38, in evaluate_event")
print("        level = evt['Level']")
print("    KeyError: 'Level'")
print()
pause()

print_box("STEP 3: TRACE CAPTURE", """
Trace Events Logged:

Event #1 (type: step):
  {"ts": 1733345678.1, "type": "step", "agent": "Intake", 
   "output": {"status": "ready"}}

Event #2 (type: tool):
  {"ts": 1733345678.2, "type": "tool", "tool": "fetch_log_events",
   "output": [{"LineId": 2, "level": "WARNING", ...}]}  ← Has "level"

Event #3 (type: error):
  {"ts": 1733345678.3, "type": "error", 
   "message": "KeyError: 'Level'",             ← Missing "Level"
   "context": {"agent": "Auditor", "event_id": 2}}
""", "red")
pause()

print_box("STEP 4: CTA AUTONOMOUS ANALYSIS", """
CTA Reads Trace Events and Performs Root Cause Analysis:

1️⃣  Find Error Events:
    → Found: KeyError: 'Level' in Auditor

2️⃣  Find Tool Outputs:
    → fetch_log_events returned: {"level": "WARNING", ...}

3️⃣  Pattern Match:
    ✓ Error says: Missing 'Level' (uppercase)
    ✓ Tool output has: 'level' (lowercase)
    ✓ Conclusion: Schema drift detected!

4️⃣  Build Causal Chain (5-Whys):
    Why1: Auditor failed?     → KeyError: 'Level'
    Why2: Why KeyError?       → Field doesn't exist
    Why3: Where should it be? → Retriever's output
    Why4: What's there?       → Field 'level' (lowercase)
    Why5: Root Cause?         → Schema drift (Level → level)
""", "cyan")
pause()

print("📊 CTA Report Generated:")
print()
print("  {")
print('    "primary_cause": "Schema drift in fetch_log_events",')
print('    "confidence": 0.92,')
print('    "symptoms": ["KeyError: \'Level\'", "Field renamed Level → level"],')
print('    "evidence": [')
print('      {"step": "tool_2", "excerpt": "output has \'level\': \'WARNING\'"},')
print('      {"step": "error_3", "excerpt": "KeyError: \'Level\'"}')
print('    ],')
print('    "proposed_fix": {')
print('      "tool_schema_patch": "map level → Level",')
print('      "implementation": "set_adapter({\'level\': \'Level\'})"')
print('    }')
print("  }")
print()
pause()

print_box("STEP 5: AUTONOMOUS PATCHING", """
CTA Actions (No Human Approval Needed):

1. Parse Fix from Report:
   → Adapter: {"level": "Level"}

2. Apply Adapter:
   → set_adapter({"level": "Level"})
   → Saved to: data/adapter_config.json
   → Hot-reloaded (no restart needed)

3. Transform Function Active:
   → apply_adapters({"level": "X"}) → {"Level": "X"}
""", "green")
pause()

print("🔧 Adapter Applied:")
print()
print("  BEFORE:                      AFTER:")
print("  {                            {")
print('    "LineId": 2,                 "LineId": 2,')
print('    "level": "WARNING",  ──────> "Level": "WARNING",  ✓')
print('    "latency_ms": 258            "latency_ms": 258')
print("  }                            }")
print()
pause()

print_box("STEP 6: CANARY TESTING", """
CTA Tests Fix on Last 5 Events:

Canary Event 1: {"level": "INFO", ...}
  → apply_adapters() → {"Level": "INFO", ...}
  → evaluate_event() → SUCCESS ✓

Canary Event 2: {"level": "WARNING", ...}
  → apply_adapters() → {"Level": "WARNING", ...}
  → evaluate_event() → SUCCESS ✓

Canary Event 3: {"level": "INFO", ...}
  → apply_adapters() → {"Level": "INFO", ...}
  → evaluate_event() → SUCCESS ✓

Canary Event 4: {"level": "ERROR", ...}
  → apply_adapters() → {"Level": "ERROR", ...}
  → evaluate_event() → SUCCESS ✓ (flagged as anomaly)

Canary Event 5: {"level": "INFO", ...}
  → apply_adapters() → {"Level": "INFO", ...}
  → evaluate_event() → SUCCESS ✓
""", "cyan")
pause()

print("📊 Canary Metrics:")
print()
print("  Total Events:    5")
print("  Errors:          0")
print("  Error Rate:      0.0% (threshold: < 1%)")
print("  P95 Latency:     261ms (threshold: < 500ms)")
print("  Status:          ✅ PASS")
print()
pause()

print_box("STEP 7: PROMOTE DECISION", """
Automated Decision Logic:

IF canary.error_rate < 0.01 AND canary.p95_latency < 500:
    decision = "PROMOTE"
    keep_adapter_active()
    save_signature_for_learning()
ELSE:
    decision = "ROLLBACK"
    clear_adapters()
    alert_humans()

Result: ✅ PROMOTED
  → Adapter stays active
  → All future events auto-transformed
  → Incident signature saved
""", "green")
pause()

print("🎯 Decision: PROMOTE")
print()
print("  Active Adapters:")
print('    {"level": "Level"}  ← Will transform ALL future events')
print()
print("  Signature Saved:")
print("    {")
print('      "id": "sig_123",')
print('      "cause": "schema_drift_Level_to_level",')
print('      "embedding": [0.23, 0.87, ...],  ← Vector for similarity')
print('      "patch": {"level": "Level"}')
print("    }")
print()
pause()

print_box("STEP 8: VALIDATION - PIPELINE RECOVERED", """
New Event Arrives (LineId: 6):
  {
    "LineId": 6,
    "level": "INFO",           ← Still lowercase (drift persists)
    "Component": "nova.api",
    "latency_ms": 235
  }

Pipeline Flow WITH Adapter:
""", "green")
pause()

print("  ┌─────────┐      ┌───────────┐      ┌──────────────┐      ┌──────────┐")
print("  │ Intake  │ ───> │ Retriever │ ───> │ apply_adapters│ ───> │ Auditor  │")
print("  └─────────┘      └───────────┘      └──────────────┘      └──────────┘")
print("      ✓                 ✓                     ✓                   ✓")
print("                                              │")
print("                               level → Level transformation")
print()
pause()

print('  Event after adapter: {"LineId": 6, "Level": "INFO", ...}')
print("  Auditor processes: evt['Level'] → SUCCESS ✓")
print("  Result: {'flag': False, 'reason': 'latency=235ms'}")
print()
pause()

print_box("STEP 9: LEARNING - REPEAT INCIDENT", """
Second Incident (Same Schema Drift):

New batch of events with "level" (lowercase)...

CTA Check Signature Cache:
  1. Extract features from error pattern
  2. Create embedding: [0.22, 0.88, ...]
  3. Query signature DB for similarity
  4. Match found! (similarity: 98%)

Result: ✅ INSTANT FIX
  → Cached adapter applied immediately
  → No RCA needed (saved ~4 seconds)
  → No LLM call needed (saved cost)
  → Events processed successfully
""", "green")
pause()

print("⚡ Performance Comparison:")
print()
print("  First Incident:        Second Incident:")
print("  ├─ Detect: 0.1s        ├─ Detect: 0.1s")
print("  ├─ RCA: 2.0s           ├─ RCA: 0.0s (cached!)")
print("  ├─ Patch: 0.5s         ├─ Patch: 0.2s")
print("  ├─ Canary: 2.0s        ├─ Canary: 0.5s (faster)")
print("  └─ Total: 4.6s         └─ Total: 0.8s")
print()
print("  📈 80% faster recovery!")
print()
pause()

print_box("SUMMARY: AUTONOMOUS LOOP", """
Complete Flow (No Human in the Loop):

  ┌─────────────────────────────────────────────────────────┐
  │  1. DETECT    → Runtime exception (KeyError)            │
  │  2. ANALYZE   → CTA reads traces, finds pattern         │
  │  3. GENERATE  → Proposes adapter patch                  │
  │  4. APPLY     → Hot-reloads adapter                     │
  │  5. TEST      → Canary on recent events                 │
  │  6. DECIDE    → Promote if thresholds pass              │
  │  7. LEARN     → Save signature for next time            │
  │  8. REPEAT    → Instant fix on similar incidents        │
  └─────────────────────────────────────────────────────────┘

Key Metrics:
  ⏱️  MTTR (First):    <5 seconds (autonomous)
  ⏱️  MTTR (Repeat):   <1 second (cached)
  👤 Human Actions:   0 (fully autonomous)
  ✅ Recovery Rate:   100%
  📊 Error Rate:      0% (after fix)
""", "cyan")

print("\n\n")
print("╔" + "═" * 78 + "╗")
print("║" + " END OF DEMO - System is Autonomous, Learning, and Self-Healing ".center(78) + "║")
print("╚" + "═" * 78 + "╝")
print("\n\n")

