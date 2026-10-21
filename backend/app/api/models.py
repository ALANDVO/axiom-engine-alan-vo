from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.core.database import get_db
from app.models import Model, ApiKey, ModelCapabilityProbe
from datetime import datetime, timezone

router = APIRouter()


class ModelResponse(BaseModel):
    id: int
    platform: str
    model_id: str
    display_name: Optional[str]
    context_window: Optional[int]
    max_output_tokens: Optional[int]
    supports_tools: bool
    supports_vision: bool
    input_cost_per_million: Optional[int]
    output_cost_per_million: Optional[int]
    is_enabled: bool
    source: str
    capability_label: str
    capability_updated_at: Optional[datetime]


class ModelListResponse(BaseModel):
    models: List[ModelResponse]
    total: int
    page: int
    page_size: int


class ApiKeyCreate(BaseModel):
    platform: str
    key_hash: str
    key_name: Optional[str] = None
    quota_limit: Optional[int] = None
    quota_pool: str = "per-key"
    concurrency_limit: Optional[int] = None


class ApiKeyResponse(BaseModel):
    id: int
    platform: str
    key_name: Optional[str]
    is_enabled: bool
    quota_limit: Optional[int]
    quota_used: int
    quota_pool: str
    concurrency_limit: Optional[int]
    created_at: datetime


@router.get("/models", response_model=ModelListResponse)
async def list_models(
    platform: Optional[str] = None,
    capability: Optional[str] = None,
    enabled_only: bool = True,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(Model)
    if enabled_only:
        stmt = stmt.where(Model.is_enabled == True)
    if platform:
        stmt = stmt.where(Model.platform == platform)
    if capability:
        stmt = stmt.where(Model.capability_label == capability)

    # Count total
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total_result = await db.execute(count_stmt)
    total = total_result.scalar()

    # Paginate
    stmt = stmt.order_by(Model.platform, Model.model_id).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(stmt)
    models = result.scalars().all()

    return ModelListResponse(
        models=[
            ModelResponse(
                id=m.id,
                platform=m.platform,
                model_id=m.model_id,
                display_name=m.display_name,
                context_window=m.context_window,
                max_output_tokens=m.max_output_tokens,
                supports_tools=m.supports_tools,
                supports_vision=m.supports_vision,
                input_cost_per_million=m.input_cost_per_million,
                output_cost_per_million=m.output_cost_per_million,
                is_enabled=m.is_enabled,
                source=m.source,
                capability_label=m.capability_label,
                capability_updated_at=m.capability_updated_at,
            )
            for m in models
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.get("/models/{model_id}", response_model=ModelResponse)
async def get_model(model_id: str, platform: str, db: AsyncSession = Depends(get_db)):
    stmt = select(Model).where(Model.platform == platform, Model.model_id == model_id)
    result = await db.execute(stmt)
    model = result.scalar_one_or_none()
    if not model:
        raise HTTPException(status_code=404, detail="Model not found")
    return ModelResponse(
        id=model.id,
        platform=model.platform,
        model_id=model.model_id,
        display_name=model.display_name,
        context_window=model.context_window,
        max_output_tokens=model.max_output_tokens,
        supports_tools=model.supports_tools,
        supports_vision=model.supports_vision,
        input_cost_per_million=model.input_cost_per_million,
        output_cost_per_million=model.output_cost_per_million,
        is_enabled=model.is_enabled,
        source=model.source,
        capability_label=model.capability_label,
        capability_updated_at=model.capability_updated_at,
    )


@router.post("/keys", response_model=ApiKeyResponse, status_code=201)
async def create_key(key: ApiKeyCreate, db: AsyncSession = Depends(get_db)):
    api_key = ApiKey(**key.model_dump())
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)
    return ApiKeyResponse(
        id=api_key.id,
        platform=api_key.platform,
        key_name=api_key.key_name,
        is_enabled=api_key.is_enabled,
        quota_limit=api_key.quota_limit,
        quota_used=api_key.quota_used,
        quota_pool=api_key.quota_pool,
        concurrency_limit=api_key.concurrency_limit,
        created_at=api_key.created_at,
    )


@router.get("/keys", response_model=List[ApiKeyResponse])
async def list_keys(platform: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    stmt = select(ApiKey).where(ApiKey.is_enabled == True)
    if platform:
        stmt = stmt.where(ApiKey.platform == platform)
    result = await db.execute(stmt)
    keys = result.scalars().all()
    return [
        ApiKeyResponse(
            id=k.id,
            platform=k.platform,
            key_name=k.key_name,
            is_enabled=k.is_enabled,
            quota_limit=k.quota_limit,
            quota_used=k.quota_used,
            quota_pool=k.quota_pool,
            concurrency_limit=k.concurrency_limit,
            created_at=k.created_at,
        )
        for k in keys
    ]


@router.delete("/keys/{key_id}")
async def delete_key(key_id: int, db: AsyncSession = Depends(get_db)):
    stmt = select(ApiKey).where(ApiKey.id == key_id)
    result = await db.execute(stmt)
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=404, detail="Key not found")

    # Phase 5: disable models that only belong to this key
    model_stmt = select(Model).where(Model.key_id == key_id)
    model_result = await db.execute(model_stmt)
    models = model_result.scalars().all()
    for model in models:
        # Check if model has other keys
        other_keys_stmt = select(ApiKey).where(
            ApiKey.platform == model.platform,
            ApiKey.id != key_id,
            ApiKey.is_enabled == True,
        )
        other_keys_result = await db.execute(other_keys_stmt)
        if not other_keys_result.scalar_one_or_none():
            model.is_enabled = False

    await db.delete(api_key)
    await db.commit()
    return {"status": "deleted"}