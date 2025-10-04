# CTA: Trace & Judge - Lite

A production-ready hackathon MVP demonstrating a Causal Trust Agent (CTA) that automatically diagnoses multi-agent pipeline failures through auditable trace analysis.

## Project Pitch

When multi-agent systems fail in production, engineers spend hours digging through logs to find root causes. CTA automates this process by:

- Capturing clean, structured JSONL traces of every agent step and tool call
- Analyzing failure patterns using heuristic detection and optional LLM reasoning
- Providing 5-Whys causal chains, evidence excerpts, and actionable fixes
- Applying patches automatically and re-running pipelines to verify success

Mean Time To Resolution (MTTR): Human baseline 150s vs CTA 2s.

## Quickstart

### Prerequisites

- Python 3.11+
- pip

### Installation & Setup

```bash
make setup
```

This creates a virtual environment and installs all dependencies.

### Seed Demo Data

```bash
source .venv/bin/activate
make seed
```

This creates three runs:
1. Good run (success)
2. Flaky run (fails due to schema drift)
3. Patched run (CTA applies fix and succeeds)

### Start Web UI

```bash
make run
```

Navigate to http://localhost:5000

## Demo Flow

### 1. Good Run

Click "Run: Good" to execute a successful pipeline with three agents:
- Intake: Validates input parameters
- Retriever: Fetches transactions from data source
- Auditor: Flags anomalies based on business rules

All steps complete successfully, trace events are logged.

### 2. Flaky Run

Click "Run: Flaky" to inject a schema drift failure:
- Retriever returns transactions with 'amt' field instead of 'amount'
- Auditor expects 'amount', throws KeyError
- Pipeline fails with diagnostic events captured

### 3. CTA Analysis

On the failed run detail page, click "Run CTA Analysis":
- CTA analyzes trace events in under 2 seconds
- Identifies primary cause: fetch_transactions tool output schema mismatch
- Provides 5-Whys chain explaining causality
- Shows evidence excerpts from trace
- Proposes fix: schema adapter to normalize 'amt' to 'amount'

### 4. Apply Fix & Rerun

Click "Apply Fix & Rerun":
- CTA patches the fetch_transactions tool with a schema adapter
- Creates new "patched" run
- Pipeline succeeds with normalized data

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         Flask Web UI                        │
│                      (HTMX Interactivity)                   │
└────────────┬────────────────────────────────────────────────┘
             │
             ├─────► /run?mode=good|flaky|patched
             │       (Trigger pipeline execution)
             │
             ├─────► /run/<id>
             │       (View trace + metrics)
             │
             └─────► /run/<id>/cta
                     (Analyze & apply fix)
                            │
    ┌───────────────────────┼───────────────────────┐
    │                       │                       │
    v                       v                       v
