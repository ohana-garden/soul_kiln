"""
Code Execution Tool.

Provides multi-runtime code execution capabilities.
"""

import logging
import os
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class Runtime(str, Enum):
    """Supported execution runtimes."""

    PYTHON = "python"
    NODEJS = "nodejs"
    TERMINAL = "terminal"
    OUTPUT = "output"  # Get output from running process
    RESET = "reset"  # Reset/kill session


class ExecutionState(str, Enum):
    """State of an execution session."""

    IDLE = "idle"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"


@dataclass
class ExecutionResult:
    """Result of code execution."""

    id: str = field(default_factory=lambda: f"exec_{uuid.uuid4().hex[:8]}")
    runtime: Runtime = Runtime.PYTHON
    code: str = ""
    stdout: str = ""
    stderr: str = ""
    return_code: int | None = None
    state: ExecutionState = ExecutionState.IDLE
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    session_id: int = 0

    @property
    def success(self) -> bool:
        """Check if execution was successful."""
        return self.state == ExecutionState.COMPLETED and self.return_code == 0

    @property
    def duration_seconds(self) -> float | None:
        """Get execution duration."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "runtime": self.runtime.value,
            "code": self.code,
            "stdout": self.stdout,
            "stderr": self.stderr,
            "return_code": self.return_code,
            "state": self.state.value,
            "success": self.success,
            "duration": self.duration_seconds,
            "error": self.error,
            "session_id": self.session_id,
        }


class ExecutionSession:
    """A code execution session with persistent state."""

    def __init__(self, session_id: int = 0):
        self.session_id = session_id
        self.process: subprocess.Popen | None = None
        self.output_buffer: list[str] = []
        self.error_buffer: list[str] = []
        self._lock = threading.Lock()
        self.state = ExecutionState.IDLE
        self.last_activity = datetime.utcnow()

    def reset(self) -> None:
        """Reset/kill the session."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except Exception as e:
                logger.error(f"Error killing process: {e}")
            self.process = None

        with self._lock:
            self.output_buffer.clear()
            self.error_buffer.clear()
        self.state = ExecutionState.IDLE
        self.last_activity = datetime.utcnow()

    def get_output(self) -> tuple[str, str]:
        """Get and clear output buffers."""
        with self._lock:
            stdout = "\n".join(self.output_buffer)
            stderr = "\n".join(self.error_buffer)
            self.output_buffer.clear()
            self.error_buffer.clear()
        return stdout, stderr


