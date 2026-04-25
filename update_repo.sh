#!/bin/bash
# update_repo.sh - Helper script to push updates to GitHub
# Usage: ./update_repo.sh "commit message"

set -e

REPO_URL="https://github.com/hp083625/agent-arena"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🤖 Agent Arena - Repository Updater${NC}"
echo "===================================="
echo ""

# Check if message provided
if [ -z "$1" ]; then
    echo -e "${YELLOW}Usage: ./update_repo.sh \"Your commit message\"${NC}"
    echo ""
    echo "Examples:"
    echo "  ./update_repo.sh \"fix: handle MCP timeout error\""
    echo "  ./update_repo.sh \"feat: add new web search provider\""
    echo "  ./update_repo.sh \"perf: improve solution generation speed\""
    exit 1
fi

COMMIT_MSG="$1"

# Check git status
echo -e "${BLUE}📋 Checking git status...${NC}"
git status --short

# Check for untracked Python files
UNTRACKED=$(git ls-files --others --exclude-standard | grep -E '\.py$' || true)
if [ ! -z "$UNTRACKED" ]; then
    echo ""
    echo -e "${YELLOW}⚠️  Untracked Python files detected:${NC}"
    echo "$UNTRACKED"
    echo ""
    read -p "Add all untracked files? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        git add -A
    fi
else
    git add -A
fi

# Check if there are changes to commit
if git diff --cached --quiet; then
    echo -e "${YELLOW}⚠️  No changes to commit${NC}"
    exit 0
fi

# Commit
echo ""
echo -e "${BLUE}📝 Committing with message:${NC}"
echo "   $COMMIT_MSG"
git commit -m "$COMMIT_MSG"

# Pull latest changes (in case of remote updates)
echo ""
echo -e "${BLUE}🔄 Pulling latest changes...${NC}"
git pull origin main --rebase || true

# Push
echo ""
echo -e "${BLUE}🚀 Pushing to GitHub...${NC}"
git push origin main

# Success message
echo ""
echo -e "${GREEN}✅ Successfully pushed to GitHub!${NC}"
echo ""
echo -e "${BLUE}📊 Repository Stats:${NC}"
echo "   URL: $REPO_URL"
echo "   Commits: $(git rev-list --count HEAD)"
echo "   Last commit: $(git log -1 --format=%cd --date=short)"
echo ""
echo -e "${GREEN}🎮 Keep leveling up!${NC}"
