"""JEV (Job Evaluation Vector) API endpoints for request analysis."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.models import Model
from app.services.jev_analyzer import TaskAnalysis, analyze_request
from app.services.model_selector import select_best_model

router = APIRouter(prefix="/jev", tags=["jev"])


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None


class JEVAnalyzeRequest(BaseModel):
    messages: List[ChatMessage]
    tools: Optional[List[dict]] = None
    model: str = "auto"


class JEVAnalyzeResponse(BaseModel):
    analysis: TaskAnalysis
    recommended_model: Optional[str] = None
    candidate_models: List[str] = []


@router.post("/analyze", response_model=JEVAnalyzeResponse)
async def analyze_request_endpoint(
    request: JEVAnalyzeRequest,
    db: AsyncSession = Depends(get_db),
):
    """Analyze a chat request and return JEV classification with model recommendations."""
    # Convert messages to dict format for analyzer
    messages = [msg.model_dump(exclude_none=True) for msg in request.messages]
    
    # Perform JEV analysis
    analysis = await analyze_request(messages, request.tools)
    
    # Get model recommendations
    recommended_model = None
    candidate_models = []
    
    if analysis.confidence > 0.3:
        model = await select_best_model(db, request.model, analysis, bool(request.tools))
        if model:
            recommended_model = f"{model.platform}/{model.model_id}"
        
        # Get top 3 candidates for display
        from app.services.model_selector import score_model
        requested_platform = request.model.split("/")[0] if "/" in request.model else request.model
        stmt = select(Model).where(Model.is_enabled == True)
        if requested_platform != "auto":
            stmt = stmt.where(Model.platform == requested_platform)
        if analysis.requires_tools or request.tools:
            stmt = stmt.where(Model.supports_tools == True)
        if analysis.requires_vision:
            stmt = stmt.where(Model.supports_vision == True)
        if analysis.requires_long_context:
            stmt = stmt.where(Model.context_window >= 16000)
        
        result = await db.execute(stmt)
        candidates = result.scalars().all()
        
        scored = [(m, score_model(m, analysis, requested_platform)) for m in candidates]
        scored.sort(key=lambda x: x[1], reverse=True)
        candidate_models = [f"{m.platform}/{m.model_id}" for m, _ in scored[:3]]
    
    return JEVAnalyzeResponse(
        analysis=analysis,
        recommended_model=recommended_model,
        candidate_models=candidate_models
    )


@router.get("/capabilities")
async def get_capability_labels(
    db: AsyncSession = Depends(get_db),
):
    """Get all capability labels and their descriptions."""
    return {
        "labels": {
            "tool_capable": "Model supports function/tool calling",
            "chat_only": "Model supports chat but not tool calling",
            "unavailable": "Model is currently unavailable",
            "unknown": "Model capability not yet determined",
        },
        "task_types": {
            "chat": "General conversation",
            "code": "Programming and software development",
            "reasoning": "Logical reasoning and problem solving",
            "analysis": "Data analysis and review",
            "creative": "Creative writing and content generation",
            "tool_use": "Tasks requiring external tool access",
        },
        "complexity_levels": {
            "simple": "Straightforward, single-step requests",
            "moderate": "Multi-step or moderately complex requests",
            "complex": "Complex, multi-faceted requests requiring deep reasoning",
        }
    }