class CodeExecutor:
    """
    Multi-runtime code execution tool.

    Features:
    - Python, Node.js, and terminal execution
    - Session management with persistent state
    - Output monitoring for long-running processes
    - Timeout handling
    """

    def __init__(
        self,
        working_dir: str | None = None,
        default_timeout: int = 30,
        max_sessions: int = 5,
        sandbox: bool = True,
    ):
        """
        Initialize code executor.

        Args:
            working_dir: Working directory for execution
            default_timeout: Default timeout in seconds
            max_sessions: Maximum concurrent sessions
            sandbox: Enable sandboxing restrictions
        """
        self.working_dir = working_dir or tempfile.gettempdir()
        self.default_timeout = default_timeout
        self.max_sessions = max_sessions
        self.sandbox = sandbox
        self._sessions: dict[int, ExecutionSession] = {}
        self._history: list[ExecutionResult] = []
        self._max_history = 100
        self._lock = threading.RLock()

    def _get_session(self, session_id: int) -> ExecutionSession:
        """Get or create a session."""
        if session_id not in self._sessions:
            if len(self._sessions) >= self.max_sessions:
                # Remove oldest idle session
                oldest = min(
                    (s for s in self._sessions.values() if s.state == ExecutionState.IDLE),
                    key=lambda s: s.last_activity,
                    default=None,
                )
                if oldest:
                    oldest.reset()
                    del self._sessions[oldest.session_id]

            self._sessions[session_id] = ExecutionSession(session_id)

        return self._sessions[session_id]

    def execute(
        self,
        code: str,
        runtime: Runtime = Runtime.PYTHON,
        session_id: int = 0,
        timeout: int | None = None,
        env: dict | None = None,
    ) -> ExecutionResult:
        """
        Execute code in the specified runtime.

        Args:
            code: Code to execute
            runtime: Execution runtime
            session_id: Session ID for persistent state
            timeout: Execution timeout
            env: Additional environment variables

        Returns:
            ExecutionResult with output
        """
        result = ExecutionResult(
            runtime=runtime,
            code=code,
            session_id=session_id,
        )

        session = self._get_session(session_id)

        # Handle special runtimes
        if runtime == Runtime.OUTPUT:
            return self._get_output(session, result)
        elif runtime == Runtime.RESET:
            return self._reset_session(session, result)

        # Execute code
        result.started_at = datetime.utcnow()
        session.state = ExecutionState.RUNNING
        session.last_activity = datetime.utcnow()

        try:
            if runtime == Runtime.PYTHON:
                self._execute_python(code, result, timeout or self.default_timeout, env)
            elif runtime == Runtime.NODEJS:
                self._execute_nodejs(code, result, timeout or self.default_timeout, env)
            elif runtime == Runtime.TERMINAL:
                self._execute_terminal(code, result, timeout or self.default_timeout, env)
            else:
                result.error = f"Unknown runtime: {runtime}"
                result.state = ExecutionState.FAILED

        except subprocess.TimeoutExpired:
            result.state = ExecutionState.TIMEOUT
            result.error = f"Execution timed out after {timeout or self.default_timeout}s"
        except Exception as e:
            result.state = ExecutionState.FAILED
            result.error = str(e)
            logger.error(f"Execution error: {e}")

        result.completed_at = datetime.utcnow()
        session.state = ExecutionState.IDLE

        # Add to history
        with self._lock:
            self._history.append(result)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history // 2 :]

        return result

    def _execute_python(
        self,
        code: str,
        result: ExecutionResult,
        timeout: int,
        env: dict | None,
    ) -> None:
        """Execute Python code."""
        # Write code to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".py", delete=False, dir=self.working_dir
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Build environment
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)

            # Execute
            proc = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir,
                env=exec_env,
            )

            result.stdout = proc.stdout
            result.stderr = proc.stderr
            result.return_code = proc.returncode
            result.state = ExecutionState.COMPLETED

        finally:
            # Cleanup temp file
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def _execute_nodejs(
        self,
        code: str,
        result: ExecutionResult,
        timeout: int,
        env: dict | None,
    ) -> None:
        """Execute Node.js code."""
        # Write code to temp file
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".js", delete=False, dir=self.working_dir
        ) as f:
            f.write(code)
            temp_file = f.name

        try:
            exec_env = os.environ.copy()
            if env:
                exec_env.update(env)

            proc = subprocess.run(
                ["node", temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.working_dir,
                env=exec_env,
            )

            result.stdout = proc.stdout
            result.stderr = proc.stderr
            result.return_code = proc.returncode
            result.state = ExecutionState.COMPLETED

        finally:
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def _execute_terminal(
        self,
        code: str,
        result: ExecutionResult,
        timeout: int,
        env: dict | None,
    ) -> None:
        """Execute terminal command."""
        if self.sandbox:
            # Basic sandboxing - block dangerous commands
            dangerous = ["rm -rf /", "mkfs", ":(){:|:&};:", "dd if=/dev/zero"]
            for cmd in dangerous:
                if cmd in code:
                    result.state = ExecutionState.FAILED
                    result.error = "Potentially dangerous command blocked"
                    return

        exec_env = os.environ.copy()
        if env:
            exec_env.update(env)

        proc = subprocess.run(
            code,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=self.working_dir,
            env=exec_env,
        )

        result.stdout = proc.stdout
        result.stderr = proc.stderr
        result.return_code = proc.returncode
        result.state = ExecutionState.COMPLETED

    def _get_output(
        self,
        session: ExecutionSession,
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Get output from a session."""
        stdout, stderr = session.get_output()
        result.stdout = stdout
        result.stderr = stderr
        result.state = ExecutionState.COMPLETED
        result.return_code = 0
        result.completed_at = datetime.utcnow()
        return result

    def _reset_session(
        self,
        session: ExecutionSession,
        result: ExecutionResult,
    ) -> ExecutionResult:
        """Reset a session."""
        session.reset()
        result.stdout = "Session reset successfully"
        result.state = ExecutionState.COMPLETED
        result.return_code = 0
        result.completed_at = datetime.utcnow()
        return result

    def get_history(
        self,
        runtime: Runtime | None = None,
        session_id: int | None = None,
        limit: int = 20,
    ) -> list[ExecutionResult]:
        """Get execution history."""
        with self._lock:
            history = self._history

            if runtime:
                history = [r for r in history if r.runtime == runtime]
            if session_id is not None:
                history = [r for r in history if r.session_id == session_id]

            return history[-limit:]

    def get_stats(self) -> dict:
        """Get executor statistics."""
        with self._lock:
            runtimes = {}
            success_count = 0
            total_duration = 0
            completed = 0

            for result in self._history:
                r = result.runtime.value
                runtimes[r] = runtimes.get(r, 0) + 1
                if result.success:
                    success_count += 1
                if result.duration_seconds:
                    total_duration += result.duration_seconds
                    completed += 1

            return {
                "total_executions": len(self._history),
                "success_count": success_count,
                "success_rate": success_count / len(self._history) if self._history else 0,
                "avg_duration": total_duration / completed if completed else 0,
                "by_runtime": runtimes,
                "active_sessions": len(self._sessions),
            }

    def cleanup_sessions(self, max_idle_seconds: int = 3600) -> int:
        """Clean up idle sessions."""
        now = datetime.utcnow()
        cleaned = 0

        with self._lock:
            to_remove = []
            for session_id, session in self._sessions.items():
                if session.state == ExecutionState.IDLE:
                    idle_time = (now - session.last_activity).total_seconds()
                    if idle_time > max_idle_seconds:
                        session.reset()
                        to_remove.append(session_id)

            for session_id in to_remove:
                del self._sessions[session_id]
                cleaned += 1

        return cleaned
