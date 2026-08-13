# interface.ai Computer-Use Automation

A focused implementation of the interface.ai take-home assignment.

The system demonstrates the central production model:

**Discovery is model-driven; replay is deterministic and model-free.**

For this implementation, I intentionally chose not to use an external API key. I treated that as an additional engineering challenge: the complete discovery-to-replay workflow had to work locally and produce the correct result without depending on a hosted model or external service.

The implementation also includes an optional local Ollama planner to demonstrate how an LLM can be introduced into the discovery layer when desired. The replay layer remains deterministic regardless of which discovery planner is used.

The repository uses a local synthetic banking application so no real credentials or financial data are needed.

## Architecture

```text
Natural-language goal
        |
        v
Discovery Agent
  - Offline deterministic planner (default)
  - Optional local Ollama LLM adapter (no API key)
        |
        v
Structured action trace
        |
        v
Artifact compiler
        |
        v
Versioned capability artifact
        |
        v
Deterministic replay engine
        |
        +--> success / business outcome
        |
        +--> recoverable failure / escalation
```

The replay engine never calls an LLM.

## Requirements

- Python 3.11+
- Chromium
- Playwright Python package

The demonstrated workflow does not require an external API key or cloud service.

The default discovery mode is completely offline and deterministic. An optional Ollama adapter is included to demonstrate LLM-driven discovery using a locally running model.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
playwright install chromium
```

If Chromium is already installed, Playwright can use it normally.

## Run tests

```bash
PYTHONPATH=src pytest -q
```

## Start the synthetic banking application

Terminal 1:

```bash
source .venv/bin/activate
PYTHONPATH=. python -m uvicorn demo_app.app:app --host 127.0.0.1 --port 8000
```

The application is available at:

```text
http://127.0.0.1:8000
```

## End-to-end demonstration

I intentionally ran the primary workflow without an API key or external model service. This was a deliberate challenge to ensure that the core capability discovery, artifact generation, and deterministic replay pipeline could independently produce the correct result.

Terminal 2:

```bash
source .venv/bin/activate
export PYTHONPATH=src
```

Discover the capability:

```bash
python -m cua.cli discover \
  --url http://127.0.0.1:8000 \
  --goal "Look up member 12345 and read their current savings balance" \
  --output evidence/discovery-artifact.json \
  --log evidence/discovery.log
```

Replay it deterministically:

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact.json \
  --url http://127.0.0.1:8000 \
  --member-id 12345 \
  --log evidence/replay-success.log
```

Expected result:

```text
REPLAY SUCCESS
savings_balance=$4821.52
```

## Business outcome demonstration

A missing member is not a system crash:

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact.json \
  --url http://127.0.0.1:8000 \
  --member-id 99999 \
  --log evidence/replay-not-found.log
```

Expected classification:

```text
BUSINESS_OUTCOME
MEMBER_NOT_FOUND
```

## Injected application failure

The synthetic application intentionally returns an application error for member `50000`.

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact.json \
  --url http://127.0.0.1:8000 \
  --member-id 50000 \
  --log evidence/replay-failure.log
```

Expected classification:

```text
HARD_FAILURE
CHECKPOINT_FAILED
```

## Human intervention

Run the failure case headed:

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact.json \
  --url http://127.0.0.1:8000 \
  --member-id 50000 \
  --headed \
  --escalate
```

The replay engine creates an intervention request containing:

- current step
- current URL
- failure classification
- last successful checkpoint
- session identifier
- redacted context

The replay process keeps the browser headed during escalation so the live browser state remains available for operator handoff. The current demo records the intervention state to the filesystem but does not persist a reconnectable session identifier or implement operator resume. A production handoff layer would associate the intervention with the live browser session and expose explicit claim, takeover, correction, and resume operations. The replay engine creates a filesystem-backed intervention request for inspection. The demo keeps the browser headed during escalation so the live session can be handed to a human operator. A production implementation would provide operator commands or a UI for inspecting and resuming interventions.

## Optional LLM-driven discovery

The primary demonstration intentionally does not use an API key or hosted model. However, the discovery layer is designed to support an LLM planner.

The repository includes an Ollama adapter that can be used with a locally running model:

```bash
python -m cua.cli discover \
  --url http://127.0.0.1:8000 \
  --goal "Look up member 12345 and read their current savings balance" \
  --planner ollama \
  --output evidence/discovery-artifact.json \
  --log evidence/discovery-ollama.log
```

## Artifact

The artifact is deliberately separate from the model transcript. It stores:

- capability identity
- application/surface metadata
- parameterized inputs
- ordered typed actions
- locator strategies
- checkpoints
- business outcomes
- safety policy

A discovery transcript is evidence/debugging data. The artifact is the reusable production capability.

## Safety

The action gate runs before every browser action.

The default demo allowlist permits:

- navigate
- fill
- click
- wait
- extract
- checkpoint

The policy rejects:

- arbitrary domains
- shell execution
- unsupported action types

Sensitive values are redacted from persistent operational logs.

## Repository structure

```text
.
├── README.md
├── REPORT.md
├── Makefile
├── pyproject.toml
├── .gitignore
├── .env.example
├── src/cua/
│   ├── agent/
│   │   ├── model.py
│   │   ├── offline.py
│   │   └── ollama.py
│   ├── artifact/
│   │   ├── schema.py
│   │   └── compiler.py
│   ├── replay/
│   │   ├── engine.py
│   │   └── errors.py
│   ├── safety/
│   │   └── policy.py
│   ├── escalation/
│   │   └── manager.py
│   ├── surfaces/
│   │   └── browser.py
│   ├── cli.py
│   ├── config.py
│   └── logging_utils.py
├── demo_app/
│   ├── app.py
│   └── templates/
├── tests/
└── evidence/
```

## What is intentionally cut

- Native desktop automation is represented by the surface interface but not implemented.
- Production distributed infrastructure is not included.
- Real tenant management is represented through compatibility/configuration fields rather than infrastructure.
- The offline planner is intentionally narrow to the demo capability.
- The local Ollama adapter is optional; the default demo does not require any model service.

These cuts keep the implementation focused on the load-bearing artifact, replay, error handling, safety, and escalation contracts.
