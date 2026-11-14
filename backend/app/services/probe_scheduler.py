"""Probe scheduler for periodic model capability probing."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import ApiKey, Model
from app.services.model_prober import probe_model

async def run_probes(db: AsyncSession):
    # Get enabled keys
    stmt = select(ApiKey).where(ApiKey.is_enabled == True)
    result = await db.execute(stmt)
    keys = result.scalars().all()
    for key in keys:
        # Get models belonging to this key
        model_stmt = select(Model).where(Model.key_id == key.id, Model.is_enabled == True)
        model_result = await db.execute(model_stmt)
        models = model_result.scalars().all()
        for model in models:
            # Probe both chat and tool types
            await probe_model(db, model.platform, model.model_id, model.key_id, "chat")
            await probe_model(db, model.platform, model.model_id, model.key_id, "tool")
