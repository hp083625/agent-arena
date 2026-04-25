#!/bin/bash
# status.sh - Show repository status and agent statistics
# Usage: ./status.sh

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}"
echo "    ╔══════════════════════════════════════════════════════════════╗"
echo "    ║             🤖 AGENT ARENA - REPOSITORY STATUS               ║"
echo "    ╚══════════════════════════════════════════════════════════════╝"
echo -e "${NC}"

# Repository info
echo -e "${BLUE}📁 Repository Information${NC}"
echo "   Remote URL: $(git remote get-url origin 2>/dev/null || echo 'N/A')"
echo "   Branch: $(git branch --show-current 2>/dev/null || echo 'N/A')"
echo "   Total Commits: $(git rev-list --count HEAD 2>/dev/null || echo '0')"
echo "   Last Update: $(git log -1 --format=%cd --date=human 2>/dev/null || echo 'N/A')"
echo ""

# File statistics
echo -e "${BLUE}📊 File Statistics${NC}"
AGENT_COUNT=$(ls -1 arena_agent_*.py 2>/dev/null | wc -l)
TOTAL_LINES=$(find . -name "*.py" -not -path "./__pycache__/*" -exec cat {} \; 2>/dev/null | wc -l)
echo "   Agent Variants: $AGENT_COUNT"
echo "   Total Python Lines: $TOTAL_LINES"
echo "   Test Files: $(ls -1 test_*.py 2>/dev/null | wc -l)"
echo ""

# Git status
echo -e "${BLUE}📝 Git Status${NC}"
if git diff --quiet && git diff --cached --quiet; then
    echo -e "   ${GREEN}✓ Working directory clean${NC}"
else
    MODIFIED=$(git diff --name-only | wc -l)
    STAGED=$(git diff --cached --name-only | wc -l)
    UNTRACKED=$(git ls-files --others --exclude-standard | wc -l)
    
    if [ $STAGED -gt 0 ]; then
        echo -e "   ${YELLOW}⚠ $STAGED file(s) staged for commit${NC}"
    fi
    if [ $MODIFIED -gt 0 ]; then
        echo -e "   ${YELLOW}⚠ $MODIFIED file(s) modified${NC}"
    fi
    if [ $UNTRACKED -gt 0 ]; then
        echo -e "   ${RED}✗ $UNTRACKED untracked file(s)${NC}"
    fi
fi
echo ""

# Recent commits
echo -e "${BLUE}📜 Recent Commits${NC}"
git log --oneline -5 2>/dev/null || echo "   No commits yet"
echo ""

# Agent health check
echo -e "${BLUE}🔍 Agent Health Check${NC}"
for agent in arena_agent_*.py; do
    if [ -f "$agent" ]; then
        # Check for common issues
        if grep -q "TEMPERATURE = 0.1" "$agent" 2>/dev/null; then
            TEMP="${GREEN}✓ t=0.1${NC}"
        else
            TEMP="${YELLOW}○ t=?${NC}"
        fi
        
        if grep -q "WebSearchTool\|PythonExecutor\|CalculatorTool" "$agent" 2>/dev/null; then
            TOOLS="${GREEN}✓ tools${NC}"
        else
            TOOLS="${YELLOW}○ basic${NC}"
        fi
        
        echo -e "   $agent: $TEMP | $TOOLS"
    fi
done
echo ""

# Quick actions
echo -e "${BLUE}🚀 Quick Actions${NC}"
echo "   Update repo:  ./update_repo.sh \"your message\""
echo "   Test agents:  python test_agents.py --dry-run"
echo "   Run enhanced: export GEMINI_API_KEY=... && python arena_agent_enhanced.py"
echo ""

# GitHub link
echo -e "${BLUE}🔗 Links${NC}"
echo "   Repo: https://github.com/hp083625/agent-arena"
echo "   Issues: https://github.com/hp083625/agent-arena/issues"
echo ""

echo -e "${GREEN}🎮 Ready to level up!${NC}"
