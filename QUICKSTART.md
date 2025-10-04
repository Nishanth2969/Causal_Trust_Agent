# Quick Start Guide

## One Command Setup

```bash
cd cta-trace-and-judge
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m app.seed
```

## Run the Web UI

```bash
export FLASK_APP=app/server.py
flask run
```

Or use the Makefile:

```bash
make run
```

Open http://localhost:5000

## Demo Flow

1. View the pre-seeded runs on the homepage
2. Click on the flaky run to see the failure
3. Click "Run CTA Analysis" to diagnose the root cause
4. Review the 5-Whys chain and evidence
5. Click "Apply Fix & Rerun" to patch and verify success

## Optional: Add LLM Support

Create a `.env` file:

```env
LLM_API_KEY=sk-your-openai-key
MODEL_NAME=gpt-4o-mini
```

The system works without an LLM using heuristic analysis.

## Run Tests

```bash
pytest tests/ -v
```

## File a Sample Run

```bash
cat data/samples/sample_run.jsonl | jq
```

## Acceptance Checklist

- Homepage loads with run list
- Good run shows green status
- Flaky run shows red status with error
- CTA panel displays analysis report
- Apply fix creates new patched run
- All tests pass

