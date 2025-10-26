#!/bin/bash
# Setup script for the coding agent demo

cd "$(dirname "$0")/sample_project"

# Initialize git if not already done
if [ ! -d ".git" ]; then
    git init
    git config user.email "demo@example.com"
    git config user.name "Demo User"
    git add .
    git commit -m "Initial commit: calculator with tests"
    echo "✅ Demo repository initialized"
else
    echo "✅ Demo repository already initialized"
fi
