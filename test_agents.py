"""
test_agents.py — Agent Arena Test Suite
========================================

Test and verify all arena agent implementations:
- arena_agent.py (Google ADK)
- arena_agent_lightweight.py (Async)
- arena_agent_enhanced.py (Retry + Degrade)
- arena_agent_langchain.py (LangChain/LangGraph)

Modes:
    --dry-run    : Test connections without submitting
    --quick      : Run 1 task only per agent
    --agent NAME : Test specific agent only
    --all        : Test all agents sequentially

Usage:
    export GEMINI_API_KEY="your-key"
    python test_agents.py --dry-run
    python test_agents.py --quick --agent enhanced
    python test_agents.py --all
"""

import asyncio
import argparse
import importlib.util
import sys
import os
import json
import re
import time
from dataclasses import dataclass, field
from typing import Optional, Callable, List, Dict, Any
from pathlib import Path

from fastmcp.client import Client
from fastmcp.client.transports import StreamableHttpTransport

# ─────────────────────────────────────────────────────────────────────────────
# Configuration
# ─────────────────────────────────────────────────────────────────────────────

MCP_ENDPOINT = "https://agent-arena.dev/mcp"
ID_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IjcwZmM5YzU0YjhiMjQyMWZmMTgyOTgxNTQyZmQ0NjRlOWJlYzM1NDUiLCJ0eXAiOiJKV1QifQ.eyJuYW1lIjoiSm9pbmFsIEFobWVkIiwicGljdHVyZSI6Imh0dHBzOi8vbGgzLmdvb2dsZXVzZXJjb250ZW50LmNvbS9hLS9BTFYtVWpYSzVYQzVTTnJCMXFQWXBMNGlWUmM0VHdtd2hHbzlTbTBaTjBsVTNBa3NuQ2JyVkg1QVROUHFSYV9vak4zeThJclYtTjNmT2dHMVk4YV9vYndvSWN6eE5RNmQ0al9JX1FMTUNNbjB4bXlCdThXWnl0OGFqYzVFeGhoOWZSR0FEanp3LWhjRDZGX1BfSDFYQ3Y2YzkwbktSZ2c0ZmlZMHY5WkJHZ29qeDU4ekNjSThIMlNrbDJIeU5LcklHR1NoTF83b1BZVjBSdFRuYXlLMldBX1ZmLVZjRXBBbWRxMGZnWWdndm9tbW9lMzVaQV9zTGR4UkVGN2UzbHQ2RTJoM1RkQmJ0bTl2aEdWbTQ5MjRQUUYxVnkxZmpIRVpEQ213eHNxY3B5LTF6VEFoM0dyLVp5c3FPRUVqRnBuejBwRmtKWEVWRWNUQlpPajJxOGZjNXEtdUVzR01MMy1tZW9Bb09tcUJIU3lsTDhDaXRZa1BMR1dWNVJON2w2S0dOSTNJd3FfOU1wUzdlUUU3VllyenJ1VEZ6ME1WdnFpOVRyMmZGOWc1a242djJ1aGh6UUdaczhXVlFObl8zcjh2QjV5bnJubzB0QlBreWplRzl0ZWs2N1BGOGNoc1VMeWl1X1I2cGRCMS1ydGVwckZ5VVJzazJWcUVqMFRUaXpWdWRSNkJwN1VYVmtpTUNqb0p5ZW92VkdXU2JtVk1hOVp2NFlwRDNzLUU1UW12bXVBOVJyUEIzRG9ZUm43N1BTU2tfQ2hjZzBwZ2h1UWJ6bEVOUndjSlRiLTdLalNub3NnVUpFanJmV0FKTFBEOE9aUHFtWlZxZVV5U2dlOW04U1NESWFMQmt2Y3JuQnlwdlpOR3ZNOGg3QjY5Y3VZRFFWUnU4dHBBR1FMaVBFaG4zQ24zWmxQZHhjaGNqV1hfbDBUallqWkJ0QlhmTXA3cVg3TzJSLWhWZTdrdjktbkZaQTctNWpEelczUTU0aUZFc3J2dlhVYWxlTGJXS0h6U3htaFVDTF9iaVg4ZElJeGQteU9vblJrQ0JObWdRdEdCS2lfNWo0OW9PNGJQSGFBV1VkdUE2M3Mzd1BzckJiYU9FR0ZfLU9IekpkT1dNTmNqQjBOdlNiMVNIcFRZWXg2eTdUUlBRQUEwXzljNnNxazM2aEtnRk1ndENreHB1Sko0MlJyMWZ6RVRCNHBlYUtpTUVFaTdWMERLZHE3S0V0TmlPdjQxelhObFlnMGpOQUVJajk0bkkwWmdmRU5xMnIxRjFpZE5NU21QVmJuLTlhMHF0ZXhkd0F3bjhib3lYblEzX2Y0ei1xU2RoY1hqRE5laTZDZVJveFdZZjNiX3RPQ0xiV082MGtOX3loTDZQMUJRamxOa3lHeDBlTUw3aERPRFR0STNLNHZ6aE9kRWdFajFldkt0T2d4MXhjNlM2dDg9czk2LWMiLCJpc3MiOiJodHRwczovL3NlY3VyZXRva2VuLmdvb2dsZS5jb20vZ2RlLWFnZW50LWV2YWwiLCJhdWQiOiJnZGUtYWdlbnQtZXZhbCIsImF1dGhfdGltZSI6MTc3NjU4MDE4NywidXNlcl9pZCI6InZQWExyZE5EWjVOTVN5azdERVY3TUVvdEdPejIiLCJzdWIiOiJ2UFhMcmRORFo1Tk1TeWs3REVWN01Fb3RHT3oyIiwiaWF0IjoxNzc2NTkzMzkxLCJleHAiOjE3NzY1OTY5OTEsImVtYWlsIjoiam9pbmFsYWhtZWRAZ21haWwuY29tIiwiZW1haWxfdmVyaWZpZWQiOnRydWUsImZpcmViYXNlIjp7ImlkZW50aXRpZXMiOnsiZ29vZ2xlLmNvbSI6WyIxMDIwOTY1ODY1OTg1MDEzNTAyOTUiXSwiZW1haWwiOlsiam9pbmFsYWhtZWRAZ21haWwuY29tIl19LCJzaWduX2luX3Byb3ZpZGVyIjoiZ29vZ2xlLmNvbSJ9fQ.xJY_ja7BIgkEhyuhYtdVr60sua0B6VWwgMZrWOz703WAVZ-kv5QeHT9aLS4SDM4_mJaUgMfEXGOg4BLs6RXjtDDfNuuNFigHW7fmX68ZFRM51GSvUGGzSPd-GX5wXr1MnspqGhlap_lq5O7uIvecDiegU0cKYJ92gzSq8TDfdJ6BGeBg-d7os9cPgWsK9_FZbhN5vINV_d3jYWqvPRo96bXsNZIsiSJlbYc7HuqrIu2AL8upK1Yz3BCmdPbGR2uM_N2Ite92wrqQwcF81YHkBDOEIWwECtq-ErOC0MW1O3orshIDQqKl_zIwe5DZJik43RgjkBfWdYS4cPFIQRhylw"

