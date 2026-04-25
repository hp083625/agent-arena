"""
arena_agent_lightweight.py — Lightweight Async Agent Arena Agent
================================================================

A simplified autonomous agent that levels up through Agent Arena.
Uses direct Gemini API calls instead of a heavy framework.

Dependencies:
    pip install google-genai fastmcp traceloop-sdk

Usage:
    export GEMINI_API_KEY="your-key"
    python arena_agent_lightweight.py
"""

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional

from google import genai
from google.genai import types
from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from traceloop.sdk import Traceloop, set_association_properties
from traceloop.sdk.tracing import set_conversation_id

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MCP_ENDPOINT = "https://agent-arena.dev/mcp"

ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjcwZmM5YzU0YjhiMjQyMWZmMTgyOTgxNTQyZmQ0NjRlOWJlYzM1NDUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9pbmFsIEFobWVkIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BTFYtVWpYSzVYQzVTTnJCMXFQWXBMNGlWUmM0VHdtd2hHbzlTbTBaTjBsVTNBa3NuQ2JyVkg1QVROUHFSYV9vak4zeThJclYtTjNmT2dHMVk4YV9vYndvSWN6eE5RNmQ0al9JX1FMTUNNbjB4bXlCdThXWnl0OGFqYzVFeGhoOWZSR0FEanp3LWhjRDZGX1BfSDFYQ3Y2YzkwbktSZ2c0ZmlZMHY5WkJHZ29qeDU4ekNjSThIMlNrbDJIeU5LcklHR1NoTF83b1BZVjBSdFRuYXlLMldBX1ZmLVZjRXBBbWRxMGZnWWdndm9tbW9lMzVaQV9zTGR4UkVGN2UzbHQ2RTJoM1RkQmJ0bTl2aEdWbTQ5MjRQUUYxVnkxZmpIRVpEQ213eHNxY3B5LTF6VEFoM0dyLVp5c3FPRUVqRnBuejBwRmtKWEVWRWNUQlpPajJxOGZjNXEtdUVzR01MMy1tZW9Bb09tcUJIU3lsTDhDaXRZa1BMR1dWNVJON2w2S0dOSTNJd3FfOU1wUzdlUUU3VllyenJ1VEZ6ME1WdnFpOVRyMmZGOWc1a242djJ1aGh6UUdaczhXVlFObl8zcjh2QjV5bnJubzB0QlBreWplRzl0ZWs2N1BGOGNoc1VMeWl1X1I2cGRCMS1ydGVwckZ5VVJzazJWcUVqMFRUaXpWdWRSNkJwN1VYVmtpTUNqb0p5ZW92VkdXU2JtVk1hOVp2NFlwRDNzLUU1UW12bXVBOVJyUEIzRG9ZUm43N1BTU2tfQ2hjZzBwZ2h1UWJ6bEVOUndjSlRiLTdLalNub3NnVUpFanJmV0FKTFBEOE9aUHFtWlZxZVV5U2dlOW04U1NESWFMQmt2Y3JuQnlwdlpOR3ZNOGg3QjY5Y3VZRFFWUnU4dHBBR1FMaVBFaG4zQ24zWmxQZHhjaGNqV1hfbDBUallqWkJ0QlhmTXA3cVg3TzJSLWhWZTdrdjktbkZaQTctNWpEelczUTU0aUZFc3J2dlhVYWxlTGJXS0h6U3htaFVDTF9iaVg4ZElJeGQteU9vblJrQ0JObWdRdEdCS2lfNWo0OW9PNGJQSGFBV1VkdUE2M3Mzd1BzckJiYU9FR0ZfLU9IekpkT1dNTmNqQjBOdlNiMVNIcFRZWXg2eTdUUlBRQUEwXzljNnNxazM2aEtnRk1ndENreHB1Sko0MlJyMWZ6RVRCNHBlYUtpTUVFaTdWMERLZHE3S0V0TmlPdjQxelhObFlnMGpOQUVJajk0bkkwWmdmRU5xMnIxRjFpZE5NU21QVmJuLTlhMHF0ZXhkd0F3bjhib3lYblEzX2Y0ei1xU2RoY1hqRE5laTZDZVJveFdZZjNiX3RPQ0xiV082MGtOX3loTDZQMUJRamxOa3lHeDBlTUw3aERPRFR0STNLNHZ6aE9kRWdFajFldkt0T2d4MXhjNlM2dDg9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZ2RlLWFnZW50LWV2YWwiLCJhdWQiOiJnZGUtYWdlbnQtZXZhbCIsImF1dGhfdGltZSI6MTc3NjU4MDE4NywidXNlcl9pZCI6InZQWExyZE5EWjVOTVN5azdERVY3TUVvdEdPejIiLCJzdWIiOiJ2UFhMcmRORFo1Tk1TeWs3REVWN01Fb3RHT3oyIiwiaWF0IjoxNzc2NTkzMzkxLCJleHAiOjE3NzY1OTY5OTEsImVtYWlsIjoiam9pbmFsYWhtZWRAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDIwOTY1ODY1OTg1MDEzNTAyOTUiXSwiZW1haWwiOlsiam9pbmFsYWhtZWRAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.xJY_ja7BIgkEhyuhYtdVr60sua0B6VWwgMZrWOz703WAVZ-kv5QeHT9aLS4SDM4_mJaUgMfEXGOg4BLs6RXjtDDfNuuNFigHW7fmX68ZFRM51GSvUGGzSPd-GX5wXr1MnspqGhlap_lq5O7uIvecDiegU0cKYJ92gzSq8TDfdJ6BGeBg-d7os9cPgWsK9_FZbhN5vINV_d3jYWqvPRo96bXsNZIsiSJlbYc7HuqrIu2AL8upK1Yz3BCmdPbGR2uM_N2Ite92wrqQwcF81YHkBDOEIWwECtq-ErOC0MW1O3orshIDQqKl_zIwe5DZJik43RgjkBfWdYS4cPFIQRhylw"

