# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

skeleton

## Roadmap

### skeleton — FastAPI/React skeleton with one working workflow

Status: done

Acceptance:
- Backend starts and serves health endpoint
- Frontend builds and loads
- One end-to-end chat completion workflow works

Implementation: `backend/app/main.py`, `backend/app/api/chat.py`, `backend/app/api/models.py`, `backend/app/api/health.py`, `backend/app/core/config.py`, `backend/app/core/database.py`, `backend/app/models/__init__.py`, `frontend/src/App.tsx`, `frontend/src/components/Chat.tsx`, `frontend/src/api/client.ts`, `frontend/src/types/api.ts`

Tests: `backend/tests/test_health.py`, `frontend/src/components/Chat.test.tsx`

### jev-routing — JEV-based intelligent model selection & routing

Status: planned

Acceptance:
- Task analysis endpoint classifies request type/complexity
- Model selector picks best model based on capabilities
- Routing integrates with existing fallback chain

Implementation: `backend/app/services/jev_analyzer.py`, `backend/app/services/model_selector.py`, `backend/app/api/jev.py`

Tests: `backend/tests/test_jev_analyzer.py`, `backend/tests/test_model_selector.py`

### model-probing — Proactive per-model probing with capability labels

Status: planned

Acceptance:
- Scheduler runs periodic probes per (platform, model, key)
- Labels: tool_capable, chat_only, unavailable, unknown
- Labels exposed via API and dashboard

Implementation: `backend/app/services/probe_scheduler.py`, `backend/app/services/model_prober.py`, `backend/app/api/models.py`

Tests: `backend/tests/test_probe_scheduler.py`, `backend/tests/test_model_prober.py`

### cross-key-concurrency — Cross-key concurrency and hedged requests

Status: planned

Acceptance:
- Per-key concurrency budgets stack independently
- Optional hedged racing with hedge_after_ms
- Failure attribution: 429/timeout -> provider, 404 -> model

Implementation: `backend/app/services/concurrency_manager.py`, `backend/app/services/hedged_router.py`, `backend/app/services/failure_classifier.py`

Tests: `backend/tests/test_concurrency_manager.py`, `backend/tests/test_hedged_router.py`, `backend/tests/test_failure_classifier.py`

### key-deletion-cleanup — Key deletion cleans up orphaned models

Status: planned

Acceptance:
- Deleting a key disables its exclusive models
- Catalog prune sweeps models pointing to deleted keys
- Dashboard reflects cleanup immediately

Implementation: `backend/app/services/key_lifecycle.py`, `backend/app/api/keys.py`

Tests: `backend/tests/test_key_lifecycle.py`

