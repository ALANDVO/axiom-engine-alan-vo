"""JEV (Job Evaluation Vector) analyzer for request classification.

Analyzes incoming chat requests to determine:
- Task type: chat, code, reasoning, analysis, creative, tool_use
- Complexity: simple, moderate, complex
- Required capabilities: tools, vision, long_context
"""

from typing import List, Literal
from pydantic import BaseModel
import re


class TaskAnalysis(BaseModel):
    """Result of JEV analysis on a request."""
    task_type: Literal["chat", "code", "reasoning", "analysis", "creative", "tool_use"]
    complexity: Literal["simple", "moderate", "complex"]
    requires_tools: bool
    requires_vision: bool
    requires_long_context: bool
    estimated_tokens: int
    confidence: float


# Keywords for task type classification
TASK_KEYWORDS = {
    "code": [
        "code", "program", "function", "class", "debug", "implement", "refactor",
        "algorithm", "script", "api", "endpoint", "database", "sql", "query",
        "javascript", "python", "typescript", "rust", "go", "java", "c++", "react",
        "component", "hook", "async", "await", "promise", "callback", "regex"
    ],
    "reasoning": [
        "reason", "reasoning", "logic", "deduce", "infer", "solve", "proof", "theorem",
        "step by step", "think through", "evaluate", "compare",
        "pros and cons", "tradeoff", "decision", "strategy", "plan"
    ],
    "analysis": [
        "analyze", "review", "examine", "investigate", "audit", "assess",
        "summarize", "extract", "identify", "pattern", "trend", "insight",
        "report", "metrics", "data", "statistics", "performance"
    ],
    "creative": [
        "write", "create", "compose", "story", "poem", "article", "blog",
        "email", "letter", "speech", "script", "dialogue", "character",
        "plot", "worldbuilding", "brainstorm", "idea", "concept"
    ],
    "tool_use": [
        "search", "lookup", "find", "fetch", "get", "retrieve", "query",
        "calculate", "compute", "convert", "translate", "format", "parse",
        "validate", "check", "verify", "test", "run", "execute"
    ]
}

# Complexity indicators
COMPLEXITY_INDICATORS = {
    "complex": [
        "architecture", "system design", "distributed", "scalable", "microservice",
        "multi-step", "pipeline", "workflow", "orchestration", "integration",
        "optimization", "refactor", "migration", "deployment", "infrastructure"
    ],
    "moderate": [
        "implement", "build", "create", "develop", "design", "configure",
        "setup", "integrate", "connect", "transform", "process", "handle"
    ]
}

# Tool-use triggers
TOOL_TRIGGERS = [
    "search", "lookup", "find", "fetch", "get", "retrieve", "current",
    "latest", "recent", "today", "now", "weather", "stock", "price",
    "calculate", "compute", "convert", "translate", "run", "execute",
    "test", "verify", "check", "validate", "api", "endpoint", "database"
]

# Vision triggers
VISION_TRIGGERS = [
    "image", "picture", "photo", "screenshot", "diagram", "chart", "graph",
    "visual", "look at", "see", "show me", "analyze this", "describe"
]

# Long context triggers
LONG_CONTEXT_TRIGGERS = [
    "document", "paper", "report", "book", "article", "transcript", "log",
    "history", "conversation", "thread", "context", "background", "large",
    "entire", "full", "complete", "comprehensive", "detailed"
]


def estimate_tokens(text: str) -> int:
    """Rough token estimation: ~4 chars per token for English."""
    return len(text) // 4


def classify_task_type(messages: List[dict]) -> tuple[str, float]:
    """Classify the primary task type from messages."""
    # Combine all user messages for analysis
    user_text = " ".join(
        msg.get("content", "") for msg in messages
        if msg.get("role") == "user" and msg.get("content")
    ).lower()
    
    if not user_text:
        return "chat", 0.5
    
    scores = {task: 0 for task in TASK_KEYWORDS}
    
    for task, keywords in TASK_KEYWORDS.items():
        for keyword in keywords:
            # Count occurrences with word boundaries
            pattern = r'\b' + re.escape(keyword) + r'\b'
            scores[task] += len(re.findall(pattern, user_text))
    
    # Find highest scoring task
    best_task = max(scores, key=scores.get)
    max_score = scores[best_task]
    
    # Calculate confidence based on score
    confidence = min(0.95, 0.4 + (max_score * 0.15))
    
    # Default to chat if no strong signals
    if max_score == 0:
        return "chat", 0.5
    
    return best_task, confidence


def classify_complexity(messages: List[dict]) -> tuple[str, float]:
    """Classify request complexity."""
    user_text = " ".join(
        msg.get("content", "") for msg in messages
        if msg.get("role") == "user" and msg.get("content")
    ).lower()
    
    if not user_text:
        return "simple", 0.5
    
    # Check for complex indicators
    for indicator in COMPLEXITY_INDICATORS["complex"]:
        if indicator in user_text:
            return "complex", 0.8
    
    # Check for moderate indicators
    for indicator in COMPLEXITY_INDICATORS["moderate"]:
        if indicator in user_text:
            return "moderate", 0.7
    
    # Check message count and length
    user_msg_count = sum(1 for m in messages if m.get("role") == "user")
    total_chars = len(user_text)
    
    if user_msg_count > 3 or total_chars > 2000:
        return "moderate", 0.6
    
    return "simple", 0.6


def detect_capabilities(messages: List[dict]) -> tuple[bool, bool, bool]:
    """Detect required capabilities: tools, vision, long_context."""
    user_text = " ".join(
        msg.get("content", "") for msg in messages
        if msg.get("role") == "user" and msg.get("content")
    ).lower()
    
    requires_tools = any(trigger in user_text for trigger in TOOL_TRIGGERS)
    requires_vision = any(trigger in user_text for trigger in VISION_TRIGGERS)
    requires_long_context = any(trigger in user_text for trigger in LONG_CONTEXT_TRIGGERS)
    
    # Also check for explicit tool definitions in the request
    # (This would be passed separately in real implementation)
    
    return requires_tools, requires_vision, requires_long_context


async def analyze_request(messages: List[dict], tools: List[dict] | None = None) -> TaskAnalysis:
    """Main entry point: analyze a chat request and return JEV classification."""
    task_type, task_confidence = classify_task_type(messages)
    complexity, complexity_confidence = classify_complexity(messages)
    requires_tools, requires_vision, requires_long_context = detect_capabilities(messages)
    
    # Override tool detection if tools are explicitly provided
    if tools:
        requires_tools = True
    
    # Estimate tokens from all messages
    total_text = " ".join(
        msg.get("content", "") for msg in messages if msg.get("content")
    )
    estimated_tokens = estimate_tokens(total_text)
    
    # Overall confidence
    confidence = (task_confidence + complexity_confidence) / 2
    
    return TaskAnalysis(
        task_type=task_type,
        complexity=complexity,
        requires_tools=requires_tools,
        requires_vision=requires_vision,
        requires_long_context=requires_long_context,
        estimated_tokens=estimated_tokens,
        confidence=confidence
    )