AGENT_NAME = "AgentVinod-Lightweight-v1"
AGENT_STACK = "Python / Gemini Direct API / Async"
LINKEDIN_URL = "https://www.linkedin.com/in/joinalahmed"
GITHUB_URL = "https://github.com/agentvinod"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
TRACELOOP_API_KEY = os.environ.get("TRACELOOP_API_KEY", "")

MAX_TASKS = 20  # Safety limit

# ─────────────────────────────────────────────────────────────────────────────
# Data Models
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TaskResult:
    """Result of a single task attempt."""

    level: int
    task_id: str
    task_title: str
    score: int
    levelled_up: bool
    feedback: str = ""


@dataclass
class AgentState:
    """Tracks the agent's complete state."""

    run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    agent_id: str = ""
    current_level: int = 1
    total_score: int = 0
    tasks_completed: int = 0
    tasks_passed: int = 0
    history: list[TaskResult] = field(default_factory=list)

    def record(self, result: TaskResult) -> None:
        self.tasks_completed += 1
        self.total_score += result.score
        if result.levelled_up or result.score >= 70:
            self.tasks_passed += 1
        if result.levelled_up:
            self.current_level = result.level + 1
        self.history.append(result)

    def scoreboard(self) -> str:
        lines = [
            f"\n{'=' * 60}",
            f"  SCOREBOARD  (Run: {self.run_id[:8]}...)",
            f"{'=' * 60}",
            f"  Current Level   : {self.current_level}",
            f"  Total Score     : {self.total_score}",
            f"  Tasks Completed : {self.tasks_completed} (passed: {self.tasks_passed})",
            f"{'=' * 60}",
        ]
        for r in self.history:
            icon = "✅" if r.levelled_up else ("🟡" if r.score >= 70 else "❌")
            lines.append(
                f"  {icon} L{r.level}: {r.task_title[:40]:<40} | {r.score:>3}/100"
            )
        lines.append(f"{'=' * 60}\n")
        return "\n".join(lines)


# ─────────────────────────────────────────────────────────────────────────────
# MCP Client Helper
# ─────────────────────────────────────────────────────────────────────────────


async def mcp_call(tool_name: str, arguments: dict, state: AgentState) -> str:
    """Make a single MCP tool call with fresh session."""
    transport = StreamableHttpTransport(url=MCP_ENDPOINT)
    try:
        async with Client(transport=transport, name="arena-lightweight") as client:
            # Set tracing context
            set_association_properties(
                {
                    "run.id": state.run_id,
                    "execution.id": state.execution_id,
                    "agent.id": state.agent_id,
                    "agent.name": AGENT_NAME,
                }
            )
            if state.agent_id:
                set_conversation_id(state.agent_id)

            result = await client.call_tool(tool_name, arguments)
            if result is None:
                return f"ERROR: {tool_name} returned no response"

            # Extract text content
            texts = []
            for content in result.content:
                if hasattr(content, "text") and content.text:
                    texts.append(content.text)
            return "\n".join(texts) if texts else str(result)
    except Exception as e:
        print(f"  [MCP ERROR] {tool_name}: {e}")
        return f"ERROR: {e}"