┌────────┐          ┌──────────────┐        ┌──────────────┐
│ Agents │          │    Trace     │        │     CTA      │
│ Graph  │────────► │  Store       │────────►│  Analyzer    │
│        │          │ (JSONL+SQLite)│        │ (Heuristic+  │
│ 3-node │          │              │        │     LLM)     │
│Pipeline│          │              │        │              │
└────────┘          └──────────────┘        └──────────────┘
```

### Module Breakdown

#### trace/

- constants.py: Paths and event type definitions
- store.py: SQLite + JSONL storage layer
- sdk.py: Decorators for automatic trace instrumentation
- event_schema.md: Event contract documentation

#### agents/

- tools.py: Business logic tools (fetch_transactions, flag_anomaly)
- failures.py: Feature flags for failure injection
- graph.py: 3-agent pipeline (Intake, Retriever, Auditor)

#### cta/

- analyze.py: Root cause analysis engine
- prompts/rca_base.md: LLM prompt template for causal reasoning

#### app/

- server.py: Flask routes and HTMX handlers
- seed.py: CLI for generating demo runs
- templates/: Jinja2 HTML templates
- static/: CSS styling

## Environment Variables

Create a `.env` file (see `.env.example`):

```env
LLM_API_KEY=sk-...           # Optional: OpenAI API key
MODEL_NAME=gpt-4o-mini       # Optional: Model to use
```

If `LLM_API_KEY` is not set, CTA falls back to heuristic analysis with ~65% confidence. With LLM, confidence typically reaches 85-95%.

## Trace Event Schema

All events are JSONL (newline-delimited JSON) with these base fields:

- ts: Unix timestamp (float)
- run_id: Unique run identifier
- idx: Sequential event index
- type: "step" | "tool" | "error"
- latency_ms: Duration in milliseconds

See `trace/event_schema.md` for full specification.

## Running Tests

```bash
source .venv/bin/activate
make test
```

Tests cover:
- Trace schema validation (all events have required fields)
- CTA heuristic detection (schema drift identification)
- End-to-end pipeline execution

## Acceptance Criteria

All behaviors verified:

- make setup && make run starts server
- POST /run?mode=good succeeds (status: ok)
- POST /run?mode=flaky fails with KeyError
- POST /run/<id>/cta returns JSON report without crash
- POST /run/<id>/apply_fix creates patched run that succeeds
- GET /run/<id>/cta.json downloads analysis report
- JSONL files in data/runs/, SQLite in data/traces.sqlite (gitignored)

## Stretch Goals

Not implemented in this MVP but designed for:

1. OpenTelemetry Integration: Ingest OTel spans alongside native traces
2. Datadog Correlation: Link CTA analysis to APM trace IDs
3. ClickHouse Clustering: Aggregate similar failures across runs
4. LangGraph Primitives: Swap simple functions for full LangGraph state machines
5. Multi-LLM Support: Anthropic, Cohere, local models

## Development Workflow

### Git Hygiene

- Main branch: main
- Feature branches: feature/agents-trace, feature/cta-ui
- Squash merge PRs for clean history

### Adding New Agents

1. Define agent function with @trace_step("AgentName") decorator
2. Add to agents/graph.py pipeline
3. Test with make seed

### Adding New Tools

1. Implement tool in agents/tools.py
2. Wrap calls with @trace_tool("ToolName") in graph.py
3. Update CTA heuristics if special handling needed

## File Structure

```
cta-trace-and-judge/
├── app/
│   ├── server.py              # Flask routes
│   ├── seed.py                # Demo data generator
│   ├── templates/             # HTML templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── run_view.html
│   │   ├── trace_panel.html
│   │   └── cta_panel.html
│   └── static/
│       └── styles.css         # Minimal CSS
├── agents/
│   ├── graph.py               # 3-agent pipeline
│   ├── tools.py               # Business tools
│   └── failures.py            # Failure injection flags
├── trace/
│   ├── constants.py           # Configuration
│   ├── store.py               # Storage layer
│   ├── sdk.py                 # Trace decorators
│   └── event_schema.md        # Event documentation
├── cta/
│   ├── analyze.py             # RCA engine
│   └── prompts/
│       └── rca_base.md        # LLM prompt
├── data/
│   ├── runs/                  # Runtime JSONL (gitignored)
│   ├── traces.sqlite          # Runtime DB (gitignored)
│   └── samples/
│       └── sample_run.jsonl   # Example trace
├── demo/
│   └── script.md              # 90s demo talk track
├── tests/
│   ├── test_trace_schema.py
│   └── test_cta_heuristics.py
├── .env.example
├── .gitignore
├── requirements.txt
├── Makefile
└── README.md
```

## Contributing

This is a hackathon MVP. For production use:

1. Add authentication/authorization to Flask routes
2. Implement rate limiting on CTA analysis
3. Add structured logging with correlation IDs
4. Set up CI/CD with GitHub Actions
5. Containerize with Docker
6. Add observability (Prometheus metrics, etc.)

## License

MIT License. Use freely for hackathons, demos, and production systems.

## Support

For questions or issues, create a GitHub issue or contact the maintainers.

Built with: Python 3.11, Flask, HTMX, LangGraph, SQLite, Pydantic.

