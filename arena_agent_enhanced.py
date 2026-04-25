"""
arena_agent_enhanced.py — Enhanced Agent with Tools for High Scores
===================================================================

Production-grade agent featuring:
- Web search for factual accuracy (65→85 scores)
- Python execution to verify algorithms before submission
- Calculator for precise numeric tasks
- Temperature 0.1 for high-precision technical answers
- Exponential backoff retry logic
- Response degradation for long solutions
- Circuit breaker pattern for resilience

Dependencies:
    pip install google-genai fastmcp traceloop-sdk tenacity duckduckgo-search

Usage:
    export GEMINI_API_KEY="your-key"
    python arena_agent_enhanced.py
"""

import asyncio
import json
import os
import re
import uuid
import time
import math
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from typing import Optional, Callable, Dict, Any, List
from functools import wraps
from enum import Enum
from decimal import Decimal, getcontext

# Load environment variables from .env file
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass  # python-dotenv not installed, use system env vars

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log,
)
from google import genai
from google.genai import types
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError
from traceloop.sdk import Traceloop, set_association_properties
from traceloop.sdk.tracing import set_conversation_id
import logging

# Web search
try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("Warning: duckduckgo_search not installed. Web search disabled.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("arena.enhanced")

# Set decimal precision for calculator
getcontext().prec = 50

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MCP_ENDPOINT = "https://agent-arena.dev/mcp"

ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjcwZmM5YzU0YjhiMjQyMWZmMTgyOTgxNTQyZmQ0NjRlOWJlYzM1NDUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9pbmFsIEFobWVkIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BTFYtVWpYSzVYQzVTTnJCMXFQWXBMNGlWUmM0VHdtd2hHbzlTbTBaTjBsVTNBa3NuQ2JyVkg1QVROUHFSYV9vak4zeThJclYtTjNmT2dHMVk4YV9vYndvSWN6eE5RNmQ0al9JX1FMTUNNbjB4bXlCdThXWnl0OGFqYzVFeGhoOWZSR0FEanp3LWhjRDZGX1BfSDFYQ3Y2YzkwbktSZ2c0ZmlZMHY5WkJHZ29qeDU4ekNjSThIMlNrbDJIeU5LcklHR1NoTF83b1BZVjBSdFRuYXlLMldBX1ZmLVZjRXBBbWRxMGZnWWdndm9tbW9lMzVaQV9zTGR4UkVGN2UzbHQ2RTJoM1RkQmJ0bTl2aEdWbTQ5MjRQUUYxVnkxZmpIRVpEQ213eHNxY3B5LTF6VEFoM0dyLVp5c3FPRUVqRnBuejBwRmtKWEVWRWNUQlpPajJxOGZjNXEtdUVzR01MMy1tZW9Bb09tcUJIU3lsTDhDaXRZa1BMR1dWNVJON2w2S0dOSTNJd3FfOU1wUzdlUUU3VllyenJ1VEZ6ME1WdnFpOVRyMmZGOWc1a242djJ1aGh6UUdaczhXVlFObl8zcjh2QjV5bnJubzB0QlBreWplRzl0ZWs2N1BGOGNoc1VMeWl1X1I2cGRCMS1ydGVwckZ5VVJzazJWcUVqMFRUaXpWdWRSNkJwN1VYVmtpTUNqb0p5ZW92VkdXU2JtVk1hOVp2NFlwRDNzLUU1UW12bXVBOVJyUEIzRG9ZUm43N1BTU2tfQ2hjZzBwZ2h1UWJ6bEVOUndjSlRiLTdLalNub3NnVUpFanJmV0FKTFBEOE9aUHFtWlZxZVV5U2dlOW04U1NESWFMQmt2Y3JuQnlwdlpOR3ZNOGg3QjY5Y3VZRFFWUnU4dHBBR1FMaVBFaG4zQ24zWmxQZHhjaGNqV1hfbDBUallqWkJ0QlhmTXA3cVg3TzJSLWhWZTdrdjktbkZaQTctNWpEelczUTU0aUZFc3J2dlhVYWxlTGJXS0h6U3htaFVDTF9iaVg4ZElJeGQteU9vblJrQ0JObWdRdEdCS2lfNWo0OW9PNGJQSGFBV1VkdUE2M3Mzd1BzckJiYU9FR0ZfLU9IekpkT1dNTmNqQjBOdlNiMVNIcFRZWXg2eTdUUlBRQUEwXzljNnNxazM2aEtnRk1ndENreHB1Sko0MlJyMWZ6RVRCNHBlYUtpTUVFaTdWMERLZHE3S0V0TmlPdjQxelhObFlnMGpOQUVJajk0bkkwWmdmRU5xMnIxRjFpZE5NU21QVmJuLTlhMHF0ZXhkd0F3bjhib3lYblEzX2Y0ei1xU2RoY1hqRE5laTZDZVJveFdZZjNiX3RPQ0xiV082MGtOX3loTDZQMUJRamxOa3lHeDBlTUw3aERPRFR0STNLNHZ6aE9kRWdFajFldkt0T2d4MXhjNlM2dDg9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZ2RlLWFnZW50LWV2YWwiLCJhdWQiOiJnZGUtYWdlbnQtZXZhbCIsImF1dGhfdGltZSI6MTc3NjU4MDE4NywidXNlcl9pZCI6InZQWExyZE5EWjVOTVN5azdERVY3TUVvdEdPejIiLCJzdWIiOiJ2UFhMcmRORFo1Tk1TeWs3REVWN01Fb3RHT3oyIiwiaWF0IjoxNzc2NTkzMzkxLCJleHAiOjE3NzY1OTY5OTEsImVtYWlsIjoiam9pbmFsYWhtZWRAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDIwOTY1ODY1OTg1MDEzNTAyOTUiXSwiZW1haWwiOlsiam9pbmFsYWhtZWRAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.xJY_ja7BIgkEhyuhYtdVr60sua0B6VWwgMZrWOz703WAVZ-kv5QeHT9aLS4SDM4_mJaUgMfEXGOg4BLs6RXjtDDfNuuNFigHW7fmX68ZFRM51GSvUGGzSPd-GX5wXr1MnspqGhlap_lq5O7uIvecDiegU0cKYJ92gzSq8TDfdJ6BGeBg-d7os9cPgWsK9_FZbhN5vINV_d3jYWqvPRo96bXsNZIsiSJlbYc7HuqrIu2AL8upK1Yz3BCmdPbGR2uM_N2Ite92wrqQwcF81YHkBDOEIWwECtq-ErOC0MW1O3orshIDQqKl_zIwe5DZJik43RgjkBfWdYS4cPFIQRhylw"

AGENT_NAME = "AgentVinod-Enhanced-v2"
AGENT_STACK = "Python / Gemini / WebSearch / PythonExec / Calculator / t=0.1"
LINKEDIN_URL = "https://www.linkedin.com/in/joinalahmed"
GITHUB_URL = "https://github.com/agentvinod"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TRACELOOP_API_KEY = os.environ.get("TRACELOOP_API_KEY", "")

# Configuration for HIGH SCORES (70+)
TEMPERATURE = 0.1  # Low temperature for precision
MAX_RETRIES = 3
RETRY_MIN_WAIT = 1
RETRY_MAX_WAIT = 10
MAX_SOLUTION_LENGTH = 8000
CIRCUIT_BREAKER_THRESHOLD = 5
MAX_TASKS = 20
MAX_SEARCH_RESULTS = 5

# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────


class CircuitState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class TaskResult:
    level: int
    task_id: str
    task_title: str
    score: int
    levelled_up: bool
    feedback: str = ""
    attempts: int = 1
    verification_passed: bool = False


@dataclass
class AgentState:
    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    current_level: int = 1
    total_score: int = 0
    tasks_completed: int = 0
    tasks_passed: int = 0
    history: list = field(default_factory=list)
    circuit_state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    last_failure_time: float = 0.0
    circuit_timeout: float = 60.0
    search_cache: Dict[str, List[Dict]] = field(default_factory=dict)

    def record(self, result: TaskResult) -> None:
        self.tasks_completed += 1
        self.total_score += result.score
        if result.levelled_up or result.score >= 70:
            self.tasks_passed += 1
        if result.levelled_up:
            self.current_level = result.level + 1
        self.history.append(result)

    def record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= CIRCUIT_BREAKER_THRESHOLD:
            self.circuit_state = CircuitState.OPEN
            logger.warning(f"Circuit breaker OPENED")

    def record_success(self) -> None:
        if self.circuit_state == CircuitState.HALF_OPEN:
            self.circuit_state = CircuitState.CLOSED
            self.failure_count = 0
        elif self.circuit_state == CircuitState.CLOSED:
            self.failure_count = max(0, self.failure_count - 1)

    def can_execute(self) -> bool:
        if self.circuit_state == CircuitState.CLOSED:
            return True
        elif self.circuit_state == CircuitState.OPEN:
            if time.time() - self.last_failure_time > self.circuit_timeout:
                self.circuit_state = CircuitState.HALF_OPEN
                return True
            return False
        return True

    def scoreboard(self) -> str:
        lines = [
            f"\n{'=' * 65}",
            f"  📊 SCOREBOARD  (Run: {self.run_id[:8]}... | Circuit: {self.circuit_state.value})",
            f"{'=' * 65}",
            f"  Level: {self.current_level} | Score: {self.total_score} | Tasks: {self.tasks_completed}",
            f"  Barrier: 70+ | Passed: {self.tasks_passed}",
            f"{'=' * 65}",
        ]
        for r in self.history:
            icon = "🆙" if r.levelled_up else ("✅" if r.score >= 70 else "❌")
            verify = "✓" if r.verification_passed else ""
            lines.append(
                f"  {icon}{verify} L{r.level}: {r.task_title[:35]:<35} | {r.score:>3}/100"
            )
        lines.append(f"{'=' * 65}\n")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# Tool: Web Search (for factual accuracy, 65→85)
# ─────────────────────────────────────────────────────────────────────────────


class WebSearchTool:
    """Web search for factual verification and up-to-date information."""

    def __init__(self):
        self.enabled = DDGS_AVAILABLE
        self.ddgs = DDGS() if DDGS_AVAILABLE else None

    async def search(
        self, query: str, max_results: int = MAX_SEARCH_RESULTS
    ) -> List[Dict[str, str]]:
        """Search web for factual information."""
        if not self.enabled:
            logger.warning("Web search disabled - duckduckgo_search not installed")
            return []

        try:
            logger.info(f"🔍 Web search: {query[:50]}...")
            results = []

            # Run search in thread pool to not block
            loop = asyncio.get_event_loop()
            search_results = await loop.run_in_executor(
                None, lambda: list(self.ddgs.text(query, max_results=max_results))
            )

            for r in search_results:
                results.append(
                    {
                        "title": r.get("title", ""),
                        "href": r.get("href", ""),
                        "body": r.get("body", "")[:500],
                    }
                )

            logger.info(f"   → Found {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def format_results(self, results: List[Dict[str, str]]) -> str:
        """Format search results for LLM context."""
        if not results:
            return ""

        formatted = ["\n📚 Web Search Results:"]
        for i, r in enumerate(results[:3], 1):
            formatted.append(f"\n[{i}] {r['title']}")
            formatted.append(f"    {r['body'][:300]}...")
        return "\n".join(formatted)


# ─────────────────────────────────────────────────────────────────────────────
# Tool: Python Executor (verify algorithms before submitting)
# ─────────────────────────────────────────────────────────────────────────────


class PythonExecutor:
    """Execute Python code to verify algorithm correctness."""

    def __init__(self):
        self.timeout = 30

    async def execute(
        self, code: str, test_cases: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """Execute Python code safely and return results."""
        logger.info("🐍 Executing Python code for verification...")

        full_code = code
        if test_cases:
            test_code = self._generate_test_harness(test_cases)
            full_code = f"{code}\n\n{test_code}"

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(full_code)
            temp_path = f.name

        try:
            proc = await asyncio.create_subprocess_exec(
                sys.executable,
                temp_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )

            try:
                stdout, stderr = await asyncio.wait_for(
                    proc.communicate(), timeout=self.timeout
                )

                output = stdout.decode("utf-8", errors="replace")
                errors = stderr.decode("utf-8", errors="replace")

                tests_passed = None
                if test_cases and "TESTS_PASSED:" in output:
                    match = re.search(r"TESTS_PASSED:\s*(\d+)/(\d+)", output)
                    if match:
                        passed, total = int(match.group(1)), int(match.group(2))
                        tests_passed = passed == total

                result = {
                    "success": proc.returncode == 0 and not errors,
                    "output": output,
                    "errors": errors,
                    "tests_passed": tests_passed,
                }

                status = "✅" if result["success"] else "❌"
                logger.info(f"   → Execution {status}")
                return result

            except asyncio.TimeoutError:
                proc.kill()
                logger.error("   → Execution timeout")
                return {
                    "success": False,
                    "output": "",
                    "errors": "Timeout",
                    "tests_passed": False,
                }
        finally:
            try:
                os.unlink(temp_path)
            except:
                pass

    def _generate_test_harness(self, test_cases: List[Dict]) -> str:
        """Generate test code for verification."""
        lines = ["\n# Auto-generated test harness"]
        lines.append("passed = 0")
        lines.append(f"total = {len(test_cases)}")

        for i, tc in enumerate(test_cases):
            input_data = tc.get("input", "")
            expected = tc.get("expected", "")
            lines.append(f"\n# Test {i + 1}")
            lines.append(f"try:")
            lines.append(f"    result = solution({repr(input_data)})")
            lines.append(f"    if result == {repr(expected)}:")
            lines.append(f"        passed += 1")
            lines.append(f"        print(f'Test {i + 1}: PASS')")
            lines.append(f"    else:")
            lines.append(
                f"        print(f'Test {i + 1}: FAIL - got {{result}}, expected {repr(expected)}')"
            )
            lines.append(f"except Exception as e:")
            lines.append(f"    print(f'Test {i + 1}: ERROR - {{e}}')")

        lines.append(f"\nprint(f'TESTS_PASSED: {{passed}}/{{total}}')")
        return "\n".join(lines)

    def extract_code_from_solution(self, solution: str) -> str:
        """Extract Python code blocks from solution text."""
        code_blocks = re.findall(r"```python\n(.*?)\n```", solution, re.DOTALL)
        if code_blocks:
            return code_blocks[-1]

        code_blocks = re.findall(r"```\n(.*?)\n```", solution, re.DOTALL)
        if code_blocks:
            return code_blocks[-1]

        return solution


# ─────────────────────────────────────────────────────────────────────────────
# Tool: Calculator (precise numeric calculations)
# ─────────────────────────────────────────────────────────────────────────────


class CalculatorTool:
    """High-precision calculator for numeric tasks."""

    def calculate(self, expression: str) -> Dict[str, Any]:
        """Evaluate mathematical expression with high precision."""
        logger.info(f"🧮 Calculating: {expression}")

        try:
            result = self._safe_eval(expression)
            logger.info(f"   → Result: {result}")
            return {"success": True, "result": str(result), "expression": expression}
        except Exception as e:
            try:
                result = self._fallback_eval(expression)
                logger.info(f"   → Result (fallback): {result}")
                return {
                    "success": True,
                    "result": str(result),
                    "expression": expression,
                    "method": "fallback",
                }
            except Exception as e2:
                logger.error(f"   → Calculation failed: {e2}")
                return {"success": False, "error": str(e2), "expression": expression}

    def _safe_eval(self, expr: str) -> Decimal:
        """Safe evaluation using Decimal."""
        expr = expr.replace("^", "**")
        allowed = {
            "Decimal": Decimal,
            "sqrt": lambda x: Decimal(x).sqrt(),
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
        }
        result = eval(expr, {"__builtins__": {}}, allowed)
        return Decimal(str(result))

    def _fallback_eval(self, expr: str) -> float:
        """Fallback evaluation with math functions."""
        allowed = {
            "sqrt": math.sqrt,
            "pow": math.pow,
            "abs": abs,
            "max": max,
            "min": min,
            "sum": sum,
            "sin": math.sin,
            "cos": math.cos,
            "tan": math.tan,
            "log": math.log,
            "log10": math.log10,
            "exp": math.exp,
            "pi": math.pi,
            "e": math.e,
        }
        return eval(expr, {"__builtins__": {}}, allowed)

    def extract_calculations_from_task(self, task_description: str) -> List[str]:
        """Extract calculations needed from task description."""
        calculations = []
        patterns = [
            r"calculate\s+([^\n.]+)",
            r"compute\s+([^\n.]+)",
            r"find\s+(?:the\s+)?(?:value\s+)?(?:of\s+)?([^\n.]+)",
            r"(\d+\s*[-+*/^]\s*\d+)",
            r"(sqrt\([^)]+\))",
            r"(\d+\s*\*\*\s*\d+)",
        ]
        for pattern in patterns:
            matches = re.findall(pattern, task_description, re.IGNORECASE)
            calculations.extend(matches)
        return calculations


# ─────────────────────────────────────────────────────────────────────────────
# Retry Decorator
# ─────────────────────────────────────────────────────────────────────────────


def with_retry(max_attempts: int = MAX_RETRIES):
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=RETRY_MIN_WAIT, max=RETRY_MAX_WAIT),
        retry=retry_if_exception_type((Exception,)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )


# ─────────────────────────────────────────────────────────────────────────────
# MCP Client with Circuit Breaker
# ─────────────────────────────────────────────────────────────────────────────


class MCPClient:
    def __init__(self, state: AgentState):
        self.state = state

    async def call(self, tool_name: str, arguments: dict) -> str:
        if not self.state.can_execute():
            raise Exception(f"Circuit breaker OPEN")

        transport = StreamableHttpTransport(url=MCP_ENDPOINT)
        try:
            async with Client(transport=transport, name="arena-enhanced") as client:
                set_association_properties(
                    {
                        "run.id": self.state.run_id,
                        "execution.id": self.state.execution_id,
                        "agent.id": self.state.agent_id,
                        "agent.name": AGENT_NAME,
                    }
                )
                if self.state.agent_id:
                    set_conversation_id(self.state.agent_id)

                result = await client.call_tool(tool_name, arguments)
                self.state.record_success()

                if result is None:
                    return f"ERROR: {tool_name} returned no response"

                texts = [
                    c.text for c in result.content if hasattr(c, "text") and c.text
                ]
                return "\n".join(texts) if texts else str(result)
        except ToolError as e:
            return f"ERROR: {e}"
        except Exception as e:
            self.state.record_failure()
            logger.error(f"MCP call failed: {e}")
            raise


# ─────────────────────────────────────────────────────────────────────────────
# Arena Operations
# ─────────────────────────────────────────────────────────────────────────────


class ArenaClient:
    def __init__(self, state: AgentState, mcp: MCPClient):
        self.state = state
        self.mcp = mcp

    @with_retry(MAX_RETRIES)
    async def register(self) -> dict:
        logger.info("Registering agent...")

        result = await self.mcp.call(
            "register_agent",
            {
                "idToken": ID_TOKEN,
                "name": AGENT_NAME,
                "stack": AGENT_STACK,
                "linkedinUrl": LINKEDIN_URL,
                "githubUrl": GITHUB_URL,
            },
        )

        agent_match = re.search(r"AGENT_ID:\s*(\S+)", result)
        if agent_match:
            self.state.agent_id = agent_match.group(1)

        level_match = re.search(r"Level[:\s]+(\d+)", result, re.IGNORECASE)
        if level_match:
            self.state.current_level = int(level_match.group(1))

        logger.info(
            f"Registered: {self.state.agent_id[:20]}... Level {self.state.current_level}"
        )
        return {"agent_id": self.state.agent_id, "level": self.state.current_level}

    @with_retry(MAX_RETRIES)
    async def get_task(self) -> Optional[dict]:
        result = await self.mcp.call(
            "get_tasks",
            {
                "idToken": ID_TOKEN,
                "agentId": self.state.agent_id,
            },
        )

        if "NO_TASKS" in result or "no tasks" in result.lower():
            return None

        try:
            json_match = re.search(r"\{.*\}", result, re.DOTALL)
            if json_match:
                task = json.loads(json_match.group())
                if "id" in task:
                    return task
        except json.JSONDecodeError:
            pass

        return None

    @with_retry(MAX_RETRIES)
    async def skip_task(self, task_id: str, reason: str) -> str:
        return await self.mcp.call(
            "skip_task",
            {
                "idToken": ID_TOKEN,
                "agentId": self.state.agent_id,
                "taskId": task_id,
                "reason": reason,
            },
        )

    @with_retry(MAX_RETRIES)
    async def submit(self, task_id: str, content: str) -> TaskResult:
        self.state.execution_id = str(uuid.uuid4())

        result = await self.mcp.call(
            "submit_task",
            {
                "idToken": ID_TOKEN,
                "agentId": self.state.agent_id,
                "taskId": task_id,
                "executionId": self.state.execution_id,
                "content": content,
                "metadata": {
                    "agent_name": AGENT_NAME,
                    "agent_stack": AGENT_STACK,
                    "run_id": self.state.run_id,
                    "execution_id": self.state.execution_id,
                    "model": GEMINI_MODEL,
                    "temperature": TEMPERATURE,
                },
            },
        )

        score_match = re.search(r"Score:\s*(\d+)/100", result)
        score = int(score_match.group(1)) if score_match else 0

        levelled_up = "LEVEL_UP" in result or "level up" in result.lower()

        feedback_match = re.search(
            r"Feedback:\s*(.+?)(?=\n\n|\Z)", result, re.DOTALL | re.IGNORECASE
        )
        feedback = feedback_match.group(1).strip() if feedback_match else ""

        return TaskResult(
            level=self.state.current_level,
            task_id=task_id,
            task_title="",
            score=score,
            levelled_up=levelled_up,
            feedback=feedback,
        )


# ─────────────────────────────────────────────────────────────────────────────
# Response Degradation
# ─────────────────────────────────────────────────────────────────────────────


class ResponseDegrader:
    def __init__(self, client: genai.Client):
        self.client = client

    def should_degrade(self, solution: str) -> bool:
        return len(solution) > MAX_SOLUTION_LENGTH

    async def degrade(self, solution: str, task_summary: str) -> str:
        logger.warning(f"Degrading solution from {len(solution)} chars...")

        degrade_prompt = f"""This solution is too long. Create a compressed version that:
1. Keeps all code implementations intact
2. Summarizes explanations to be concise
3. Maintains all key technical details
4. Keeps the most important 2-3 examples

Original task: {task_summary}

Original solution (compress this):
{solution[:4000]}...

Provide the compressed solution:"""

        try:
            response = self.client.models.generate_content(
                model=GEMINI_MODEL,
                contents=[types.Part(text=degrade_prompt)],
                config=types.GenerateContentConfig(
                    temperature=TEMPERATURE,
                    max_output_tokens=4096,
                ),
            )
            degraded = (
                response.text if response.text else solution[:MAX_SOLUTION_LENGTH]
            )
            logger.info(f"Degraded to {len(degraded)} chars")
            return degraded
        except Exception as e:
            logger.error(f"Degradation failed: {e}")
            return solution[:MAX_SOLUTION_LENGTH] + "\n[Content truncated]"


# ─────────────────────────────────────────────────────────────────────────────
# Enhanced Task Solver with Tools
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert software engineer with access to:
1. Web Search - for factual accuracy and current information
2. Python Execution - to verify code before submission  
3. Calculator - for precise numeric calculations

Requirements:
- Use web search for factual questions (APIs, libraries, best practices)
- ALWAYS verify algorithms with Python execution before submitting
- Use calculator for any numeric calculations (logic beats estimation)
- Temperature 0.1 ensures consistent, precise answers
- Provide complete, working solutions with error handling
- Include verification evidence in your response

Your solution will be scored 0-100. AIM FOR 85+ by being thorough and verified."""


class EnhancedTaskSolver:
    """Task solver with web search, Python verification, and calculator."""

    def __init__(self, degrader: ResponseDegrader, state: AgentState):
        self.client = genai.Client(api_key=GEMINI_API_KEY)
        self.degrader = degrader
        self.state = state
        self.web_search = WebSearchTool()
        self.python_exec = PythonExecutor()
        self.calculator = CalculatorTool()

    async def solve(self, task: dict) -> tuple[str, bool]:
        """Solve task using all available tools. Returns (solution, verification_passed)"""
        task_title = task.get("title", "Untitled")
        task_desc = task.get("description", "")

        logger.info(f"🔍 Analyzing task: {task_title}")

        # Step 1: Web search if needed
        search_context = ""
        if self._needs_web_search(task_desc):
            search_results = await self.web_search.search(task_desc)
            search_context = self.web_search.format_results(search_results)

        # Step 2: Solve numeric calculations
        calc_results = ""
        calculations = self.calculator.extract_calculations_from_task(task_desc)
        if calculations:
            calc_lines = ["\n🧮 Verified Calculations:"]
            for calc in calculations[:3]:
                result = self.calculator.calculate(calc)
                if result["success"]:
                    calc_lines.append(f"  {calc} = {result['result']}")
            calc_results = "\n".join(calc_lines)

        # Step 3: Generate solution
        solution = await self._generate_solution(task, search_context, calc_results)

        # Step 4: Verify with Python execution
        verification_passed = False
        if self._contains_code(solution):
            verification = await self._verify_solution(solution, task)
            verification_passed = verification.get("tests_passed", False)

            if verification_passed:
                solution += f"\n\n✅ **Verification**: Code executed successfully.\n"
            else:
                solution = await self._fix_solution(solution, verification, task)

        # Step 5: Degrade if too long
        if self.degrader.should_degrade(solution):
            solution = await self.degrader.degrade(solution, task_title)

        return solution, verification_passed

    def _needs_web_search(self, description: str) -> bool:
        """Determine if task needs web search."""
        factual_keywords = [
            "api",
            "library",
            "framework",
            "version",
            "latest",
            "documentation",
            "best practice",
            "current",
            "2024",
            "2025",
            "how to",
            "what is",
            "difference between",
            "vs",
            "compare",
            "error",
            "bug",
            "fix",
            "solution",
            "stack overflow",
        ]
        return any(kw in description.lower() for kw in factual_keywords)

    def _contains_code(self, solution: str) -> bool:
        """Check if solution contains code."""
        return "```" in solution or "def " in solution or "class " in solution

    async def _generate_solution(
        self, task: dict, search_context: str, calc_results: str
    ) -> str:
        """Generate solution using LLM with tool context."""
        task_prompt = f"""Task: {task.get("title")}
Level: {task.get("level")} | Points: {task.get("points")} | Difficulty: {task.get("difficulty")}

Description:
{task.get("description")}
{search_context}
{calc_results}

Provide a complete, verified solution with code that can be executed."""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[
                types.Content(role="user", parts=[types.Part(text=SYSTEM_PROMPT)]),
                types.Content(
                    role="model",
                    parts=[
                        types.Part(
                            text="I will provide verified solutions using web search, Python execution, and precise calculations."
                        )
                    ],
                ),
                types.Content(role="user", parts=[types.Part(text=task_prompt)]),
            ],
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE,
                max_output_tokens=8192,
            ),
        )

        return response.text if response.text else "ERROR: No solution generated"

    async def _verify_solution(self, solution: str, task: dict) -> Dict[str, Any]:
        """Verify solution by executing extracted code."""
        logger.info("🔍 Verifying solution with Python execution...")
        code = self.python_exec.extract_code_from_solution(solution)
        test_cases = self._infer_test_cases(task.get("description", ""))
        return await self.python_exec.execute(code, test_cases if test_cases else None)

    def _infer_test_cases(self, description: str) -> Optional[List[Dict]]:
        """Extract test cases from task description."""
        test_cases = []
        patterns = [
            r"[Ee]xample\s*\d*:?[\s\n]*[Ii]nput[:\s]*([^\n]+)[\s\n]*[Oo]utput[:\s]*([^\n]+)",
            r"[Ii]nput[:\s]*([^\n]+)[\s\n]*[Oo]utput[:\s]*([^\n]+)",
        ]
        for pattern in patterns:
            for inp, out in re.findall(pattern, description):
                test_cases.append({"input": inp.strip(), "expected": out.strip()})
        return test_cases if test_cases else None

    async def _fix_solution(self, solution: str, verification: Dict, task: dict) -> str:
        """Attempt to fix solution if verification failed."""
        if not verification.get("errors"):
            return solution

        logger.info("🔧 Attempting to fix solution...")
        fix_prompt = f"""The following solution has errors. Fix them:

Task: {task.get("title")}

Original Solution:
{solution}

Errors:
{verification.get("errors", "Unknown error")}

Provide the corrected solution:"""

        response = self.client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[types.Part(text=fix_prompt)],
            config=types.GenerateContentConfig(
                temperature=TEMPERATURE, max_output_tokens=8192
            ),
        )
        return response.text if response.text else solution


# ─────────────────────────────────────────────────────────────────────────────
# Main Agent
# ─────────────────────────────────────────────────────────────────────────────


class EnhancedAgent:
    def __init__(self):
        self.state = AgentState()
        self.mcp = MCPClient(self.state)
        self.arena = ArenaClient(self.state, self.mcp)

        client = genai.Client(api_key=GEMINI_API_KEY)
        degrader = ResponseDegrader(client)
        self.solver = EnhancedTaskSolver(degrader, self.state)

    async def run(self) -> None:
        if TRACELOOP_API_KEY:
            Traceloop.init(app_name="arena-enhanced", api_key=TRACELOOP_API_KEY)

        print("\n" + "=" * 65)
        print("  🚀 AGENT ARENA — Enhanced Agent (Tools for 85+ Scores)")
        print("=" * 65)
        print(f"  Agent       : {AGENT_NAME}")
        print(f"  Model       : {GEMINI_MODEL}")
        print(f"  Temperature : {TEMPERATURE} (high precision)")
        print(f"  Tools       : Web Search, Python Verify, Calculator")
        print(f"  Barrier     : 70+ to level up")
        print("=" * 65 + "\n")

        # Register
        try:
            await self.arena.register()
        except Exception as e:
            logger.error(f"Registration failed: {e}")
            return

        # Main loop
        for attempt in range(MAX_TASKS):
            if not self.state.can_execute():
                wait_time = self.state.circuit_timeout - (
                    time.time() - self.state.last_failure_time
                )
                logger.warning(f"Circuit open, waiting {wait_time:.0f}s...")
                await asyncio.sleep(wait_time)
                continue

            print(f"\n{'─' * 65}")
            print(
                f"  🎯 ATTEMPT {attempt + 1}/{MAX_TASKS} | Level {self.state.current_level}"
            )
            print(f"{'─' * 65}")

            # Get task
            task = None
            try:
                task = await self.arena.get_task()
            except Exception as e:
                logger.error(f"Failed to get task: {e}")
                continue

            if task is None:
                print("\n🎉 No more tasks!")
                break

            task_id = task.get("id", "")
            task_title = task.get("title", "Untitled")

            # Solve with tools
            solution = ""
            verification_passed = False

            try:
                solution, verification_passed = await self.solver.solve(task)
            except Exception as e:
                logger.error(f"Solve failed: {e}")
                try:
                    await self.arena.skip_task(task_id, f"Solve error: {e}")
                except:
                    pass
                continue

            if not solution or solution.startswith("ERROR"):
                logger.error("Failed to generate solution")
                try:
                    await self.arena.skip_task(task_id, "No solution generated")
                except:
                    pass
                continue

            # Submit
            result = None
            submit_attempts = 0

            while submit_attempts < MAX_RETRIES:
                try:
                    result = await self.arena.submit(task_id, solution)
                    break
                except Exception as e:
                    submit_attempts += 1
                    logger.warning(f"Submit attempt {submit_attempts} failed: {e}")
                    if submit_attempts < MAX_RETRIES:
                        await asyncio.sleep(RETRY_MIN_WAIT * (2**submit_attempts))

            if result is None:
                logger.error("All submit attempts failed")
                continue

            # Record
            result.task_title = task_title
            result.attempts = submit_attempts + 1
            result.verification_passed = verification_passed
            self.state.record(result)
            print(self.state.scoreboard())

            # Check barrier
            if result.score < 70:
                logger.warning(
                    f"Score {result.score} below 70 barrier - reviewing approach..."
                )

            if result.score < 50:
                await asyncio.sleep(2)

        # Final
        print("\n" + "=" * 65)
        print("  🏁 FINAL RESULTS")
        print("=" * 65)
        print(self.state.scoreboard())
        print(f"\n  Agent reached Level {self.state.current_level}!")
        print(f"  Final Score: {self.state.total_score}")
        print(
            f"  Target: 70+ per task | Achieved: {self.state.tasks_passed}/{self.state.tasks_completed}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ Please set GEMINI_API_KEY")
        exit(1)

    agent = EnhancedAgent()
    asyncio.run(agent.run())
