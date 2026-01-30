"""
Comprehensive tests for REST API endpoints.

Tests cover:
- Chat completion endpoint
- Batch processing endpoint
- Usage tracking endpoint
- Model routing endpoint
- Budget enforcement
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import asyncio

from main import app
from src.worker_pool import WorkerPool, TaskResult, TaskStatus
from src.budget_manager import BudgetManager


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


@pytest.fixture
def mock_worker_pool():
    """Mock worker pool for testing."""
    pool = Mock(spec=WorkerPool)
    pool.running = True
    return pool


@pytest.fixture
def mock_budget_manager():
    """Mock budget manager for testing."""
    manager = AsyncMock(spec=BudgetManager)
    return manager


# ============================================================================
# Test: POST /v1/chat/completions
# ============================================================================

def test_chat_completion_success(client, mock_worker_pool, mock_budget_manager):
    """Test successful chat completion."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget check
        mock_budget_manager.check_budget.return_value = True
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 1000,
            "total_cost": 0.05,
            "by_model": {},
            "limit": 100000,
            "remaining": 99000
        }

        # Mock worker pool result
        task_id = "test-task-123"
        mock_worker_pool.submit.return_value = task_id
        mock_worker_pool.get_result.return_value = TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            completion="This is a test response from Claude.",
            usage={
                "input_tokens": 10,
                "output_tokens": 20,
                "total_tokens": 30
            },
            cost=0.0001
        )

        # Make request
        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "Hello, Claude!"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["id"] == task_id
        assert data["model"] == "haiku"
        assert data["content"] == "This is a test response from Claude."
        assert data["usage"]["total_tokens"] == 30
        assert data["cost"] == 0.0001
        assert data["project_id"] == "test-project"


def test_chat_completion_auto_model_selection(client, mock_worker_pool, mock_budget_manager):
    """Test chat completion with automatic model selection."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget check
        mock_budget_manager.check_budget.return_value = True
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 1000,
            "total_cost": 0.05,
            "by_model": {},
            "limit": 100000,
            "remaining": 99000
        }

        # Mock worker pool result
        task_id = "test-task-456"
        mock_worker_pool.submit.return_value = task_id
        mock_worker_pool.get_result.return_value = TaskResult(
            task_id=task_id,
            status=TaskStatus.COMPLETED,
            completion="Auto-selected model response.",
            usage={
                "input_tokens": 15,
                "output_tokens": 25,
                "total_tokens": 40
            },
            cost=0.0002
        )

        # Make request without specifying model
        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "Analyze this complex system architecture"}
            ],
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        # Should auto-select sonnet for "analyze" keyword
        assert data["model"] == "sonnet"


def test_chat_completion_budget_exceeded(client, mock_worker_pool, mock_budget_manager):
    """Test chat completion when budget is exceeded."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget check - budget exceeded
        mock_budget_manager.check_budget.return_value = False
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 99500,
            "total_cost": 5.0,
            "by_model": {},
            "limit": 100000,
            "remaining": 500
        }

        # Make request
        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "Hello!"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        assert response.status_code == 429
        assert "Budget exceeded" in response.json()["detail"]


