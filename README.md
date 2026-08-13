# interface.ai Computer-Use Automation

A focused implementation of the interface.ai take-home assignment.

The system demonstrates the central production model:

**Discovery is model-driven; replay is deterministic and model-free.**

The primary discovery run uses a locally-running LLM (Ollama, `llama3.2:3b`) to satisfy the assignment's requirement for a genuine LLM-driven discovery run — no cloud API key needed to reproduce it, but it is real model-in-the-loop discovery, not scripted automation. Evidence from that run is in `evidence/discovery-ollama.log` and `evidence/discovery-artifact-ollama.json`.

The repository also includes an offline, fully deterministic planner as a secondary demonstration that the artifact schema and replay engine don't depend on any model being available at all — useful for CI, for reviewers without Ollama installed, and as a baseline to compare against the LLM-discovered artifact. The replay layer is identical and model-free regardless of which planner produced the artifact.

The repository uses a local synthetic banking application so no real credentials or financial data are needed.

## Architecture

```text
Natural-language goal
        |
        v
Discovery Agent
  - Local Ollama LLM planner (primary — genuine model-driven discovery)
  - Offline deterministic planner (secondary — no model dependency)
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

To reproduce the primary (LLM-driven) discovery run: [Ollama](https://ollama.com) installed locally, with the model pulled (`ollama pull llama3.2:3b`) and `ollama serve` running.

The offline planner and all replay commands require no model at all.

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

## Start Ollama

Terminal 2:

```bash
ollama serve
```

Make sure the model is pulled first: `ollama pull llama3.2:3b`

## End-to-end demonstration (LLM-driven discovery)

The primary demonstration below uses `--planner ollama`, since that's the genuine LLM-driven discovery run the assignment requires. An equivalent offline-planner walkthrough follows in "Offline / model-free discovery" for reference.

Terminal 3:

```bash
source .venv/bin/activate
export PYTHONPATH=src
```

Discover the capability:

```bash
python -m cua.cli discover \
  --url http://127.0.0.1:8000 \
  --goal "Look up member 12345 and read their current savings balance" \
  --planner ollama \
  --output evidence/discovery-artifact-ollama.json \
  --log evidence/discovery-ollama.log
```

Replay it deterministically:

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact-ollama.json \
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
  --artifact evidence/discovery-artifact-ollama.json \
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
  --artifact evidence/discovery-artifact-ollama.json \
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
  --artifact evidence/discovery-artifact-ollama.json \
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

The replay process keeps the browser headed during escalation so the live browser state remains available for operator handoff. The current demo records the intervention state to the filesystem but does not persist a reconnectable session identifier or implement operator resume. A production handoff layer would associate the intervention with the live browser session and expose explicit claim, takeover, correction, and resume operations.

## Offline / model-free discovery

The offline planner produces the same artifact/replay contract without calling any model — useful to show the pipeline doesn't have a hard LLM dependency, and as a fallback if Ollama isn't installed.

```bash
python -m cua.cli discover \
  --url http://127.0.0.1:8000 \
  --goal "Look up member 12345 and read their current savings balance" \
  --planner offline \
  --output evidence/discovery-artifact.json \
  --log evidence/discovery.log
```

Replay works identically against this artifact:

```bash
python -m cua.cli replay \
  --artifact evidence/discovery-artifact.json \
  --url http://127.0.0.1:8000 \
  --member-id 12345 \
  --log evidence/replay-success.log
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
- The Ollama planner is stateless per turn; it relies on explicit action-history and current-input-value feedback injected into each prompt (rather than true conversational memory) to avoid repeating actions. This works for a short flow but is a known constraint, not a full agent memory system.

These cuts keep the implementation focused on the load-bearing artifact, replay, error handling, safety, and escalation contracts.