# ─────────────────────────────────────────────────────────────────────────────
# Test Infrastructure
# ─────────────────────────────────────────────────────────────────────────────


@dataclass
class TestResult:
    agent_name: str
    success: bool
    level: int = 0
    score: int = 0
    tasks_completed: int = 0
    errors: List[str] = field(default_factory=list)
    duration: float = 0.0


class Colors:
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    END = "\033[0m"


def print_header(text: str) -> None:
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'=' * 65}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}  {text}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'=' * 65}{Colors.END}\n")


def print_success(text: str) -> None:
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_error(text: str) -> None:
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_warning(text: str) -> None:
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


# ─────────────────────────────────────────────────────────────────────────────
# MCP Connection Tests
# ─────────────────────────────────────────────────────────────────────────────


async def test_mcp_connection() -> bool:
    """Test basic MCP connectivity."""
    print("Testing MCP connection...")
    try:
        transport = StreamableHttpTransport(url=MCP_ENDPOINT)
        async with Client(transport=transport, name="test-client") as client:
            # Try to call register_agent
            result = await client.call_tool(
                "register_agent",
                {
                    "idToken": ID_TOKEN,
                    "name": "TestAgent",
                    "stack": "Test",
                    "linkedinUrl": "https://linkedin.com",
                    "githubUrl": "https://github.com",
                },
            )
            if result and result.content:
                print_success("MCP connection successful")
                return True
    except Exception as e:
        print_error(f"MCP connection failed: {e}")
        return False
    return False


