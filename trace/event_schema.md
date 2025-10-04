# Trace Event Schema

Each line in a JSONL trace file is one JSON object representing a discrete event in the agent pipeline execution.

## Common Fields

All events share these base fields:

- `ts` (float): Unix epoch timestamp in seconds
- `run_id` (str): Unique identifier for this execution run
- `idx` (int): Monotonically increasing index within the run
- `type` (str): Event type - one of: "step", "tool", "note", "error"
- `latency_ms` (int, optional): Duration of the operation in milliseconds

## Event Type: "step"

Represents a complete agent step execution.

Additional fields:
- `agent` (str): Name of the agent executing this step
- `step_id` (str): UUID for this specific step
- `input` (any): Input parameters passed to the step (kept small for readability)
- `output` (any): Output returned by the step

Example:
```json
{
  "ts": 1696435200.123,
  "run_id": "run_abc123",
  "idx": 0,
  "type": "step",
  "agent": "Intake",
  "step_id": "550e8400-e29b-41d4-a716-446655440000",
  "input": {"mode": "good"},
  "output": {"status": "ready"},
  "latency_ms": 45
}
```

## Event Type: "tool"

Represents a tool invocation.

Additional fields:
- `tool` (str): Name of the tool being called
- `args` (object): Arguments passed to the tool
- `output` (any): Result returned by the tool

Example:
```json
{
  "ts": 1696435200.456,
  "run_id": "run_abc123",
  "idx": 1,
  "type": "tool",
  "tool": "fetch_transactions",
  "args": {"flaky": false},
  "output": [{"id": "T1", "currency": "USD", "amount": 12.0}],
  "latency_ms": 120
}
```

## Event Type: "error"

Represents an error that occurred during execution.

Additional fields:
- `message` (str): Error message
- `context` (object): Additional context about where/why the error occurred

Example:
```json
{
  "ts": 1696435201.789,
  "run_id": "run_abc123",
  "idx": 5,
  "type": "error",
  "message": "KeyError: 'amount'",
  "context": {"agent": "Auditor", "tx_id": "T1"}
}
```

## Storage

Events are stored in two places:

1. **JSONL files**: `data/runs/<run_id>.jsonl` - Append-only log of all events
2. **SQLite**: `data/traces.sqlite` - Indexed storage for quick queries

Both storage layers must maintain consistency.

