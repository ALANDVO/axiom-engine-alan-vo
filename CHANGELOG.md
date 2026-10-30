# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

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