# ─────────────────────────────────────────────────────────────────────────────
# Arena API Operations
# ─────────────────────────────────────────────────────────────────────────────


async def register_agent(state: AgentState) -> dict:
    """Register the agent and return registration info."""
    print("\n📋 [REGISTER] Registering agent...")

    result = await mcp_call(
        "register_agent",
        {
            "idToken": ID_TOKEN,
            "name": AGENT_NAME,
            "stack": AGENT_STACK,
            "linkedinUrl": LINKEDIN_URL,
            "githubUrl": GITHUB_URL,
        },
        state,
    )

    # Parse AGENT_ID
    agent_match = re.search(r"AGENT_ID:\s*(\S+)", result)
    if agent_match:
        state.agent_id = agent_match.group(1)

    # Parse level
    level_match = re.search(r"Level[:\s]+(\d+)", result, re.IGNORECASE)
    if level_match:
        state.current_level = int(level_match.group(1))

    print(f"   → Agent ID: {state.agent_id[:20]}...")
    print(f"   → Starting Level: {state.current_level}")
    return {"agent_id": state.agent_id, "level": state.current_level, "raw": result}


async def get_task(state: AgentState) -> Optional[dict]:
    """Fetch the current task. Returns None if NO_TASKS."""
    print(f"\n📥 [GET_TASK] Fetching task for Level {state.current_level}...")

    result = await mcp_call(
        "get_tasks",
        {
            "idToken": ID_TOKEN,
            "agentId": state.agent_id,
        },
        state,
    )

    # Check for NO_TASKS
    if "NO_TASKS" in result or "no tasks" in result.lower():
        print("   → NO_TASKS available at this level")
        return None

    # Try to parse JSON task
    try:
        # Extract JSON if wrapped in other text
        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            task = json.loads(json_match.group())
            if "id" in task:
                print(
                    f"   → Task: {task.get('title', 'Untitled')} (Level {task.get('level', '?')})"
                )
                print(
                    f"   → Points: {task.get('points', '?')} | Difficulty: {task.get('difficulty', '?')}"
                )
                return task
    except json.JSONDecodeError:
        pass

    print(f"   → Raw response: {result[:200]}...")
    return None


async def skip_task(state: AgentState, task_id: str, reason: str = "") -> str:
    """Skip the current task."""
    print(f"\n⏭️  [SKIP_TASK] Skipping {task_id[:15]}... (Reason: {reason})")

    result = await mcp_call(
        "skip_task",
        {
            "idToken": ID_TOKEN,
            "agentId": state.agent_id,
            "taskId": task_id,
            "reason": reason,
        },
        state,
    )

    return result


async def submit_task(state: AgentState, task_id: str, content: str) -> TaskResult:
    """Submit solution and parse result."""
    print(f"\n📤 [SUBMIT] Submitting solution for {task_id[:15]}...")
    print(f"   → Content length: {len(content)} chars")

    # Rotate execution ID for tracing
    state.execution_id = str(uuid.uuid4())

    result = await mcp_call(
        "submit_task",
        {
            "idToken": ID_TOKEN,
            "agentId": state.agent_id,
            "taskId": task_id,
            "executionId": state.execution_id,
            "content": content,
            "metadata": {
                "agent_name": AGENT_NAME,
                "agent_stack": AGENT_STACK,
                "run_id": state.run_id,
                "execution_id": state.execution_id,
                "model": GEMINI_MODEL,
            },
        },
        state,
    )

    # Parse score
    score_match = re.search(r"Score:\s*(\d+)/100", result)
    score = int(score_match.group(1)) if score_match else 0

    # Check for level up
    levelled_up = "LEVEL_UP" in result or "level up" in result.lower()

    # Extract feedback
    feedback_match = re.search(
        r"Feedback:\s*(.+?)(?=\n\n|\Z)", result, re.DOTALL | re.IGNORECASE
    )
    feedback = feedback_match.group(1).strip() if feedback_match else ""

    print(f"   → Score: {score}/100")
    print(f"   → Levelled Up: {'✅ YES' if levelled_up else '❌ No'}")
    if feedback:
        print(f"   → Feedback: {feedback[:100]}...")

    return TaskResult(
        level=state.current_level,
        task_id=task_id,
        task_title="",  # Will fill from task data
        score=score,
        levelled_up=levelled_up,
        feedback=feedback,
    )


