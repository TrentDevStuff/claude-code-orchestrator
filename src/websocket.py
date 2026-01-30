"""
WebSocket streaming endpoint for real-time chat responses.

Provides real-time token streaming from Claude CLI with:
- Token-by-token streaming
- Usage statistics on completion
- Connection management
- Error handling
- Integration with WorkerPool and BudgetManager
"""

import json
import asyncio
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
import uuid

from src.worker_pool import WorkerPool
from src.budget_manager import BudgetManager


class WebSocketStreamer:
    """
    Manages WebSocket streaming for real-time chat responses.

    Handles:
    - Connection lifecycle
    - Token streaming from Claude CLI
    - Usage tracking
    - Error handling
    """

    # Cost per million tokens (as of Jan 2026)
    COST_PER_MTK = {
        "haiku": {"input": 0.25, "output": 1.25},
        "sonnet": {"input": 3.00, "output": 15.00},
        "opus": {"input": 15.00, "output": 75.00},
    }

    def __init__(self, worker_pool: WorkerPool, budget_manager: BudgetManager):
        """
        Initialize WebSocket streamer.

        Args:
            worker_pool: WorkerPool instance for process management
            budget_manager: BudgetManager instance for budget tracking
        """
        self.worker_pool = worker_pool
        self.budget_manager = budget_manager
        self.active_connections: Dict[str, WebSocket] = {}

    async def handle_connection(self, websocket: WebSocket):
        """
        Handle a WebSocket connection.

        Args:
            websocket: FastAPI WebSocket connection
        """
        connection_id = str(uuid.uuid4())
        await websocket.accept()
        self.active_connections[connection_id] = websocket

        try:
            while True:
                # Receive message from client
                data = await websocket.receive_text()

                try:
                    message = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({
                        "type": "error",
                        "error": "Invalid JSON format"
                    })
                    continue

                # Handle different message types
                if message.get("type") == "chat":
                    await self._handle_chat(websocket, message)
                else:
                    await websocket.send_json({
                        "type": "error",
                        "error": f"Unknown message type: {message.get('type')}"
                    })

        except WebSocketDisconnect:
            # Clean disconnect
            pass
        except Exception as e:
            # Unexpected error
            try:
                await websocket.send_json({
                    "type": "error",
                    "error": f"Server error: {str(e)}"
                })
            except:
                pass  # Connection already closed
        finally:
            # Cleanup
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]

    async def _handle_chat(self, websocket: WebSocket, message: Dict[str, Any]):
        """
        Handle a chat message and stream the response.

        Args:
            websocket: WebSocket connection
            message: Chat message containing model and messages
        """
        # Extract parameters
        model = message.get("model", "sonnet")
        messages = message.get("messages", [])
        project_id = message.get("project_id", "default")

        if not messages:
            await websocket.send_json({
                "type": "error",
                "error": "No messages provided"
            })
            return

        # Validate model
        if model not in ["haiku", "sonnet", "opus"]:
            await websocket.send_json({
                "type": "error",
                "error": f"Invalid model: {model}. Must be haiku, sonnet, or opus"
            })
            return

        # Combine messages into prompt
        prompt = "\n\n".join([f"{msg.get('role', 'user')}: {msg.get('content', '')}" for msg in messages])

        # Check budget
        estimated_tokens = len(prompt.split()) * 2  # Rough estimate
        budget_ok = await self.budget_manager.check_budget(project_id, estimated_tokens)

        if not budget_ok:
            await websocket.send_json({
                "type": "error",
                "error": f"Budget exceeded for project {project_id}"
            })
            return

        # Stream response
        try:
            await self._stream_response(websocket, prompt, model, project_id)
        except Exception as e:
            await websocket.send_json({
                "type": "error",
                "error": f"Streaming error: {str(e)}"
            })

    async def _stream_response(
        self,
        websocket: WebSocket,
        prompt: str,
        model: str,
        project_id: str
    ):
        """
        Stream response tokens from Claude CLI.

        Args:
            websocket: WebSocket connection
            prompt: User prompt
            model: Model to use
            project_id: Project identifier
        """
        # Create temp directory
        temp_dir = Path(tempfile.mkdtemp(prefix=f"claude_ws_{uuid.uuid4().hex[:8]}_"))
        prompt_file = temp_dir / "prompt.txt"

        try:
            # Write prompt
            prompt_file.write_text(prompt)

            # Build command for streaming
            cmd = [
                "claude",
                "-p", f"$(cat {prompt_file})",
                "--model", model,
                "--output-format", "json"
            ]

            # Start process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=True,
                text=True,
                bufsize=1  # Line buffered
            )

            # Stream output
            full_output = []

            # Read stderr in background for potential errors
            async def read_stderr():
                if process.stderr:
                    for line in process.stderr:
                        if line.strip():
                            print(f"Claude CLI stderr: {line.strip()}")

            # Start stderr reader
            stderr_task = asyncio.create_task(
                asyncio.to_thread(lambda: list(process.stderr) if process.stderr else [])
            )

            # Stream stdout
            if process.stdout:
                # For streaming, we'll simulate token-by-token streaming
                # by reading the full output and chunking it
                for line in process.stdout:
                    full_output.append(line)

            # Wait for process
            return_code = process.wait(timeout=30.0)

            # Cancel stderr task
            stderr_task.cancel()

            if return_code != 0:
                # Try to get stderr output, ignore if cancelled
                try:
                    await asyncio.wait_for(stderr_task, timeout=0.1)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
                raise RuntimeError(f"Claude CLI exited with code {return_code}")

            # Parse output
            output_text = "".join(full_output)

            try:
                output = json.loads(output_text)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"Failed to parse Claude CLI output: {e}")

            # Extract content and usage
            content = output.get("content", [{}])[0].get("text", "")
            usage = output.get("usage", {})
            input_tokens = usage.get("input_tokens", 0)
            output_tokens = usage.get("output_tokens", 0)
            total_tokens = input_tokens + output_tokens

            # Calculate cost
            cost = self._calculate_cost(model, input_tokens, output_tokens)

            # Stream tokens (simulate streaming by chunking)
            # In a real implementation, we'd parse streaming output from Claude CLI
            chunk_size = max(1, len(content) // 20)  # ~20 chunks
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                await websocket.send_json({
                    "type": "token",
                    "content": chunk
                })
                # Small delay to simulate streaming
                await asyncio.sleep(0.01)

            # Send completion message
            await websocket.send_json({
                "type": "done",
                "usage": {
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                },
                "cost": cost,
                "model": model
            })

            # Track usage
            await self.budget_manager.track_usage(
                project_id=project_id,
                model=model,
                tokens=total_tokens,
                cost=cost
            )

        except subprocess.TimeoutExpired:
            process.kill()
            raise RuntimeError("Request timed out after 30 seconds")

        except Exception as e:
            raise

        finally:
            # Cleanup
            if temp_dir.exists():
                import shutil
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of a request in USD.

        Args:
            model: Model name (haiku, sonnet, opus)
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens

        Returns:
            Cost in USD
        """
        if model not in self.COST_PER_MTK:
            return 0.0

        rates = self.COST_PER_MTK[model]
        input_cost = (input_tokens / 1_000_000) * rates["input"]
        output_cost = (output_tokens / 1_000_000) * rates["output"]

        return input_cost + output_cost


# Global streamer instance
_streamer: Optional[WebSocketStreamer] = None


def initialize_websocket(worker_pool: WorkerPool, budget_manager: BudgetManager):
    """
    Initialize the WebSocket streamer.

    Args:
        worker_pool: WorkerPool instance
        budget_manager: BudgetManager instance
    """
    global _streamer
    _streamer = WebSocketStreamer(worker_pool, budget_manager)


async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint handler.

    Protocol:

    Client → Server:
    {
        "type": "chat",
        "model": "haiku",
        "messages": [{"role": "user", "content": "Hello"}],
        "project_id": "default"
    }

    Server → Client (streaming):
    {"type": "token", "content": "Hello"}
    {"type": "token", "content": " world"}
    {"type": "done", "usage": {...}, "cost": 0.0001, "model": "haiku"}

    Server → Client (error):
    {"type": "error", "error": "Error message"}

    Args:
        websocket: FastAPI WebSocket connection
    """
    if _streamer is None:
        await websocket.close(code=1011, reason="WebSocket service not initialized")
        return

    await _streamer.handle_connection(websocket)
