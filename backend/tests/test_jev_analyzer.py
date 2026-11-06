"""Tests for JEV analyzer service."""

import pytest
from app.services.jev_analyzer import (
    analyze_request,
    classify_task_type,
    classify_complexity,
    detect_capabilities,
    estimate_tokens,
    TaskAnalysis,
)


class TestEstimateTokens:
    def test_empty_string(self):
        assert estimate_tokens("") == 0

    def test_short_string(self):
        assert estimate_tokens("hello") == 1  # 5 chars // 4 = 1

    def test_longer_string(self):
        assert estimate_tokens("hello world") == 2  # 11 chars // 4 = 2


class TestClassifyTaskType:
    def test_code_task(self):
        messages = [{"role": "user", "content": "Write a Python function to sort a list"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "code"
        assert confidence > 0.5

    def test_reasoning_task(self):
        messages = [{"role": "user", "content": "Think through this logic step by step"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "reasoning"
        assert confidence > 0.5

    def test_analysis_task(self):
        messages = [{"role": "user", "content": "Analyze this data and find patterns"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "analysis"
        assert confidence > 0.5

    def test_creative_task(self):
        messages = [{"role": "user", "content": "Write a creative story about a robot"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "creative"
        assert confidence > 0.5

    def test_tool_use_task(self):
        messages = [{"role": "user", "content": "Search for the latest weather forecast"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "tool_use"
        assert confidence > 0.5

    def test_chat_default(self):
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "chat"

    def test_empty_messages(self):
        messages = []
        task_type, confidence = classify_task_type(messages)
        assert task_type == "chat"

    def test_system_message_only(self):
        messages = [{"role": "system", "content": "You are a helpful assistant"}]
        task_type, confidence = classify_task_type(messages)
        assert task_type == "chat"


class TestClassifyComplexity:
    def test_complex_task(self):
        messages = [{"role": "user", "content": "Design a distributed microservice architecture"}]
        complexity, confidence = classify_complexity(messages)
        assert complexity == "complex"
        assert confidence > 0.7

    def test_moderate_task(self):
        messages = [{"role": "user", "content": "Implement a user authentication system"}]
        complexity, confidence = classify_complexity(messages)
        assert complexity == "moderate"
        assert confidence > 0.6

    def test_simple_task(self):
        messages = [{"role": "user", "content": "What is 2+2?"}]
        complexity, confidence = classify_complexity(messages)
        assert complexity == "simple"
        assert confidence > 0.5

    def test_long_conversation_moderate(self):
        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi"},
            {"role": "user", "content": "How are you?"},
            {"role": "assistant", "content": "Good"},
            {"role": "user", "content": "Tell me a joke"},
            {"role": "assistant", "content": "Here's one"},
            {"role": "user", "content": "Another one please"},
        ]
        complexity, confidence = classify_complexity(messages)
        assert complexity == "moderate"


class TestDetectCapabilities:
    def test_requires_tools(self):
        messages = [{"role": "user", "content": "Search for current stock prices"}]
        tools, vision, long_ctx = detect_capabilities(messages)
        assert tools is True
        assert vision is False
        assert long_ctx is False

    def test_requires_vision(self):
        messages = [{"role": "user", "content": "Analyze this image for me"}]
        tools, vision, long_ctx = detect_capabilities(messages)
        assert tools is False
        assert vision is True
        assert long_ctx is False

    def test_requires_long_context(self):
        messages = [{"role": "user", "content": "Summarize this entire document"}]
        tools, vision, long_ctx = detect_capabilities(messages)
        assert tools is False
        assert vision is False
        assert long_ctx is True

    def test_no_special_capabilities(self):
        messages = [{"role": "user", "content": "Hello, how are you?"}]
        tools, vision, long_ctx = detect_capabilities(messages)
        assert tools is False
        assert vision is False
        assert long_ctx is False


class TestAnalyzeRequest:
    @pytest.mark.asyncio
    async def test_code_task_analysis(self):
        messages = [{"role": "user", "content": "Write a Python function to parse JSON"}]
        analysis = await analyze_request(messages)
        
        assert isinstance(analysis, TaskAnalysis)
        assert analysis.task_type == "code"
        assert analysis.complexity in ["simple", "moderate"]
        assert analysis.requires_tools is False
        assert analysis.confidence > 0.3

    @pytest.mark.asyncio
    async def test_tool_use_with_tools(self):
        messages = [{"role": "user", "content": "Get the current weather"}]
        tools = [{"type": "function", "function": {"name": "get_weather"}}]
        analysis = await analyze_request(messages, tools)
        
        assert analysis.requires_tools is True

    @pytest.mark.asyncio
    async def test_reasoning_complex(self):
        messages = [{"role": "user", "content": "Design a complex system architecture with distributed reasoning"}]
        analysis = await analyze_request(messages)
        
        assert analysis.task_type == "reasoning"
        assert analysis.complexity == "complex"

    @pytest.mark.asyncio
    async def test_estimated_tokens(self):
        messages = [{"role": "user", "content": "This is a test message with several words"}]
        analysis = await analyze_request(messages)
        
        assert analysis.estimated_tokens > 0