def test_chat_completion_task_failed(client, mock_worker_pool, mock_budget_manager):
    """Test chat completion when task fails."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget check
        mock_budget_manager.check_budget.return_value = True
        mock_budget_manager.get_usage.return_value = {
            "remaining": 99000
        }

        # Mock worker pool result - failed task
        task_id = "test-task-789"
        mock_worker_pool.submit.return_value = task_id
        mock_worker_pool.get_result.return_value = TaskResult(
            task_id=task_id,
            status=TaskStatus.FAILED,
            error="Process crashed"
        )

        # Make request
        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "Hello!"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        assert response.status_code == 500
        assert "Task failed" in response.json()["detail"]


# ============================================================================
# Test: POST /v1/batch
# ============================================================================

def test_batch_processing_success(client, mock_worker_pool, mock_budget_manager):
    """Test successful batch processing."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager
        mock_budget_manager.get_usage.return_value = {
            "remaining": 99000
        }

        # Mock worker pool - simulate 3 successful tasks
        task_results = [
            TaskResult(
                task_id=f"task-{i}",
                status=TaskStatus.COMPLETED,
                completion=f"Response {i}",
                usage={"input_tokens": 10, "output_tokens": 15, "total_tokens": 25},
                cost=0.0001
            )
            for i in range(3)
        ]

        mock_worker_pool.submit.side_effect = [f"task-{i}" for i in range(3)]
        mock_worker_pool.get_result.side_effect = task_results

        # Make batch request
        response = client.post("/v1/batch", json={
            "prompts": [
                {"prompt": "Task 1", "id": "1"},
                {"prompt": "Task 2", "id": "2"},
                {"prompt": "Task 3", "id": "3"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert data["completed"] == 3
        assert data["failed"] == 0
        assert len(data["results"]) == 3
        assert abs(data["total_cost"] - 0.0003) < 1e-10  # Floating point comparison
        assert data["total_tokens"] == 75


def test_batch_processing_partial_failure(client, mock_worker_pool, mock_budget_manager):
    """Test batch processing with some failures."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager
        mock_budget_manager.get_usage.return_value = {
            "remaining": 99000
        }

        # Mock worker pool - 2 success, 1 failure
        task_results = [
            TaskResult(
                task_id="task-0",
                status=TaskStatus.COMPLETED,
                completion="Response 0",
                usage={"input_tokens": 10, "output_tokens": 15, "total_tokens": 25},
                cost=0.0001
            ),
            TaskResult(
                task_id="task-1",
                status=TaskStatus.FAILED,
                error="Task failed"
            ),
            TaskResult(
                task_id="task-2",
                status=TaskStatus.COMPLETED,
                completion="Response 2",
                usage={"input_tokens": 10, "output_tokens": 15, "total_tokens": 25},
                cost=0.0001
            )
        ]

        mock_worker_pool.submit.side_effect = [f"task-{i}" for i in range(3)]
        mock_worker_pool.get_result.side_effect = task_results

        # Make batch request
        response = client.post("/v1/batch", json={
            "prompts": [
                {"prompt": "Task 1"},
                {"prompt": "Task 2"},
                {"prompt": "Task 3"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["total"] == 3
        assert data["completed"] == 2
        assert data["failed"] == 1
        assert data["total_cost"] == 0.0002
        assert data["total_tokens"] == 50


# ============================================================================
# Test: GET /v1/usage
# ============================================================================

def test_usage_endpoint(client, mock_budget_manager):
    """Test usage statistics endpoint."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock usage stats
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 5000,
            "total_cost": 0.25,
            "by_model": {
                "haiku": {"tokens": 2000, "cost": 0.05},
                "sonnet": {"tokens": 3000, "cost": 0.20}
            },
            "limit": 100000,
            "remaining": 95000
        }

        # Make request
        response = client.get("/v1/usage?project_id=test-project&period=month")

        assert response.status_code == 200
        data = response.json()

        assert data["project_id"] == "test-project"
        assert data["period"] == "month"
        assert data["total_tokens"] == 5000
        assert data["total_cost"] == 0.25
        assert "haiku" in data["by_model"]
        assert "sonnet" in data["by_model"]
        assert data["limit"] == 100000
        assert data["remaining"] == 95000


def test_usage_endpoint_invalid_period(client, mock_budget_manager):
    """Test usage endpoint with invalid period."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager to raise ValueError
        mock_budget_manager.get_usage.side_effect = ValueError("Invalid period: invalid")

        # Make request
        response = client.get("/v1/usage?project_id=test-project&period=invalid")

        assert response.status_code == 400


# ============================================================================
# Test: POST /v1/route
# ============================================================================

def test_route_endpoint_haiku(client, mock_budget_manager):
    """Test routing recommendation for simple task."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 1000,
            "total_cost": 0.05,
            "limit": 100000,
            "remaining": 99000
        }

        # Make request with simple prompt
        response = client.post("/v1/route", json={
            "prompt": "List all files",
            "context_size": 50,
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["recommended_model"] == "haiku"
        assert "budget_status" in data
        assert data["budget_status"]["remaining"] == 99000


def test_route_endpoint_sonnet(client, mock_budget_manager):
    """Test routing recommendation for complex task."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 1000,
            "total_cost": 0.05,
            "limit": 100000,
            "remaining": 99000
        }

        # Make request with complex prompt
        response = client.post("/v1/route", json={
            "prompt": "Analyze and refactor this codebase architecture",
            "context_size": 5000,
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["recommended_model"] == "sonnet"
        assert "Complex reasoning keywords" in data["reasoning"]


def test_route_endpoint_opus(client, mock_budget_manager):
    """Test routing recommendation for large context."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 1000,
            "total_cost": 0.05,
            "limit": 100000,
            "remaining": 99000
        }

        # Make request with large context
        response = client.post("/v1/route", json={
            "prompt": "Review this code",
            "context_size": 15000,
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["recommended_model"] == "opus"
        assert "Large context requires Opus" in data["reasoning"]


def test_route_endpoint_low_budget(client, mock_budget_manager):
    """Test routing recommendation with low budget."""
    with patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget manager - low budget
        mock_budget_manager.get_usage.return_value = {
            "total_tokens": 99500,
            "total_cost": 5.0,
            "limit": 100000,
            "remaining": 500
        }

        # Make request (should force haiku due to budget)
        response = client.post("/v1/route", json={
            "prompt": "Analyze this complex system",
            "context_size": 5000,
            "project_id": "test-project"
        })

        assert response.status_code == 200
        data = response.json()

        assert data["recommended_model"] == "haiku"
        assert "Budget constraint" in data["reasoning"]


# ============================================================================
# Test: Budget Enforcement
# ============================================================================

def test_budget_enforcement_blocks_request(client, mock_worker_pool, mock_budget_manager):
    """Test that budget enforcement blocks requests when limit exceeded."""
    with patch('src.api.worker_pool', mock_worker_pool), \
         patch('src.api.budget_manager', mock_budget_manager):

        # Mock budget check - budget exceeded
        mock_budget_manager.check_budget.return_value = False
        mock_budget_manager.get_usage.return_value = {
            "remaining": 100
        }

        # Make request
        response = client.post("/v1/chat/completions", json={
            "messages": [
                {"role": "user", "content": "Hello!"}
            ],
            "model": "haiku",
            "project_id": "test-project"
        })

        # Should be blocked
        assert response.status_code == 429

        # Worker pool should NOT have been called
        mock_worker_pool.submit.assert_not_called()


# ============================================================================
# Test: Health Endpoint
# ============================================================================

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get("/health")

    assert response.status_code == 200
    data = response.json()

    assert data["status"] == "ok"
    assert data["version"] == "0.1.0"
    assert "services" in data


# ============================================================================
# Test: Root Endpoint
# ============================================================================

def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")

    assert response.status_code == 200
    data = response.json()

    assert data["name"] == "Claude Code API Service"
    assert "endpoints" in data
    assert data["endpoints"]["chat"] == "/v1/chat/completions"