# ─────────────────────────────────────────────────────────────────────────────
# Agent Tests
# ─────────────────────────────────────────────────────────────────────────────


async def test_enhanced_agent(dry_run: bool = False, quick: bool = False) -> TestResult:
    """Test the enhanced agent with retry logic."""
    start_time = time.time()
    result = TestResult(agent_name="enhanced")

    print_header("Testing Enhanced Agent (Retry + Degrade)")

    try:
        # Import and check
        spec = importlib.util.spec_from_file_location(
            "enhanced", "arena_agent_enhanced.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print_success("Module imports successfully")

        if dry_run:
            print_warning("Dry run - skipping execution")
            return result

        # Run agent
        agent = module.EnhancedAgent()

        if quick:
            # Monkey-patch to only run 1 task
            original_run = agent.run
            task_count = [0]

            async def limited_run():
                # Just do registration and one task
                if module.TRACELOOP_API_KEY and module.TRACELOOP_API_KEY != "":
                    module.Traceloop.init(
                        app_name="arena-enhanced-test", api_key=module.TRACELOOP_API_KEY
                    )

                print("\n" + "=" * 65)
                print("  🚀 QUICK TEST MODE - 1 task only")
                print("=" * 65)

                await agent.arena.register()
                if not agent.state.agent_id:
                    print_error("Registration failed")
                    return

                task = await agent.arena.get_task()
                if not task:
                    print_warning("No task available")
                    return

                solution = await agent.solver.solve(task)
                submit_result = await agent.arena.submit(task["id"], solution)
                agent.state.record(submit_result)
                print(agent.state.scoreboard())

            await limited_run()
        else:
            await agent.run()

        result.success = True
        result.level = agent.state.current_level
        result.score = agent.state.total_score
        result.tasks_completed = agent.state.tasks_completed

    except Exception as e:
        result.errors.append(str(e))
        print_error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()

    result.duration = time.time() - start_time
    return result


async def test_langchain_agent(
    dry_run: bool = False, quick: bool = False
) -> TestResult:
    """Test the LangChain agent."""
    start_time = time.time()
    result = TestResult(agent_name="langchain")

    print_header("Testing LangChain Agent")

    try:
        # Check imports
        spec = importlib.util.spec_from_file_location(
            "langchain", "arena_agent_langchain.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print_success("Module imports successfully")

        if dry_run:
            print_warning("Dry run - skipping execution")
            return result

        # Run agent
        if quick:
            print_warning(
                "Quick mode not fully implemented for LangChain - running full agent"
            )

        await module.main()
        result.success = True

    except Exception as e:
        result.errors.append(str(e))
        print_error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()

    result.duration = time.time() - start_time
    return result


async def test_adk_agent(dry_run: bool = False, quick: bool = False) -> TestResult:
    """Test the original ADK agent."""
    start_time = time.time()
    result = TestResult(agent_name="adk")

    print_header("Testing Original ADK Agent")

    try:
        # Check imports
        spec = importlib.util.spec_from_file_location("adk", "arena_agent.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print_success("Module imports successfully")

        if dry_run:
            print_warning("Dry run - skipping execution")
            return result

        # Note: ADK agent runs full loop
        print_warning("ADK agent runs full autonomous loop - use --quick with caution")
        if not quick:
            await module.run()

        result.success = True

    except Exception as e:
        result.errors.append(str(e))
        print_error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()

    result.duration = time.time() - start_time
    return result


async def test_lightweight_agent(
    dry_run: bool = False, quick: bool = False
) -> TestResult:
    """Test the lightweight agent."""
    start_time = time.time()
    result = TestResult(agent_name="lightweight")

    print_header("Testing Lightweight Agent")

    try:
        # Check imports
        spec = importlib.util.spec_from_file_location(
            "lightweight", "arena_agent_lightweight.py"
        )
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        print_success("Module imports successfully")

        if dry_run:
            print_warning("Dry run - skipping execution")
            return result

        if quick:
            print_warning(
                "Quick mode not implemented for lightweight - running full agent"
            )

        await module.run_agent()
        result.success = True

    except Exception as e:
        result.errors.append(str(e))
        print_error(f"Test failed: {e}")
        import traceback

        traceback.print_exc()

    result.duration = time.time() - start_time
    return result


# ─────────────────────────────────────────────────────────────────────────────
# Test Runner
# ─────────────────────────────────────────────────────────────────────────────


async def run_all_tests(args) -> List[TestResult]:
    """Run all requested tests."""
    results: List[TestResult] = []

    # Check environment
    if not os.environ.get("GEMINI_API_KEY"):
        print_error("GEMINI_API_KEY not set!")
        return results

    print_header("Agent Arena Test Suite")
    print(f"Dry run: {args.dry_run}")
    print(f"Quick mode: {args.quick}")
    print(f"Target: {args.agent or 'all'}")

    # Test MCP first
    if not await test_mcp_connection():
        print_error("MCP connection failed - aborting tests")
        return results

    # Run requested tests
    agents_to_test = []
    if args.agent:
        agents_to_test = [args.agent.lower()]
    else:
        agents_to_test = ["enhanced", "langchain", "adk", "lightweight"]

    for agent_name in agents_to_test:
        if agent_name == "enhanced":
            results.append(await test_enhanced_agent(args.dry_run, args.quick))
        elif agent_name == "langchain":
            results.append(await test_langchain_agent(args.dry_run, args.quick))
        elif agent_name == "adk":
            results.append(await test_adk_agent(args.dry_run, args.quick))
        elif agent_name == "lightweight":
            results.append(await test_lightweight_agent(args.dry_run, args.quick))
        else:
            print_error(f"Unknown agent: {agent_name}")

    return results


def print_summary(results: List[TestResult]) -> None:
    """Print test summary."""
    print_header("Test Summary")

    total = len(results)
    passed = sum(1 for r in results if r.success)

    print(f"{Colors.BOLD}Results: {passed}/{total} passed{Colors.END}\n")

    for r in results:
        status = f"{Colors.GREEN}PASS" if r.success else f"{Colors.RED}FAIL"
        print(
            f"  {status}{Colors.END} {r.agent_name:<15} | Duration: {r.duration:.1f}s"
        )
        if r.level > 0:
            print(
                f"           Level: {r.level} | Score: {r.score} | Tasks: {r.tasks_completed}"
            )
        for err in r.errors:
            print(f"           Error: {err[:60]}")

    print()
    if passed == total:
        print_success("All tests passed!")
    else:
        print_error(f"{total - passed} test(s) failed")


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Test Arena Agents")
    parser.add_argument("--dry-run", action="store_true", help="Test imports only")
    parser.add_argument(
        "--quick", action="store_true", help="Run only 1 task per agent"
    )
    parser.add_argument(
        "--agent",
        type=str,
        help="Test specific agent (enhanced/langchain/adk/lightweight)",
    )
    parser.add_argument("--all", action="store_true", help="Test all agents (default)")

    args = parser.parse_args()

    # Run tests
    results = asyncio.run(run_all_tests(args))

    # Print summary
    if results:
        print_summary(results)
    else:
        print_error("No tests were run")
        sys.exit(1)

    # Exit with appropriate code
    sys.exit(0 if all(r.success for r in results) else 1)


if __name__ == "__main__":
    main()
