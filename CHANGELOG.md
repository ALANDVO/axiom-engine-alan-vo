# Changelog

## 1.2.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.1.0 — 2026-11-06

### Added
- JEV-based intelligent model selection & routing (jev-routing feature)
- JEV analyzer service: classifies requests by task type (code, reasoning, analysis, creative, tool_use, chat), complexity (simple/moderate/complex), and required capabilities (tools, vision, long_context)
- Model selector service: scores candidates by platform match, capability label, task preferences, complexity requirements, tool/vision support, context window, and cost efficiency
- JEV API endpoints: POST /v1/jev/analyze for request analysis with model recommendations, GET /v1/jev/capabilities for label documentation
- Integration with chat completions: JEV routing replaces round-robin as default strategy
- Comprehensive test coverage: 34 new tests (14 for JEV analyzer, 20 for model selector)

### Changed
- Chat completions now use JEV-based model selection via `select_model_jev()`
- Request logging includes `routing_strategy="jev"`

### Fixed
- Backend database directory creation for SQLite persistence (test environment)
- All backend tests pass (41/41)
- All frontend tests pass (4/4)
- Frontend production build successful

## 1.0.0 - work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## [1.0.0] - 2025-10-21

### Added
- Initial skeleton: FastAPI backend + React/TypeScript/Vite frontend
- SQLite persistence with models, keys, requests, audit log, rate limit cooldowns, probe tables
- Basic chat completion workflow (POST /v1/chat/completions) with round-robin routing
- Model listing with capability labels (GET /v1/models)
- API key management (POST/GET/DELETE /v1/keys) with orphaned model cleanup on delete
- Health endpoints (GET /health/, GET /health/db)
- Dockerfiles (backend/frontend) + docker-compose with healthchecks
- CI workflow (backend pytest, frontend build/test)
- Basic OIDC/Keycloak auth structure (demo mode)
- Frontend chat interface with model selector
- Comprehensive test suite (backend + frontend)

### Security
- Demo mode binds to localhost only; refuses production startup without Keycloak config
- Keys stored as hashes (placeholder encryption)
- CORS restricted to localhost:5173

## [1.0.1] - 2026-10-30

### Fixed
- Backend database directory creation for SQLite persistence
- Verified end-to-end chat completion workflow: model selection, API key retrieval, request forwarding
- All backend tests pass (7/7)
- All frontend tests pass (4/4)
- Frontend production build successful
</arg_key>
<arg_key=i>
<arg_value>Update changelog with checkpoint

---

Alan Vo · [alanvo.net](https://alanvo.net)
