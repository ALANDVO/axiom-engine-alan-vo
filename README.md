# Axiom Engine — Alan Vo

> Work in progress. This checkpoint may be incomplete or fail tests. See PLAN.md and STATUS.md before use.


**Alan Vo | AI & Machine Learning**

An intelligent model routing layer aggregating 34+ free LLM providers behind a single `/v1` endpoint. Features JEV-based intelligent model selection, proactive capability probing, cross-key concurrency, and hedged requests.

## Problem

Developers using free LLM APIs face fragmented endpoints, unreliable models, and no intelligent routing. Each provider has different capabilities, context limits, token costs, and free-tier constraints. Manually selecting the best model for each task is time-consuming and error-prone.

## Solution

Axiom Engine provides:
- **Unified `/v1` endpoint** — OpenAI-compatible API aggregating 34+ free providers
- **JEV-based intelligent routing** — Task analysis dynamically selects optimal models by capability, token efficiency, and context requirements
- **Proactive model probing** — Periodic probes classify models as `tool_capable`, `chat_only`, `unavailable`, or `unknown`
- **Cross-key concurrency** — Per-key budgets stack independently; hedged racing for lower latency
- **Failure attribution** — Distinguishes provider-level throttling (429/timeout) from model-level failures (404)
- **Encrypted key storage** — Keys stored securely, never exposed to clients

## Architecture

```mermaid
graph TD
    Client[Client App] --> Gateway[/v1 Gateway]
    Gateway --> Router[Routing Engine]
    Router --> JEV[JEV Analyzer]
    Router --> Selector[Model Selector]
    Router --> Concurrency[Concurrency Manager]
    Router --> Hedged[Hedged Router]
    Selector --> ProbeDB[(Probe Results DB)]
    Concurrency --> KeyPool[Key Pool]
    Hedged --> Providers[Provider Endpoints]
    ProbeDB --> Scheduler[Probe Scheduler]
    Scheduler --> Providers
```

## Workflows

1. **Chat Completion** — Send request to `/v1/chat/completions`; routing engine selects best model
2. **Model Discovery** — Browse models with capability labels via `/v1/models`
3. **Key Management** — Add/remove API keys; automatic model cleanup on key deletion

## Installation

### Local Development

```bash
# Backend
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000

# Frontend (separate terminal)
cd frontend
npm install
npm run dev
```

### Docker

```bash
docker compose up --build
```

Access frontend at http://localhost:5173, API at http://localhost:8000/v1, docs at http://localhost:8000/docs.

## Testing

```bash
# Backend tests
cd backend
source .venv/bin/activate
PYTHONPATH=backend python -m pytest tests/ -v

# Frontend tests
cd frontend
npm test
```

## API Reference

### Chat Completions
`POST /v1/chat/completions`
- `model`: Target model (e.g., `openai/gpt-4o-mini`)
- `messages`: Array of chat messages
- `tools`: Optional tool definitions
- `stream`: Optional streaming (not yet implemented)

### Models
`GET /v1/models` — List models with filtering
`GET /v1/models/{model_id}?platform={platform}` — Get model details

### Keys
`POST /v1/keys` — Add API key
`GET /v1/keys` — List keys
`DELETE /v1/keys/{key_id}` — Delete key (cleans up orphaned models)

### Health
`GET /health/` — Basic health check
`GET /health/db` — Database connectivity check

## AI/ML Evaluation

The JEV analyzer (Phase 2) classifies tasks by:
- **Type**: chat, code, reasoning, analysis, creative
- **Complexity**: low, medium, high (token budget estimation)
- **Required capabilities**: tools, vision, long context

Model selector scores candidates on:
- Capability match (tool_capable > chat_only > unknown > unavailable)
- Token efficiency (cost per 1M tokens)
- Context window fit
- Current availability (probe freshness, cooldowns)

*Reproducible evaluation command (Phase 2):*
```bash
cd backend
source .venv/bin/activate
python -m pytest tests/test_jev_analyzer.py tests/test_model_selector.py -v
```

## Security Limitations

- Demo mode binds to localhost only; refuses to start in production without proper Keycloak config
- Keys encrypted at rest (placeholder implementation — production needs proper key management)
- No rate limiting on gateway yet (planned)
- OIDC auth structure in place; full Keycloak integration pending

## Provider Configuration

| Provider | Type | Base URL | Auth |
|----------|------|----------|------|
| OpenAI | Official | https://api.openai.com/v1 | Bearer token |
| Anthropic | Official | https://api.anthropic.com/v1 | Bearer token |
| Custom | OpenAI-compat | Configurable | Bearer token |

## SSO/SAML Setup

Keycloak realm import provided in `docs/keycloak-realm.json`. Configure identity brokering for SAML IdPs.

## License

MIT License — Copyright (c) 2025 Alan Vo <alanvo@gmail.com>