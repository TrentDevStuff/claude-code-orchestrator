"""
Worker Pool Manager for Claude CLI processes.

Manages a pool of Claude CLI subprocess workers with:
- Process pooling with configurable max workers
- Task queue system for when workers are busy
- Timeout handling
- PID tracking and automatic cleanup
- Thread-safe operations
"""

from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from queue import Empty, Queue


class TaskStatus(Enum):
    """Status of a submitted task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    KILLED = "killed"


@dataclass
class TaskResult:
    """Result of a completed task."""

    task_id: str
    status: TaskStatus
    completion: str | None = None
    usage: dict[str, int] | None = None
    cost: float | None = None
    error: str | None = None


@dataclass
class Task:
    """Internal task representation."""

    task_id: str
    prompt: str
    model: str
    project_id: str
    status: TaskStatus = TaskStatus.PENDING
    process: subprocess.Popen | None = None
    temp_dir: Path | None = None
    result: TaskResult | None = None
    start_time: float | None = None
    timeout: float = 30.0


class WorkerPool:
    """
    Manages a pool of Claude CLI worker processes.

    Features:
    - Configurable max concurrent workers
    - Task queue for overflow
    - Automatic worker cleanup
    - Timeout handling
    - PID tracking
    """

    # Cost per million tokens (as of Jan 2026)
    COST_PER_MTK = {
        "haiku": {"input": 0.25, "output": 1.25},
        "sonnet": {"input": 3.00, "output": 15.00},
        "opus": {"input": 15.00, "output": 75.00},
    }

    def __init__(self, max_workers: int = 5):
        """
        Initialize the worker pool.

        Args:
            max_workers: Maximum number of concurrent Claude CLI processes
        """
        self.max_workers = max_workers
        self.tasks: dict[str, Task] = {}
        self.task_queue: Queue = Queue()
        self.active_workers = 0
        self.lock = threading.Lock()
        self.monitor_thread = None
        self.running = False

    def start(self):
        """Start the worker pool monitor thread."""
        if self.running:
            return

        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop(self):
        """Stop the worker pool and cleanup all tasks."""
        self.drain(timeout=5)

    def drain(self, timeout: int = 30) -> tuple:
        """
        Gracefully drain the worker pool.

        Stops accepting new tasks, waits for active tasks to finish up to
        *timeout* seconds, then SIGTERMs stragglers (with a 5 s grace
        period before SIGKILL).

        Returns:
            (completed, killed) — counts of tasks that finished vs were force-killed.
        """
        import signal

        self.running = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=min(timeout, 5.0))

        completed = 0
        killed = 0

        # Wait for active tasks to finish
        deadline = time.time() + timeout
        while time.time() < deadline:
            with self.lock:
                still_running = [
                    t for t in self.tasks.values() if t.process and t.process.poll() is None
                ]
            if not still_running:
                break
            time.sleep(0.5)

        # Count completed, SIGTERM remaining
        with self.lock:
            for task in self.tasks.values():
                if task.process is None:
                    continue
                if task.process.poll() is not None:
                    completed += 1
                else:
                    # Still running after timeout — send SIGTERM
                    try:
                        task.process.send_signal(signal.SIGTERM)
                    except OSError:
                        pass

        # Give SIGTERM 5 s to take effect, then SIGKILL
        term_deadline = time.time() + 5
        while time.time() < term_deadline:
            with self.lock:
                stragglers = [
                    t for t in self.tasks.values() if t.process and t.process.poll() is None
                ]
            if not stragglers:
                break
            time.sleep(0.5)

        with self.lock:
            for task in self.tasks.values():
                if task.process and task.process.poll() is None:
                    try:
                        task.process.kill()
                        task.process.wait(timeout=2.0)
                    except Exception:
                        pass
                    killed += 1
                self._cleanup_task(task)

        return completed, killed

    def submit(
        self, prompt: str, model: str = "sonnet", project_id: str = "default", timeout: float = 30.0
    ) -> str:
        """
        Submit a task to the worker pool.

        Args:
            prompt: The prompt to send to Claude
            model: Model to use (haiku, sonnet, opus)
            project_id: Project identifier for tracking
            timeout: Timeout in seconds (default 30s)

        Returns:
            task_id: Unique identifier for this task
        """
        task_id = str(uuid.uuid4())

        task = Task(
            task_id=task_id, prompt=prompt, model=model, project_id=project_id, timeout=timeout
        )

        with self.lock:
            self.tasks[task_id] = task
            self.task_queue.put(task_id)

        # Ensure monitor is running
        if not self.running:
            self.start()

        return task_id

    def get_result(self, task_id: str, timeout: float = 30.0) -> TaskResult:
        """
        Get the result of a submitted task (blocking).

        Args:
            task_id: The task identifier returned by submit()
            timeout: How long to wait for completion (seconds)

        Returns:
            TaskResult with completion, usage, and cost information

        Raises:
            ValueError: If task_id not found
            TimeoutError: If task doesn't complete within timeout
        """
        if task_id not in self.tasks:
            raise ValueError(f"Task {task_id} not found")

        start_time = time.time()
        while time.time() - start_time < timeout:
            task = self.tasks[task_id]

            if task.result:
                return task.result

            time.sleep(0.1)

        # Timeout - kill the task if it's running
        with self.lock:
            task = self.tasks[task_id]
            if task.process and task.process.poll() is None:
                task.process.kill()
                task.status = TaskStatus.TIMEOUT

            task.result = TaskResult(
                task_id=task_id,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {timeout} seconds",
            )

        return task.result

    def kill(self, task_id: str) -> bool:
        """
        Terminate a running task.

        Args:
            task_id: The task identifier to kill

        Returns:
            True if task was killed, False if not found or already finished
        """
        with self.lock:
            if task_id not in self.tasks:
                return False

            task = self.tasks[task_id]

            if task.process and task.process.poll() is None:
                task.process.kill()
                task.status = TaskStatus.KILLED
                task.result = TaskResult(
                    task_id=task_id, status=TaskStatus.KILLED, error="Task was killed by user"
                )
                self.active_workers -= 1
                self._cleanup_task(task)
                return True

        return False

    def get_active_pids(self) -> dict[str, int]:
        """
        Get PIDs of all active worker processes.

        Returns:
            Dict mapping task_id to PID
        """
        pids = {}
        with self.lock:
            for task_id, task in self.tasks.items():
                if task.process and task.process.poll() is None:
                    pids[task_id] = task.process.pid
        return pids

    def _monitor_loop(self):
        """Main monitoring loop - processes queue and checks worker status."""
        while self.running:
            # Process queue if we have capacity
            with self.lock:
                can_start = self.active_workers < self.max_workers

            if can_start:
                try:
                    task_id = self.task_queue.get(timeout=0.5)
                    self._start_task(task_id)
                except Empty:
                    pass

            # Check for completed tasks
            self._check_completed_tasks()

            time.sleep(0.1)

    def _start_task(self, task_id: str):
        """Start executing a task."""
        with self.lock:
            task = self.tasks.get(task_id)
            if not task:
                return

            # Create temp directory for this task
            task.temp_dir = Path(tempfile.mkdtemp(prefix=f"claude_task_{task_id[:8]}_"))
            prompt_file = task.temp_dir / "prompt.txt"

            # Write prompt to file
            prompt_file.write_text(task.prompt)

            # Build command - use shell string for proper prompt handling
            # This matches the orchestrator's daemon pattern
            claude_path = shutil.which("claude") or "claude"
            cmd = (
                f'{claude_path} -p "$(cat {prompt_file})" '
                f"--model {task.model} "
                f"--output-format json"
            )

            # Start process
            try:
                task.process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    shell=True,
                    text=True,
                    executable="/bin/bash",  # Use bash for $(cat ...) substitution
                )
                task.status = TaskStatus.RUNNING
                task.start_time = time.time()
                self.active_workers += 1

            except Exception as e:
                task.status = TaskStatus.FAILED
                task.result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=f"Failed to start process: {str(e)}",
                )
                self._cleanup_task(task)

    def _check_completed_tasks(self):
        """Check for completed tasks and process their results."""
        with self.lock:
            completed_tasks = []

            for task_id, task in self.tasks.items():
                if task.status != TaskStatus.RUNNING:
                    continue

                # Check if process is done
                if task.process and task.process.poll() is not None:
                    completed_tasks.append(task_id)
                    continue

                # Check for timeout
                if task.start_time and (time.time() - task.start_time) > task.timeout:
                    if task.process:
                        task.process.kill()
                    task.status = TaskStatus.TIMEOUT
                    task.result = TaskResult(
                        task_id=task_id,
                        status=TaskStatus.TIMEOUT,
                        error=f"Task timed out after {task.timeout} seconds",
                    )
                    self.active_workers -= 1
                    completed_tasks.append(task_id)

            # Process completed tasks outside the iteration
            for task_id in completed_tasks:
                self._process_completed_task(task_id)

    def _process_completed_task(self, task_id: str):
        """Process a completed task and extract results."""
        task = self.tasks[task_id]

        if not task.process:
            return

        # Skip if already has a result (e.g., from timeout)
        if task.result:
            return

        returncode = task.process.returncode

        # Try to get output - may already be consumed in some edge cases
        try:
            stdout, stderr = task.process.communicate(timeout=2.0)
        except ValueError:
            # Process output already consumed (e.g., killed task)
            stdout, stderr = "", ""

        if returncode == 0:
            try:
                # Parse JSON output from Claude CLI
                output = json.loads(stdout)

                # Extract usage information
                usage = output.get("usage", {})
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)

                # Calculate cost
                cost = self._calculate_cost(task.model, input_tokens, output_tokens)

                task.status = TaskStatus.COMPLETED
                task.result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED,
                    completion=output.get(
                        "result", ""
                    ),  # Fixed: Claude CLI returns "result" not "content"
                    usage={
                        "input_tokens": input_tokens,
                        "output_tokens": output_tokens,
                        "total_tokens": input_tokens + output_tokens,
                    },
                    cost=cost,
                )

            except json.JSONDecodeError as e:
                task.status = TaskStatus.FAILED
                task.result = TaskResult(
                    task_id=task_id,
                    status=TaskStatus.FAILED,
                    error=f"Failed to parse JSON output: {str(e)}\nOutput: {stdout}",
                )

        else:
            task.status = TaskStatus.FAILED
            task.result = TaskResult(
                task_id=task_id,
                status=TaskStatus.FAILED,
                error=f"Process exited with code {returncode}\nStderr: {stderr}",
            )

        self.active_workers -= 1
        self._cleanup_task(task)

    def _cleanup_task(self, task: Task):
        """Clean up temporary files for a task."""
        if task.temp_dir and task.temp_dir.exists():
            try:
                import shutil

                shutil.rmtree(task.temp_dir)
            except Exception:
                pass  # Best effort cleanup

    def _calculate_cost(self, model: str, input_tokens: int, output_tokens: int) -> float:
        """
        Calculate the cost of a task in USD.

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
