# Axiom Engine - Documentation

## Architecture

### Backend Structure
```
backend/app/
├── main.py                 # FastAPI app entrypoint
├── core/
│   ├── config.py          # Settings management
│   └── database.py        # SQLAlchemy async setup
├── models/
│   └── __init__.py        # SQLAlchemy models
├── api/
│   ├── health.py          # Health endpoints
│   ├── chat.py            # Chat completions
│   └── models.py          # Models & keys endpoints
└── services/              # Domain services (future phases)
```

### Frontend Structure
```
frontend/src/
├── main.tsx               # React entrypoint
├── App.tsx                # Root component
├── index.css              # Global styles
├── api/
│   └── client.ts          # Typed API client
├── components/
│   ├── Chat.tsx           # Chat interface
│   └── Chat.test.tsx      # Chat tests
├── types/
│   └── api.ts             # TypeScript types
└── hooks/                 # Custom hooks (future)
```

## Database Schema

### api_keys
Stores encrypted API keys per platform with quota and concurrency limits.

### models
Model catalog with capability labels (`tool_capable`, `chat_only`, `unavailable`, `unknown`).

### requests
Request log with failure attribution (`model`, `provider`, `network`).

### audit_log
Security audit trail.

### rate_limit_cooldowns
Per-model/key cooldowns with source tracking.

### model_capability_probes
Probe results for capability classification.

## Deployment

### Requirements
- Docker 24+
- Docker Compose 2+
- Keycloak 24+ (for production)

### Production Checklist
- [ ] Set `DEMO_MODE=false`
- [ ] Configure Keycloak realm (import `docs/keycloak-realm.json`)
- [ ] Set `KEYCLOAK_*` environment variables
- [ ] Use proper secret management for `KEYCLOAK_CLIENT_SECRET`
- [ ] Enable TLS via reverse proxy (nginx/Traefik)
- [ ] Configure backup for SQLite volume
- [ ] Set `CORS_ORIGINS` to production frontend URL

### Backup/Restore
```bash
# Backup
docker compose exec backend sqlite3 /app/data/axiom.db .dump > backup.sql

# Restore
docker compose exec -i backend sqlite3 /app/data/axiom.db < backup.sql
```