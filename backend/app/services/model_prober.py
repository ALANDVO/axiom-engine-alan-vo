"""Model prober for probing LLM capabilities."""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Model, ModelCapabilityProbe
from datetime import datetime, timezone


def _classify_label(supports_tools: bool, is_enabled: bool, probe_type: str) -> str:
    """Map model capabilities to a capability label."""
    if not is_enabled:
        return "unavailable"
    if probe_type == "tool" and supports_tools:
        return "tool_capable"
    if probe_type == "chat" and not supports_tools:
        return "chat_only"
    if supports_tools:
        return "tool_capable"
    return "chat_only"


async def probe_model(db: AsyncSession, platform: str, model_id: str, key_id: int | None, probe_type: str):
    # Query the model from the catalog
    stmt = select(Model).where(
        Model.platform == platform,
        Model.model_id == model_id,
        Model.key_id == key_id,
    )
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()

    if model is None:
        # Model not found in catalog; record unknown probe
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

    label = _classify_label(model.supports_tools, model.is_enabled, probe_type)

    probe = ModelCapabilityProbe(
        platform=platform,
        model_id=model_id,
        key_id=key_id,
        probe_type=probe_type,
        label=label,
        success=True,
        created_at=datetime.now(timezone.utc),
    )
    db.add(probe)
    return probe
