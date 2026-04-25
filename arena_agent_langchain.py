"""
arena_agent_langchain.py — LangChain-Based Agent with LCEL
==========================================================

A LangChain agent using:
- LangChain Expression Language (LCEL) for composable chains
- Gemini via ChatGoogleGenerativeAI
- Structured output with Pydantic
- Tool calling for arena operations
- State graph for the leveling loop

Dependencies:
    pip install langchain langchain-google-genai fastmcp pydantic

Usage:
    export GEMINI_API_KEY="your-key"
    python arena_agent_langchain.py
"""

import asyncio
import json
import os
import re
import uuid
from dataclasses import dataclass, field
from typing import Optional, Literal, TypedDict, Annotated
from operator import add

from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import tool, ToolException
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.runnables import RunnableLambda, RunnableSequence
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport
from fastmcp.exceptions import ToolError

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MCP_ENDPOINT = "https://agent-arena.dev/mcp"

ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjcwZmM5YzU0YjhiMjQyMWZmMTgyOTgxNTQyZmQ0NjRlOWJlYzM1NDUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9pbmFsIEFobWVkIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BTFYtVWpYSzVYQzVTTnJCMXFQWXBMNGlWUmM0VHdtd2hHbzlTbTBaTjBsVTNBa3NuQ2JyVkg1QVROUHFSYV9vak4zeThJclYtTjNmT2dHMVk4YV9vYndvSWN6eE5RNmQ0al9JX1FMTUNNbjB4bXlCdThXWnl0OGFqYzVFeGhoOWZSR0FEanp3LWhjRDZGX1BfSDFYQ3Y2YzkwbktSZ2c0ZmlZMHY5WkJHZ29qeDU4ekNjSThIMlNrbDJIeU5LcklHR1NoTF83b1BZVjBSdFRuYXlLMldBX1ZmLVZjRXBBbWRxMGZnWWdndm9tbW9lMzVaQV9zTGR4UkVGN2UzbHQ2RTJoM1RkQmJ0bTl2aEdWbTQ5MjRQUUYxVnkxZmpIRVpEQ213eHNxY3B5LTF6VEFoM0dyLVp5c3FPRUVqRnBuejBwRmtKWEVWRWNUQlpPajJxOGZjNXEtdUVzR01MMy1tZW9Bb09tcUJIU3lsTDhDaXRZa1BMR1dWNVJON2w2S0dOSTNJd3FfOU1wUzdlUUU3VllyenJ1VEZ6ME1WdnFpOVRyMmZGOWc1a242djJ1aGh6UUdaczhXVlFObl8zcjh2QjV5bnJubzB0QlBreWplRzl0ZWs2N1BGOGNoc1VMeWl1X1I2cGRCMS1ydGVwckZ5VVJzazJWcUVqMFRUaXpWdWRSNkJwN1VYVmtpTUNqb0p5ZW92VkdXU2JtVk1hOVp2NFlwRDNzLUU1UW12bXVBOVJyUEIzRG9ZUm43N1BTU2tfQ2hjZzBwZ2h1UWJ6bEVOUndjSlRiLTdLalNub3NnVUpFanJmV0FKTFBEOE9aUHFtWlZxZVV5U2dlOW04U1NESWFMQmt2Y3JuQnlwdlpOR3ZNOGg3QjY5Y3VZRFFWUnU4dHBBR1FMaVBFaG4zQ24zWmxQZHhjaGNqV1hfbDBUallqWkJ0QlhmTXA3cVg3TzJSLWhWZTdrdjktbkZaQTctNWpEelczUTU0aUZFc3J2dlhVYWxlTGJXS0h6U3htaFVDTF9iaVg4ZElJeGQteU9vblJrQ0JObWdRdEdCS2lfNWo0OW9PNGJQSGFBV1VkdUE2M3Mzd1BzckJiYU9FR0ZfLU9IekpkT1dNTmNqQjBOdlNiMVNIcFRZWXg2eTdUUlBRQUEwXzljNnNxazM2aEtnRk1ndENreHB1Sko0MlJyMWZ6RVRCNHBlYUtpTUVFaTdWMERLZHE3S0V0TmlPdjQxelhObFlnMGpOQUVJajk0bkkwWmdmRU5xMnIxRjFpZE5NU21QVmJuLTlhMHF0ZXhkd0F3bjhib3lYblEzX2Y0ei1xU2RoY1hqRE5laTZDZVJveFdZZjNiX3RPQ0xiV082MGtOX3loTDZQMUJRamxOa3lHeDBlTUw3aERPRFR0STNLNHZ6aE9kRWdFajFldkt0T2d4MXhjNlM2dDg9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZ2RlLWFnZW50LWV2YWwiLCJhdWQiOiJnZGUtYWdlbnQtZXZhbCIsImF1dGhfdGltZSI6MTc3NjU4MDE4NywidXNlcl9pZCI6InZQWExyZE5EWjVOTVN5azdERVY3TUVvdEdPejIiLCJzdWIiOiJ2UFhMcmRORFo1Tk1TeWs3REVWN01Fb3RHT3oyIiwiaWF0IjoxNzc2NTkzMzkxLCJleHAiOjE3NzY1OTY5OTEsImVtYWlsIjoiam9pbmFsYWhtZWRAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDIwOTY1ODY1OTg1MDEzNTAyOTUiXSwiZW1haWwiOlsiam9pbmFsYWhtZWRAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.xJY_ja7BIgkEhyuhYtdVr60sua0B6VWwgMZrWOz703WAVZ-kv5QeHT9aLS4SDM4_mJaUgMfEXGOg4BLs6RXjtDDfNuuNFigHW7fmX68ZFRM51GSvUGGzSPd-GX5wXr1MnspqGhlap_lq5O7uIvecDiegU0cKYJ92gzSq8TDfdJ6BGeBg-d7os9cPgWsK9_FZbhN5vINV_d3jYWqvPRo96bXsNZIsiSJlbYc7HuqrIu2AL8upK1Yz3BCmdPbGR2uM_N2Ite92wrqQwcF81YHkBDOEIWwECtq-ErOC0MW1O3orshIDQqKl_zIwe5DZJik43RgjkBfWdYS4cPFIQRhylw"

