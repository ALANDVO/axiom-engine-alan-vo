"""Model prober for probing LLM capabilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Model, ModelCapabilityProbe
from datetime import datetime, timezone

async def probe_model(db: AsyncSession, platform: str, model_id: str, key_id: int | None, probe_type: str):
    # Stub: record a probe result with a fixed label
    probe = ModelCapabilityProbe(
        platform=platform,
        model_id=model_id,
        key_id=key_id,
        probe_type=probe_type,
        label="unknown",
        success=False,
        created_at=datetime.now(timezone.utc),
    )
    db.add(probe)
    return probe
