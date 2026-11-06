"""Tests for model selector service."""

import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession
from app.services.model_selector import score_model, select_best_model, select_model_jev
from app.services.jev_analyzer import TaskAnalysis
from app.models import Model


class TestScoreModel:
    def test_platform_match_bonus(self):
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = False
        model.context_window = 128000
        model.input_cost_per_million = 100
        model.is_enabled = True
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="moderate",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score = score_model(model, analysis, "openai")
        # Should get platform match bonus (50) + capability (10) + task pref (20) + tool support (25)
        assert score > 100

    def test_platform_mismatch_penalty(self):
        model = MagicMock(spec=Model)
        model.platform = "anthropic"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = False
        model.context_window = 128000
        model.input_cost_per_million = 100
        model.is_enabled = True
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="moderate",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score = score_model(model, analysis, "openai")
        # No platform match bonus
        assert score < 100

    def test_disabled_model_penalty(self):
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = True
        model.context_window = 128000
        model.input_cost_per_million = 100
        model.is_enabled = False
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="moderate",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score = score_model(model, analysis, "openai")
        # Heavy penalty for disabled
        assert score < -500

    def test_insufficient_capability_penalty(self):
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.capability_label = "chat_only"
        model.supports_tools = False
        model.supports_vision = False
        model.context_window = 4096
        model.input_cost_per_million = 100
        model.is_enabled = True
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="complex",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score = score_model(model, analysis, "openai")
        # Penalty for no tool support when required
        assert score < 0

    def test_vision_support_bonus(self):
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = True
        model.context_window = 128000
        model.input_cost_per_million = 100
        model.is_enabled = True
        
        analysis = TaskAnalysis(
            task_type="analysis",
            complexity="moderate",
            requires_tools=False,
            requires_vision=True,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score_with_vision = score_model(model, analysis, "openai")
        
        model.supports_vision = False
        score_without_vision = score_model(model, analysis, "openai")
        
        assert score_with_vision > score_without_vision

    def test_long_context_bonus(self):
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = False
        model.context_window = 128000
        model.input_cost_per_million = 100
        model.is_enabled = True
        
        analysis = TaskAnalysis(
            task_type="analysis",
            complexity="moderate",
            requires_tools=False,
            requires_vision=False,
            requires_long_context=True,
            estimated_tokens=100,
            confidence=0.8
        )
        
        score_large_context = score_model(model, analysis, "openai")
        
        model.context_window = 4096
        score_small_context = score_model(model, analysis, "openai")
        
        assert score_large_context > score_small_context


class TestSelectBestModel:
    @pytest.mark.asyncio
    async def test_selects_highest_scored(self):
        db = AsyncMock(spec=AsyncSession)
        
        # Create mock models
        model1 = MagicMock(spec=Model)
        model1.platform = "openai"
        model1.model_id = "gpt-4o-mini"
        model1.capability_label = "chat_only"
        model1.supports_tools = False
        model1.supports_vision = False
        model1.context_window = 128000
        model1.input_cost_per_million = 15
        model1.is_enabled = True
        
        model2 = MagicMock(spec=Model)
        model2.platform = "openai"
        model2.model_id = "gpt-4o"
        model2.capability_label = "tool_capable"
        model2.supports_tools = True
        model2.supports_vision = True
        model2.context_window = 128000
        model2.input_cost_per_million = 500
        model2.is_enabled = True
        
        # Mock the execute result
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model1, model2]
        db.execute.return_value = mock_result
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="moderate",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        selected = await select_best_model(db, "openai/gpt-4o", analysis, True)
        
        # Should select gpt-4o because it supports tools
        assert selected.model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_returns_none_when_no_candidates(self):
        db = AsyncMock(spec=AsyncSession)
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        db.execute.return_value = mock_result
        
        analysis = TaskAnalysis(
            task_type="chat",
            complexity="simple",
            requires_tools=False,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        selected = await select_best_model(db, "openai/gpt-4o", analysis, False)
        assert selected is None

    @pytest.mark.asyncio
    async def test_filters_by_platform(self):
        db = AsyncMock(spec=AsyncSession)
        
        # Model that matches the requested platform
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.model_id = "gpt-4o"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = True
        model.context_window = 128000
        model.input_cost_per_million = 500
        model.is_enabled = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        db.execute.return_value = mock_result
        
        analysis = TaskAnalysis(
            task_type="chat",
            complexity="simple",
            requires_tools=False,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        # Request openai platform, model matches
        selected = await select_best_model(db, "openai/gpt-4o", analysis, False)
        assert selected is not None
        assert selected.model_id == "gpt-4o"

    @pytest.mark.asyncio
    async def test_filters_by_tool_requirement(self):
        db = AsyncMock(spec=AsyncSession)
        
        # Model that supports tools
        model_with_tools = MagicMock(spec=Model)
        model_with_tools.platform = "openai"
        model_with_tools.model_id = "gpt-4o"
        model_with_tools.capability_label = "tool_capable"
        model_with_tools.supports_tools = True
        model_with_tools.supports_vision = True
        model_with_tools.context_window = 128000
        model_with_tools.input_cost_per_million = 500
        model_with_tools.is_enabled = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model_with_tools]
        db.execute.return_value = mock_result
        
        analysis = TaskAnalysis(
            task_type="code",
            complexity="moderate",
            requires_tools=True,
            requires_vision=False,
            requires_long_context=False,
            estimated_tokens=100,
            confidence=0.8
        )
        
        selected = await select_best_model(db, "openai/gpt-4o", analysis, True)
        assert selected is not None
        assert selected.model_id == "gpt-4o"
        assert selected.supports_tools is True


class TestSelectModelJEV:
    @pytest.mark.asyncio
    async def test_integration(self):
        db = AsyncMock(spec=AsyncSession)
        
        model = MagicMock(spec=Model)
        model.platform = "openai"
        model.model_id = "gpt-4o"
        model.capability_label = "tool_capable"
        model.supports_tools = True
        model.supports_vision = True
        model.context_window = 128000
        model.input_cost_per_million = 500
        model.is_enabled = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [model]
        db.execute.return_value = mock_result
        
        messages = [{"role": "user", "content": "Write a Python function"}]
        
        selected = await select_model_jev(db, "openai/gpt-4o", False, messages)
        
        assert selected is not None
        assert selected.model_id == "gpt-4o"