AGENT_NAME = "AgentVinod-LangChain-v1"
AGENT_STACK = "Python / LangChain / LangGraph / Gemini"
LINKEDIN_URL = "https://www.linkedin.com/in/joinalahmed"
GITHUB_URL = "https://github.com/agentvinod"
GEMINI_MODEL = "gemini-2.0-flash"
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
MAX_TASKS = 15

# ─────────────────────────────────────────────────────────────────────────────
# State Management
# ─────────────────────────────────────────────────────────────────────────────


class TaskRecord(BaseModel):
    level: int
    task_id: str
    title: str
    score: int
    levelled_up: bool


class AgentState(TypedDict):
    """State for LangGraph."""

    run_id: str
    agent_id: str
    current_level: int
    total_score: int
    tasks_completed: int
    task_history: Annotated[list[TaskRecord], add]
    current_task: Optional[dict]
    current_solution: str
    last_result: Optional[dict]
    messages: Annotated[list, add]
    continue_loop: bool
    error_count: int


# ─────────────────────────────────────────────────────────────────────────────
# MCP Tools
# ─────────────────────────────────────────────────────────────────────────────


async def mcp_call(tool_name: str, arguments: dict) -> str:
    """Execute MCP tool call."""
    transport = StreamableHttpTransport(url=MCP_ENDPOINT)
    try:
        async with Client(transport=transport, name="arena-langchain") as client:
            result = await client.call_tool(tool_name, arguments)
            if result is None:
                return f"ERROR: {tool_name} returned no response"
            texts = [c.text for c in result.content if hasattr(c, "text") and c.text]
            return "\n".join(texts) if texts else str(result)
    except ToolError as e:
        return f"ERROR: {e}"
    except Exception as e:
        raise ToolException(f"MCP call failed: {e}")


# ─────────────────────────────────────────────────────────────────────────────
# LangGraph Nodes
# ─────────────────────────────────────────────────────────────────────────────


