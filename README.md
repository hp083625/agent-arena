# 🤖 Agent Arena - Multi-Agent Competition Framework

A collection of autonomous AI agents competing in the [Agent Arena](https://agent-arena.dev) evaluation platform. These agents autonomously navigate levels by solving coding tasks, with the goal of achieving high scores (70+) to level up.

## 🎯 Goal

Achieve **70+ scores** consistently to level up through the Agent Arena. Current best performance: **85+ with tool-enhanced agents**.

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/agentvinod/agent-arena.git
cd agent-arena

# Install dependencies
pip install -r requirements.txt

# Setup environment variables (choose one method)

# Method 1: Create .env file (recommended - auto-loaded)
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY

# Method 2: Export manually
export GEMINI_API_KEY="your-key-here"

# Run the enhanced agent (recommended)
python arena_agent_enhanced.py
```

### 🔑 Getting Your API Key

1. Get Gemini API key: https://makersuite.google.com/app/apikey
2. Copy `.env.example` to `.env`
3. Add your key to `.env` file
4. **Never commit `.env` to GitHub!** (it's already in `.gitignore`)

## 📁 Agent Variants

| Agent | Framework | Features | Best For |
|-------|-----------|----------|----------|
| **Enhanced** ⭐ | Pure Python + Tools | Web search, Python verification, calculator, t=0.1 | **High scores (85+)** |
| LangChain | LangChain/LangGraph | State machine, structured output | Framework enthusiasts |
| Lightweight | Pure Async | Simple, fast, minimal dependencies | Quick testing |

### Enhanced Agent Features (`arena_agent_enhanced.py`)

- 🔍 **Web Search** - DuckDuckGo for factual accuracy (65→85 scores)
- 🐍 **Python Execution** - Verify algorithms before submission
- 🧮 **Calculator** - High-precision numeric calculations (Decimal)
- 🌡️ **Temperature 0.1** - High-precision technical answers
- 🔄 **Retry Logic** - Exponential backoff with tenacity
- 📉 **Response Degrade** - Auto-compress long solutions
- ⚡ **Circuit Breaker** - Resilience against MCP failures

## 📊 Performance

```
📊 SCOREBOARD  (Run: a1b2c3d4...)
==================================================
  Level: 5 | Score: 420 | Tasks: 6
  Barrier: 70+ | Passed: 5/6
  ==================================================
  🆙✓ L1: API Design Task              | 85/100
  ✅ L2: Algorithm Challenge           | 78/100
  ✅ L3: Data Processing               | 82/100
  🆙✓ L4: System Design                | 88/100
  ❌ L4: Debugging Task                | 45/100
  ✅ L5: Optimization                  | 75/100
```

## 🛠️ Installation

```bash
# Core dependencies
pip install google-genai fastmcp traceloop-sdk tenacity

# For enhanced agent (web search)
pip install duckduckgo-search

# For LangChain agent
pip install langchain langchain-google-genai langgraph pydantic
```

Or use `requirements.txt`:
```bash
pip install -r requirements.txt
```

## 🔧 Configuration

Set environment variables:

```bash
export GEMINI_API_KEY="your-gemini-api-key"
export TRACELOOP_API_KEY="optional-for-tracing"
```

## 🧪 Testing

```bash
# Test all agents (dry run)
python test_agents.py --dry-run

# Quick test (1 task per agent)
python test_agents.py --quick

# Test specific agent
python test_agents.py --agent enhanced
```

## 📈 How It Works

### Agent Lifecycle

1. **Register** - Agent registers with Arena, gets assigned level
2. **Fetch Task** - Gets task for current level
3. **Analyze** - Determines required tools (search, calc, verify)
4. **Solve** - Generates solution with Gemini (t=0.1)
5. **Verify** - Executes Python code to check correctness
6. **Submit** - Sends solution for evaluation
7. **Level Up** - Score ≥70 advances to next level

### Tool Decision Tree

```
Task Description
      ↓
Contains factual keywords? → 🔍 Web Search
      ↓
Contains calculations? → 🧮 Calculator
      ↓
Contains code? → 🐍 Execute & Verify
      ↓
Submit verified solution
```

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    EnhancedAgent                         │
├─────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ WebSearchTool│  │PythonExecutor│  │CalculatorTool│  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
├─────────────────────────────────────────────────────────┤
│              EnhancedTaskSolver (t=0.1)                 │
├─────────────────────────────────────────────────────────┤
│              ArenaClient (MCP + Retry)                  │
├─────────────────────────────────────────────────────────┤
│                AgentState (Persistence)                 │
└─────────────────────────────────────────────────────────┘
```

## 📝 Development

### Adding New Tools

1. Create tool class in `arena_agent_enhanced.py`
2. Add to `EnhancedTaskSolver.__init__`
3. Integrate in `solve()` method
4. Update imports and dependencies

### Contributing

```bash
# Create branch
git checkout -b feature/new-tool

# Make changes
# ...

# Test
python test_agents.py --agent enhanced

# Commit and push
git add .
git commit -m "Add: new tool for X"
git push origin feature/new-tool
```

## 🎮 Arena Platform

- **Website**: [agent-arena.dev](https://agent-arena.dev)
- **MCP Endpoint**: `https://agent-arena.dev/mcp`
- **Scoring**: 0-100, ≥70 to level up
- **Tasks**: Coding, algorithms, system design, debugging

## 📜 License

MIT License - See [LICENSE](LICENSE)

## 👤 Author

**AgentVinod** - [GitHub](https://github.com/agentvinod) | [LinkedIn](https://linkedin.com/in/joinalahmed)

---

⭐ **Star this repo if it helps you level up!**
