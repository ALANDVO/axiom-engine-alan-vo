from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import Model, RequestLog, ApiKey
from datetime import datetime, timezone
import uuid
import time
import httpx
import json

router = APIRouter()


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: Optional[str] = None
    tool_calls: Optional[List[dict]] = None
    tool_call_id: Optional[str] = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    temperature: Optional[float] = 1.0
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False
    tools: Optional[List[dict]] = None
    tool_choice: Optional[Literal["auto", "none", "required"]] = "auto"


class ChatCompletionChoice(BaseModel):
    index: int
    message: ChatMessage
    finish_reason: str


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage


async def select_model_round_robin(db: AsyncSession, requested_model: str, requires_tools: bool) -> Model | None:
    """Simple round-robin selection from enabled models matching the request."""
    stmt = select(Model).where(
        Model.is_enabled == True,
        Model.platform == requested_model.split("/")[0] if "/" in requested_model else requested_model
    )
    if requires_tools:
        stmt = stmt.where(Model.supports_tools == True)
    stmt = stmt.order_by(Model.id)
    result = await db.execute(stmt)
    return result.scalars().first()


async def select_model_jev(db: AsyncSession, requested_model: str, requires_tools: bool, messages: list) -> Model | None:
    """JEV-based intelligent selection (placeholder - Phase 2)."""
    return await select_model_round_robin(db, requested_model, requires_tools)


async def forward_to_provider(model: Model, payload: dict, api_key: str, base_url: str) -> dict:
    """Forward request to upstream provider."""
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    url = f"{base_url.rstrip('/')}/chat/completions"
    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(url, json=payload, headers=headers)
        response.raise_for_status()
        return response.json()


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def chat_completions(
    request: ChatCompletionRequest,
    http_request: Request,
    db: AsyncSession = Depends(get_db),
):
    start_time = time.time()
    request_id = f"req_{uuid.uuid4().hex[:16]}"
    requires_tools = bool(request.tools)

    # Resolve model
    model = await select_model_round_robin(db, request.model, requires_tools)
    if not model:
        raise HTTPException(status_code=404, detail=f"No enabled model found for {request.model}")

    # Get API key
    api_key_stmt = select(ApiKey).where(ApiKey.id == model.key_id, ApiKey.is_enabled == True)
    api_key_result = await db.execute(api_key_stmt)
    api_key_obj = api_key_result.scalar_one_or_none()
    if not api_key_obj:
        raise HTTPException(status_code=503, detail="No available API key for model")

    # Decrypt key (placeholder - in production use proper encryption)
    decrypted_key = api_key_obj.key_hash  # TODO: decrypt

    # Prepare upstream payload
    upstream_payload = request.model_dump(exclude_none=True)
    upstream_payload["model"] = model.model_id

    # Forward to provider
    try:
        # Use model's platform base URL (simplified)
        base_url = f"https://api.{model.platform}.com/v1"  # TODO: configurable per platform
        upstream_response = await forward_to_provider(model, upstream_payload, decrypted_key, base_url)

        latency_ms = int((time.time() - start_time) * 1000)

        # Log success
        log_entry = RequestLog(
            request_id=request_id,
            platform=model.platform,
            model_id=model.model_id,
            key_id=model.key_id,
            status="success",
            latency_ms=latency_ms,
            input_tokens=upstream_response.get("usage", {}).get("prompt_tokens"),
            output_tokens=upstream_response.get("usage", {}).get("completion_tokens"),
            total_tokens=upstream_response.get("usage", {}).get("total_tokens"),
            routing_strategy="round_robin",
        )
        db.add(log_entry)
        await db.commit()

        return ChatCompletionResponse(
            id=upstream_response.get("id", request_id),
            created=int(time.time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    index=0,
                    message=ChatMessage(**choice["message"]),
                    finish_reason=choice.get("finish_reason", "stop"),
                )
                for choice in upstream_response.get("choices", [])
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=upstream_response.get("usage", {}).get("prompt_tokens", 0),
                completion_tokens=upstream_response.get("usage", {}).get("completion_tokens", 0),
                total_tokens=upstream_response.get("usage", {}).get("total_tokens", 0),
            ),
        )
    except httpx.HTTPStatusError as e:
        latency_ms = int((time.time() - start_time) * 1000)
        error_detail = e.response.text
        status = "rate_limited" if e.response.status_code == 429 else "error"

        log_entry = RequestLog(
            request_id=request_id,
            platform=model.platform,
            model_id=model.model_id,
            key_id=model.key_id,
            status=status,
            error_code=str(e.response.status_code),
            error_message=error_detail,
            latency_ms=latency_ms,
            routing_strategy="round_robin",
            failure_attribution="provider" if e.response.status_code in (429, 502, 503, 504) else "model",
        )
        db.add(log_entry)
        await db.commit()

        raise HTTPException(status_code=e.response.status_code, detail=error_detail)
    except Exception as e:
        latency_ms = int((time.time() - start_time) * 1000)
        log_entry = RequestLog(
            request_id=request_id,
            platform=model.platform,
            model_id=model.model_id,
            key_id=model.key_id,
            status="error",
            error_message=str(e),
            latency_ms=latency_ms,
            routing_strategy="round_robin",
            failure_attribution="network",
        )
        db.add(log_entry)
        await db.commit()
        raise HTTPException(status_code=500, detail=str(e))