async def register_node(state: AgentState) -> AgentState:
    """Register the agent."""
    print("\n📋 [REGISTER] Registering with Arena...")

    result = await mcp_call(
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
        state["agent_id"] = agent_match.group(1)

    level_match = re.search(r"Level[:\s]+(\d+)", result, re.IGNORECASE)
    if level_match:
        state["current_level"] = int(level_match.group(1))

    print(f"   → Agent: {state['agent_id'][:20]}... | Level: {state['current_level']}")
    state["messages"].append(
        SystemMessage(
            content=f"Registered as {state['agent_id']}, Level {state['current_level']}"
        )
    )
    return state


async def fetch_task_node(state: AgentState) -> AgentState:
    """Fetch the next task."""
    print(f"\n📥 [FETCH] Getting task for Level {state['current_level']}...")

    result = await mcp_call(
        "get_tasks",
        {
            "idToken": ID_TOKEN,
            "agentId": state["agent_id"],
        },
    )

    if "NO_TASKS" in result or "no tasks" in result.lower():
        print("   → NO_TASKS available")
        state["current_task"] = None
        state["continue_loop"] = False
        return state

    # Parse task
    try:
        json_match = re.search(r"\{.*\}", result, re.DOTALL)
        if json_match:
            task = json.loads(json_match.group())
            if "id" in task:
                state["current_task"] = task
                print(f"   → Task: {task.get('title')} ({task.get('points')} pts)")
                state["messages"].append(
                    HumanMessage(
                        content=f"Task: {task.get('title')}\n{task.get('description', '')}"
                    )
                )
                return state
    except json.JSONDecodeError:
        pass

    state["current_task"] = None
    return state


class SolutionOutput(BaseModel):
    """Structured solution output."""

    solution: str = Field(description="Complete solution to the task")
    approach: str = Field(description="Brief description of the approach taken")


def create_solve_node():
    """Create the solver node with structured output."""
    llm = ChatGoogleGenerativeAI(
        model=GEMINI_MODEL,
        google_api_key=GEMINI_API_KEY,
        temperature=0.2,
        convert_system_message_to_human=True,
    )

    structured_llm = llm.with_structured_output(SolutionOutput)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                """You are an expert software engineer. Solve the given task completely.
Provide working code, explanations, and handle edge cases. Be thorough - your solution is scored 0-100.""",
            ),
            MessagesPlaceholder(variable_name="messages"),
            ("human", "Provide a complete solution for this task."),
        ]
    )

    chain = prompt | structured_llm

    async def solve(state: AgentState) -> AgentState:
        task = state["current_task"]
        if not task:
            return state

        print(f"\n🤖 [SOLVE] Generating solution with {GEMINI_MODEL}...")

        # Add task context
        task_msg = f"""Task: {task.get("title")}
Level: {task.get("level")} | Points: {task.get("points")} | Difficulty: {task.get("difficulty")}

Description:
{task.get("description")}"""

        temp_state = {**state, "messages": [HumanMessage(content=task_msg)]}

        try:
            result: SolutionOutput = await chain.ainvoke(temp_state)
            full_solution = f"{result.approach}\n\n{result.solution}"
            state["current_solution"] = full_solution
            print(f"   → Generated {len(full_solution)} chars")
        except Exception as e:
            print(f"   → Error: {e}")
            state["current_solution"] = f"Error generating solution: {e}"
            state["error_count"] += 1

        return state

    return solve


async def submit_node(state: AgentState) -> AgentState:
    """Submit the solution."""
    task = state["current_task"]
    solution = state["current_solution"]

    if not task or not solution:
        return state

    print(f"\n📤 [SUBMIT] Submitting solution...")

    execution_id = str(uuid.uuid4())
    result = await mcp_call(
        "submit_task",
        {
            "idToken": ID_TOKEN,
            "agentId": state["agent_id"],
            "taskId": task["id"],
            "executionId": execution_id,
            "content": solution,
            "metadata": {
                "agent_name": AGENT_NAME,
                "agent_stack": AGENT_STACK,
                "model": GEMINI_MODEL,
            },
        },
    )

    # Parse result
    score_match = re.search(r"Score:\s*(\d+)/100", result)
    score = int(score_match.group(1)) if score_match else 0

    levelled_up = "LEVEL_UP" in result

    print(f"   → Score: {score}/100 | Levelled Up: {'✅' if levelled_up else '❌'}")

    # Update state
    state["tasks_completed"] += 1
    state["total_score"] += score

    if levelled_up:
        state["current_level"] += 1

    record = TaskRecord(
        level=state["current_level"],
        task_id=task["id"],
        title=task.get("title", "Untitled"),
        score=score,
        levelled_up=levelled_up,
    )
    state["task_history"].append(record)
    state["last_result"] = {"score": score, "levelled_up": levelled_up}

    # Check if we should continue
    if state["tasks_completed"] >= MAX_TASKS:
        state["continue_loop"] = False

    return state


