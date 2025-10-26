# Coding Agent Demo

Quick demonstration of the coding agent in action.

## Setup

```bash
# From the coding_agent directory
pip install -e .

# Initialize the demo repository (first time only)
cd demo
./setup_demo.sh
cd ..
```

## Run the Demo

```bash
# Simple task: Add multiply function with docstring
adl-agent "Add a multiply function with docstring to calculator.py" \
  --repo demo/sample_project \
  --allow "*.py"

# The agent will:
# 1. Analyze the repository
# 2. Generate a code patch
# 3. Apply the patch
# 4. Run ruff linting
# 5. Run pytest tests
# 6. Create a commit if tests pass
```

## What to Expect

The agent will:
- ✅ Read the existing code
- ✅ Generate a patch adding the multiply function
- ✅ Add a proper docstring
- ✅ Lint the code with ruff
- ✅ Run existing tests (they should still pass)
- ✅ Create a git commit with the changes

## View the Results

```bash
cd demo/sample_project
git log -1 --stat
git diff HEAD~1
```

## Clean Up

```bash
# Reset the demo repo for another run
cd demo/sample_project
git reset --hard HEAD~1
```
