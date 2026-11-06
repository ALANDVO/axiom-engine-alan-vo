"""Model selector using JEV analysis for intelligent routing."""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Model
from app.services.jev_analyzer import TaskAnalysis, analyze_request


# Model capability scoring weights
CAPABILITY_WEIGHTS = {
    "tool_capable": 10,
    "chat_only": 5,
    "unknown": 2,
    "unavailable": 0,
}

# Task type to model preference mapping
TASK_MODEL_PREFERENCES = {
    "code": ["tool_capable"],
    "reasoning": ["tool_capable", "chat_only"],
    "analysis": ["tool_capable", "chat_only"],
    "creative": ["chat_only", "tool_capable"],
    "tool_use": ["tool_capable"],
    "chat": ["chat_only", "tool_capable"],
}

# Complexity to minimum capability mapping
COMPLEXITY_MIN_CAPABILITY = {
    "simple": "chat_only",
    "moderate": "tool_capable",
    "complex": "tool_capable",
}


def score_model(model: Model, analysis: TaskAnalysis, requested_platform: str) -> float:
    """Score a model based on JEV analysis and request requirements."""
    score = 0.0
    
    # Platform match (strong signal)
    if model.platform == requested_platform:
        score += 50
    elif requested_platform == "auto":
        score += 25
    
    # Capability label scoring
    capability_score = CAPABILITY_WEIGHTS.get(model.capability_label, 0)
    score += capability_score
    
    # Task type preference
    preferred_labels = TASK_MODEL_PREFERENCES.get(analysis.task_type, [])
    if model.capability_label in preferred_labels:
        score += 20 * (preferred_labels.index(model.capability_label) + 1)
    
    # Complexity requirement
    min_capability = COMPLEXITY_MIN_CAPABILITY.get(analysis.complexity, "chat_only")
    capability_order = ["unavailable", "unknown", "chat_only", "tool_capable"]
    model_cap_idx = capability_order.index(model.capability_label)
    min_cap_idx = capability_order.index(min_capability)
    
    if model_cap_idx >= min_cap_idx:
        score += 15
    else:
        score -= 30  # Penalty for insufficient capability
    
    # Tool support requirement
    if analysis.requires_tools and model.supports_tools:
        score += 25
    elif analysis.requires_tools and not model.supports_tools:
        score -= 50
    
    # Vision support
    if analysis.requires_vision and model.supports_vision:
        score += 15
    elif analysis.requires_vision and not model.supports_vision:
        score -= 20
    
    # Context window for long context
    if analysis.requires_long_context and model.context_window:
        if model.context_window >= 32000:
            score += 15
        elif model.context_window >= 16000:
            score += 10
        elif model.context_window >= 8000:
            score += 5
    
    # Cost efficiency (lower cost = higher score for simple tasks)
    if analysis.complexity == "simple" and model.input_cost_per_million:
        if model.input_cost_per_million < 50:  # < $0.50/M tokens
            score += 10
        elif model.input_cost_per_million < 200:  # < $2.00/M tokens
            score += 5
    
    # Prefer enabled models
    if not model.is_enabled:
        score -= 1000
    
    return score


async def select_best_model(
    db: AsyncSession,
    requested_model: str,
    analysis: TaskAnalysis,
    requires_tools: bool
) -> Optional[Model]:
    """Select the best model based on JEV analysis."""
    # Parse requested platform
    requested_platform = requested_model.split("/")[0] if "/" in requested_model else requested_model
    if requested_platform == "auto":
        requested_platform = "auto"
    
    # Build base query
    stmt = select(Model).where(Model.is_enabled == True)
    
    # Filter by platform if specified
    if requested_platform != "auto":
        stmt = stmt.where(Model.platform == requested_platform)
    
    # Filter by tool support if required
    if requires_tools or analysis.requires_tools:
        stmt = stmt.where(Model.supports_tools == True)
    
    # Filter by vision if required
    if analysis.requires_vision:
        stmt = stmt.where(Model.supports_vision == True)
    
    # Filter by context window for long context
    if analysis.requires_long_context:
        stmt = stmt.where(Model.context_window >= 16000)
    
    result = await db.execute(stmt)
    candidates = result.scalars().all()
    
    if not candidates:
        return None
    
    # Score all candidates
    scored = [(model, score_model(model, analysis, requested_platform)) for model in candidates]
    
    # Sort by score descending
    scored.sort(key=lambda x: x[1], reverse=True)
    
    return scored[0][0]


async def select_model_jev(
    db: AsyncSession,
    requested_model: str,
    requires_tools: bool,
    messages: List[dict]
) -> Optional[Model]:
    """JEV-based intelligent model selection (main entry point)."""
    from app.services.jev_analyzer import analyze_request
    
    # Analyze the request
    analysis = await analyze_request(messages)
    
    # Select best model
    return await select_best_model(db, requested_model, analysis, requires_tools)
