"""Tests for Pydantic models."""

import pytest
from claude_code_client.models import (
    CompletionRequest,
    CompletionResponse,
    AgenticTaskRequest,
    AgenticTaskResponse,
    ExecutionLogEntry,
    Artifact,
)


def test_completion_request():
    """Test CompletionRequest model."""
    req = CompletionRequest(
        prompt="Test prompt",
        model="sonnet",
        max_tokens=500,
        temperature=0.8,
    )
    assert req.prompt == "Test prompt"
    assert req.model == "sonnet"
    assert req.max_tokens == 500


def test_completion_request_defaults():
    """Test CompletionRequest default values."""
    req = CompletionRequest(prompt="Test")
    assert req.model is None
    assert req.max_tokens == 1000
    assert req.temperature == 1.0


def test_agentic_task_request():
    """Test AgenticTaskRequest model."""
    req = AgenticTaskRequest(
        description="Analyze code",
        allow_tools=["Read", "Grep"],
        allow_agents=["security-auditor"],
        timeout=120,
    )
    assert req.description == "Analyze code"
    assert "Read" in req.allow_tools
    assert req.timeout == 120


def test_agentic_task_request_defaults():
    """Test AgenticTaskRequest default values."""
    req = AgenticTaskRequest(description="Test")
    assert req.allow_tools == []
    assert req.timeout == 300
    assert req.max_cost == 1.0
    assert req.working_directory == "/project"


def test_execution_log_entry():
    """Test ExecutionLogEntry model."""
    entry = ExecutionLogEntry(
        step=1,
        timestamp="2024-01-01T00:00:00Z",
        action="tool_call",
        details={"tool": "Read", "file": "test.py"},
    )
    assert entry.step == 1
    assert entry.action == "tool_call"
    assert entry.details["tool"] == "Read"


def test_artifact():
    """Test Artifact model."""
    artifact = Artifact(
        type="file",
        path="/tmp/report.txt",
        size_bytes=1024,
        created_at="2024-01-01T00:00:00Z",
    )
    assert artifact.type == "file"
    assert artifact.path == "/tmp/report.txt"
    assert artifact.size_bytes == 1024


def test_agentic_task_response():
    """Test AgenticTaskResponse model."""
    response = AgenticTaskResponse(
        task_id="task-123",
        status="completed",
        result={"summary": "Done"},
        execution_log=[],
        artifacts=[],
        usage={"total_cost": 0.05},
    )
    assert response.task_id == "task-123"
    assert response.status == "completed"
    assert response.usage["total_cost"] == 0.05