# ─────────────────────────────────────────────────────────────────────────────
# LLM Solver
# ─────────────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are an expert software engineer solving coding tasks for the Agent Arena.

Your task is to:
1. Read the task description carefully
2. Provide a complete, correct, and well-structured solution
3. Include code examples where appropriate
4. Explain your reasoning clearly

Rules:
- Be thorough and detailed
- Write production-quality code
- Include comments explaining complex logic
- Handle edge cases when relevant
- If the task asks for a specific format, follow it exactly

Your answer will be scored 0-100. Aim for 90+ by being comprehensive."""


async def solve_task(task: dict, state: AgentState) -> str:
    """Use Gemini to solve the task."""
    print(f"\n🤖 [SOLVE] Generating solution with {GEMINI_MODEL}...")

    client = genai.Client(api_key=GEMINI_API_KEY)

    # Build the prompt
    task_prompt = f"""Task Title: {task.get("title", "Untitled")}
Level: {task.get("level", "?")}
Points: {task.get("points", "?")}
Difficulty: {task.get("difficulty", "Unknown")}

Description:
{task.get("description", "No description provided.")}

Provide a complete solution."""

    # Call Gemini
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[
            types.Content(role="user", parts=[types.Part(text=SYSTEM_PROMPT)]),
            types.Content(
                role="model",
                parts=[
                    types.Part(
                        text="I understand. I'll provide complete, high-quality solutions."
                    )
                ],
            ),
            types.Content(role="user", parts=[types.Part(text=task_prompt)]),
        ],
        config=types.GenerateContentConfig(
            temperature=0.2,
            max_output_tokens=8192,
        ),
    )

    solution = response.text if response.text else "ERROR: No solution generated"
    print(f"   → Generated {len(solution)} chars")
    return solution


# ─────────────────────────────────────────────────────────────────────────────
# Main Agent Loop
# ─────────────────────────────────────────────────────────────────────────────


async def run_agent() -> None:
    """Main autonomous agent loop."""

    # Initialize Traceloop
    if TRACELOOP_API_KEY:
        Traceloop.init(app_name="arena-lightweight", api_key=TRACELOOP_API_KEY)
        print("[TRACELOOP] Initialized")

    # Initialize state
    state = AgentState()

    print("\n" + "=" * 60)
    print("  🏆 AGENT ARENA — Lightweight Async Agent")
    print("=" * 60)
    print(f"  Agent     : {AGENT_NAME}")
    print(f"  Model     : {GEMINI_MODEL}")
    print(f"  Run ID    : {state.run_id}")
    print("=" * 60 + "\n")

    # Step 1: Register
    reg_info = await register_agent(state)
    if not state.agent_id:
        print("❌ Failed to register agent!")
        return

    # Step 2: Main loop
    consecutive_errors = 0

    for attempt in range(MAX_TASKS):
        print(f"\n{'─' * 60}")
        print(f"  ATTEMPT {attempt + 1}/{MAX_TASKS} | Level {state.current_level}")
        print(f"{'─' * 60}")

        # Get task
        task = await get_task(state)
        if task is None:
            print("\n🎉 No more tasks available!")
            break

        task_id = task.get("id", "")
        task_title = task.get("title", "Untitled")

        try:
            # Solve
            solution = await solve_task(task, state)

            # Submit
            result = await submit_task(state, task_id, solution)
            result.task_title = task_title

            # Record
            state.record(result)
            print(state.scoreboard())

            # Reset error counter on success
            consecutive_errors = 0

            # If didn't level up and score is low, optionally skip next similar tasks
            if not result.levelled_up and result.score < 50:
                print("   ⚠️ Low score - will try next task...")

        except Exception as e:
            print(f"\n❌ Error processing task: {e}")
            consecutive_errors += 1
            if consecutive_errors >= 3:
                print("   Too many consecutive errors, stopping.")
                break
            # Try to skip this task
            try:
                await skip_task(state, task_id, f"Error: {e}")
            except:
                pass

    # Final scoreboard
    print("\n" + "=" * 60)
    print("  🏁 FINAL RESULTS")
    print("=" * 60)
    print(state.scoreboard())
    print(f"\n  Agent {AGENT_NAME} reached Level {state.current_level}!")
    print(f"  Final Score: {state.total_score}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    if not GEMINI_API_KEY:
        print("❌ Please set GEMINI_API_KEY environment variable")
        exit(1)

    asyncio.run(run_agent())
