#!/usr/bin/env bash
set -euo pipefail

REPO_URL=${1:-}
if [ -z "$REPO_URL" ]; then
  echo "Usage: ./scripts/git_publish_template.sh https://github.com/<YOUR_ID>/fabmind-agent.git"
  exit 1
fi

git init
git add .
git commit -m "PR-00 initialize FabMind Agent repository"
git branch -M main
git remote add origin "$REPO_URL"
git push -u origin main
