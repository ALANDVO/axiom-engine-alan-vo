from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base
from datetime import datetime
from typing import Optional


class ApiKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(100), nullable=False, index=True)
    key_hash = Column(String(255), nullable=False)  # encrypted
    key_name = Column(String(100), nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    quota_limit = Column(Integer, nullable=True)
    quota_used = Column(Integer, default=0, nullable=False)
    quota_pool = Column(String(20), default="per-key", nullable=False)  # per-key, per-account
    concurrency_limit = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    models = relationship("Model", back_populates="api_key", cascade="all, delete-orphan")


class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(100), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    display_name = Column(String(255), nullable=True)
    context_window = Column(Integer, nullable=True)
    max_output_tokens = Column(Integer, nullable=True)
    supports_tools = Column(Boolean, default=False, nullable=False)
    supports_vision = Column(Boolean, default=False, nullable=False)
    input_cost_per_million = Column(Integer, nullable=True)  # in cents
    output_cost_per_million = Column(Integer, nullable=True)
    is_enabled = Column(Boolean, default=True, nullable=False)
    source = Column(String(20), default="catalog", nullable=False)  # catalog, custom
    key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    capability_label = Column(String(20), default="unknown", nullable=False)  # tool_capable, chat_only, unavailable, unknown
    capability_updated_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    api_key = relationship("ApiKey", back_populates="models")

    __table_args__ = (
        UniqueConstraint("platform", "model_id", "key_id", name="uq_platform_model_key"),
        Index("ix_models_platform_enabled", "platform", "is_enabled"),
        Index("ix_models_capability", "capability_label"),
    )


class RequestLog(Base):
    __tablename__ = "requests"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String(64), nullable=False, unique=True, index=True)
    platform = Column(String(100), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    status = Column(String(20), nullable=False, index=True)  # success, error, canceled, rate_limited
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    routing_strategy = Column(String(30), nullable=True)
    failure_attribution = Column(String(20), nullable=True)  # model, provider, network
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_requests_platform_model_created", "platform", "model_id", "created_at"),
        Index("ix_requests_status_created", "status", "created_at"),
    )


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    resource_type = Column(String(50), nullable=True)
    resource_id = Column(String(100), nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_audit_log_user_created", "user_id", "created_at"),
        Index("ix_audit_log_action_created", "action", "created_at"),
    )


class RateLimitCooldown(Base):
    __tablename__ = "rate_limit_cooldowns"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(100), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    source = Column(String(20), default="heuristic", nullable=False)  # heuristic, probe, explicit
    reason = Column(String(100), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("platform", "model_id", "key_id", "source", name="uq_cooldown_platform_model_key_source"),
        Index("ix_cooldown_expires", "expires_at"),
    )


class ModelCapabilityProbe(Base):
    __tablename__ = "model_capability_probes"

    id = Column(Integer, primary_key=True, index=True)
    platform = Column(String(100), nullable=False, index=True)
    model_id = Column(String(255), nullable=False, index=True)
    key_id = Column(Integer, ForeignKey("api_keys.id"), nullable=True, index=True)
    probe_type = Column(String(20), nullable=False)  # chat, tool
    label = Column(String(20), nullable=False)  # tool_capable, chat_only, unavailable
    success = Column(Boolean, nullable=False)
    latency_ms = Column(Integer, nullable=True)
    error_code = Column(String(50), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)

    __table_args__ = (
        Index("ix_probe_platform_model_key", "platform", "model_id", "key_id"),
        Index("ix_probe_created", "created_at"),
    )