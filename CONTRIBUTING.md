# Contributing to Agent Arena

Thank you for your interest in improving the Agent Arena agents! This guide will help you contribute effectively.

## 🎯 Development Goals

Our primary goal is **consistent 85+ scores** on Agent Arena tasks. Every contribution should aim to:

1. Improve factual accuracy (use web search)
2. Verify code before submission (use Python execution)
3. Ensure numeric precision (use calculator)
4. Maintain temperature 0.1 for consistency

## 🚀 Quick Start for Contributors

```bash
# Fork and clone
git clone https://github.com/YOUR_USERNAME/agent-arena.git
cd agent-arena

# Setup virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dev dependencies
pip install -r requirements.txt
pip install black ruff mypy pytest

# Create branch
git checkout -b feature/your-feature-name
```

## 📁 Repository Structure

```
agent-arena/
├── arena_agent_enhanced.py    # ⭐ Main agent with tools
├── arena_agent_langchain.py   # LangChain variant
├── arena_agent_lightweight.py # Minimal async agent
├── test_agents.py             # Test suite
├── requirements.txt           # Dependencies
├── README.md                  # Documentation
├── LICENSE                    # MIT License
└── .github/
    └── workflows/
        └── test.yml           # CI/CD pipeline
```

## 🔧 Making Changes

### Adding a New Tool

1. **Create the tool class** in `arena_agent_enhanced.py`:

```python
class MyNewTool:
    def __init__(self):
        pass
    
    async def process(self, data: str) -> dict:
        # Implementation
        return {"result": "success"}
```

2. **Integrate in solver**:

```python
class EnhancedTaskSolver:
    def __init__(self, ...):
        self.new_tool = MyNewTool()
    
    async def solve(self, task):
        # Use tool when appropriate
        if self._needs_tool(task):
            result = await self.new_tool.process(task)
```

3. **Add tests** in `test_agents.py`

4. **Update README** with new feature

### Improving Existing Agents

When modifying agents:

1. Maintain **temperature = 0.1** for precision
2. Add **retry logic** for external calls
3. Include **error handling** with fallbacks
4. Log important events for debugging
5. Keep code formatted with `black`

## 🧪 Testing

### Before Committing

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy arena_agent_enhanced.py --ignore-missing-imports

# Test imports
python test_agents.py --dry-run

# Quick test (1 task)
export GEMINI_API_KEY="your-key"
python test_agents.py --quick --agent enhanced
```

### Running Full Tests

```bash
# Test specific agent
python test_agents.py --agent enhanced

# Test all
python test_agents.py --all
```

## 📝 Commit Message Guidelines

Use conventional commits:

```
<type>: <description>

[optional body]
```

Types:
- `feat:` New feature
- `fix:` Bug fix
- `perf:` Performance improvement
- `refactor:` Code restructuring
- `test:` Test additions/changes
- `docs:` Documentation updates

Examples:
```
feat: add web search tool for factual tasks
fix: handle MCP timeout in circuit breaker
perf: reduce solution generation time by 20%
refactor: extract calculator to separate module
```

## 🎮 Performance Benchmarks

Target scores by task type:

| Task Type | Target Score | Key Tool |
|-----------|--------------|----------|
| API/Library questions | 85+ | Web Search |
| Algorithm challenges | 80+ | Python Verify |
| Numeric calculations | 90+ | Calculator |
| Code debugging | 75+ | Python Verify |
| System design | 85+ | Web Search |

## 🔄 Continuous Updates

This repo follows a **continuous improvement** model:

1. **Daily**: Score tracking and analysis
2. **Weekly**: Tool improvements based on failures
3. **Monthly**: Major feature additions

### Update Checklist

When pushing updates:

- [ ] Tests pass (`python test_agents.py --dry-run`)
- [ ] Code formatted (`black .`)
- [ ] README updated if needed
- [ ] CHANGELOG.md updated
- [ ] Version bumped if significant

## 🐛 Reporting Issues

When reporting issues, include:

1. Agent version/commit hash
2. Task description (if possible)
3. Expected vs actual score
4. Error messages/logs
5. Environment (Python version, OS)

## 💡 Feature Requests

For new features, open an issue with:

1. **Problem**: What score barrier are you hitting?
2. **Solution**: What tool/change would help?
3. **Evidence**: Examples of tasks that would benefit

## 🏆 Recognition

Contributors will be:

- Listed in README.md
- Mentioned in release notes
- Credited in code comments for significant features

## 📜 Code of Conduct

- Be respectful and constructive
- Focus on score improvement, not just code style
- Share failure cases to help everyone improve
- Credit original authors when building on their work

## 📞 Questions?

- Open a GitHub issue
- Check existing issues for similar questions
- Review README.md for usage examples

---

**Let's build agents that consistently score 85+!** 🚀
