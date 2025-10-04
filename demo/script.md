# CTA Demo Script

90-second talk track for live demo.

## Setup (Before Demo)

```bash
make setup
make seed
make run
```

Navigate to http://localhost:5000

## Talk Track

### 0:00 - Introduction (15s)

"This is CTA: Trace & Judge, a Causal Trust Agent for diagnosing multi-agent failures.

The problem: When agent pipelines fail, engineers spend hours tracing through logs. Our MVP automates root-cause analysis with auditable JSONL traces."

### 0:15 - Show Good Run (15s)

Click "Run: Good"

"Here's a successful run through our 3-agent pipeline: Intake, Retriever, and Auditor. All green. Clean trace events, each step logged with inputs and outputs."

Expand one step event to show JSON.

### 0:30 - Trigger Flaky Run (15s)

Click "Run: Flaky"

"Now the flaky mode. Schema drift injected: the Retriever returns 'amt' instead of 'amount'. Watch the Auditor fail with a KeyError."

Point to red status badge and error event.

### 0:45 - Run CTA Analysis (20s)

Click "Run CTA Analysis"

"CTA analyzes the trace in under 2 seconds. It identifies the primary cause: the fetch_transactions tool. Provides a 5-Whys chain, evidence excerpts, and a proposed fix."

Scroll through symptoms, evidence, and why-chain.

### 1:05 - Apply Fix (15s)

Click "Apply Fix & Rerun"

"One click applies the schema adapter and reruns. Now patched mode succeeds. The amt field is normalized to amount before reaching the Auditor."

Show green status.

### 1:20 - Highlight Metrics (10s)

Return to homepage, show table.

"Compare MTTR: human baseline 150 seconds vs CTA 2 seconds. Deterministic, auditable, extensible."

## Key Points to Emphasize

- Deterministic demo flow: good, flaky, diagnose, patch, succeed
- Clean JSONL traces for auditability
- Heuristic CTA works without LLM, but supports optional OpenAI integration
- Single command to run: make run
- Production-ready structure: Flask + HTMX, sqlite + JSONL, LangGraph agents

## Fallback (If LLM Fails)

"Even without an LLM API key, our heuristic analyzer detects the schema mismatch and provides actionable insights. This ensures the system works in offline or resource-constrained environments."

## Stretch Discussion (If Time)

- "Next steps: integrate OpenTelemetry spans, Datadog correlation, ClickHouse for clustering similar failures."
- "The agent graph is minimal now but designed to scale: swap in ReAct, chain-of-thought, or domain-specific reasoners."

