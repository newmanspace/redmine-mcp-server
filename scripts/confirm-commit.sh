#!/bin/bash
# Interactive confirmation for git operations

set -e

echo "Git Status:"
git status --short

echo ""
read -p "Confirm commit? (y/n): " confirm

if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Commit cancelled"
    exit 1
fi

read -p "Enter commit message (format: type: description): " message

if [[ ! $message =~ ^(feat|fix|refactor|docs|style|test|chore): ]]; then
    echo "ERROR: Commit message must start with type prefix"
    echo "Valid types: feat, fix, refactor, docs, style, test, chore"
    echo "Example: feat: add new feature"
    exit 1
fi

git add -A
git commit -m "$message"

echo ""
read -p "Push to remote? (y/n): " push_confirm

if [ "$push_confirm" = "y" ] || [ "$push_confirm" = "Y" ]; then
    git push origin develop
    echo "Done: Committed and pushed"
else
    echo "Done: Committed but not pushed"
    echo "Run 'git push origin develop' to push"
fi