def scoreboard_node(state: AgentState) -> AgentState:
    """Display scoreboard."""
    lines = [
        f"\n{'=' * 60}",
        f"  📊 SCOREBOARD  (Run: {state['run_id'][:8]}...)",
        f"{'=' * 60}",
        f"  Level: {state['current_level']} | Score: {state['total_score']} | Tasks: {state['tasks_completed']}",
        f"{'=' * 60}",
    ]
    for r in state["task_history"]:
        icon = "🆙" if r.levelled_up else ("✅" if r.score >= 70 else "❌")
        lines.append(f"  {icon} L{r.level}: {r.title[:40]:<40} | {r.score:>3}/100")
    lines.append(f"{'=' * 60}\n")
    print("\n".join(lines))
    return state


def final_report_node(state: AgentState) -> AgentState:
    """Final report."""
    print("\n" + "=" * 60)
    print("  🏁 FINAL RESULTS")
    print("=" * 60)
    print(f"  Agent: {AGENT_NAME}")
    print(f"  Final Level: {state['current_level']}")
    print(f"  Total Score: {state['total_score']}")
    print(f"  Tasks Completed: {state['tasks_completed']}")
    print(f"  Errors: {state['error_count']}")
    print("=" * 60)
    return state


# ─────────────────────────────────────────────────────────────────────────────
# Graph Routing
# ─────────────────────────────────────────────────────────────────────────────


def should_continue(state: AgentState) -> Literal["fetch", "end"]:
    """Determine if we should fetch another task."""
    if state.get("continue_loop", False) and state["tasks_completed"] < MAX_TASKS:
        return "fetch"
    return "end"


def has_task(state: AgentState) -> Literal["solve", "end"]:
    """Check if we got a task."""
    if state.get("current_task"):
        return "solve"
    state["continue_loop"] = False
    return "end"


# ─────────────────────────────────────────────────────────────────────────────
# Build Graph
# ─────────────────────────────────────────────────────────────────────────────


def build_agent_graph():
    """Build the LangGraph state machine."""

    # Create workflow
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node("register", register_node)
    workflow.add_node("fetch_task", fetch_task_node)
    workflow.add_node("solve", create_solve_node())
    workflow.add_node("submit", submit_node)
    workflow.add_node("scoreboard", scoreboard_node)
    workflow.add_node("final_report", final_report_node)

    # Define edges
    workflow.set_entry_point("register")
    workflow.add_edge("register", "fetch_task")
    workflow.add_edge("scoreboard", "fetch_task")

    # Conditional edges from fetch
    workflow.add_conditional_edges(
        "fetch_task", has_task, {"solve": "solve", "end": "final_report"}
    )

    workflow.add_edge("solve", "submit")
    workflow.add_edge("submit", "scoreboard")

    # Conditional edges from scoreboard (loop back)
    workflow.add_conditional_edges(
        "fetch_task", should_continue, {"fetch": "fetch_task", "end": "final_report"}
    )

    workflow.add_edge("final_report", END)

    # Compile with memory
    memory = MemorySaver()
    return workflow.compile(checkpointer=memory)


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────


async def main():
    """Run the LangChain agent."""

    print("\n" + "=" * 60)
    print("  🦜 AGENT ARENA — LangChain / LangGraph Agent")
    print("=" * 60)
    print(f"  Agent: {AGENT_NAME}")
    print(f"  Model: {GEMINI_MODEL}")
    print("=" * 60 + "\n")

    if not GEMINI_API_KEY:
        print("❌ Please set GEMINI_API_KEY environment variable")
        return

    # Build and run graph
    graph = build_agent_graph()

    # Initial state
    initial_state: AgentState = {
        "run_id": str(uuid.uuid4()),
        "agent_id": "",
        "current_level": 1,
        "total_score": 0,
        "tasks_completed": 0,
        "task_history": [],
        "current_task": None,
        "current_solution": "",
        "last_result": None,
        "messages": [],
        "continue_loop": True,
        "error_count": 0,
    }

    # Run
    config = {"configurable": {"thread_id": initial_state["run_id"]}}
    result = await graph.ainvoke(initial_state, config)

    print("\n✅ Agent execution complete!")


if __name__ == "__main__":
    asyncio.run(main())
