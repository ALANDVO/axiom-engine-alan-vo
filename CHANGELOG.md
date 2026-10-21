# Changelog

## 1.0.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

All notable changes to this project will be documented in this file.

## [1.0.0] - 2025-10-21

### Added
- Initial skeleton: FastAPI backend + React/TypeScript/Vite frontend
- SQLite persistence with models, keys, requests, audit log, rate limit cooldowns, probe tables
- Basic chat completion workflow (`POST /v1/chat/completions`) with round-robin routing
- Model listing with capability labels (`GET /v1/models`)
- API key management (`POST/GET/DELETE /v1/keys`) with orphaned model cleanup on delete
- Health endpoints (`GET /health/`, `GET /health/db`)
- Dockerfiles (backend/frontend) + docker-compose with healthchecks
- CI workflow (backend pytest, frontend build/test)
- Basic OIDC/Keycloak auth structure (demo mode)
- Frontend chat interface with model selector
- Comprehensive test suite (backend + frontend)

### Security
- Demo mode binds to localhost only; refuses production startup without Keycloak config
- Keys stored as hashes (placeholder encryption)
- CORS restricted to localhost:5173