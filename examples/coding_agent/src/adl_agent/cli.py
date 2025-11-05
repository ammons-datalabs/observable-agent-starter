"""CLI for the ADL coding agent."""

import argparse
import os
import sys
import pathlib
import subprocess
from adl_agent.harness import make_patch_and_test, run_command
from adl_agent.agent import CodeAgent
from observable_agent_starter import create_observability
import dspy

__version__ = "0.1.0"


def setup_dspy():
    """Configure DSPy with the appropriate LLM."""
    model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

    # Check for appropriate API key based on model
    if model.startswith("anthropic/"):
        if not os.getenv("ANTHROPIC_API_KEY"):
            print("❌ Error: ANTHROPIC_API_KEY not set but required for Anthropic models")
            print("   Set it in your .env file or export ANTHROPIC_API_KEY=your-key")
            sys.exit(1)
    elif model.startswith("openai/") or model.startswith("gpt-"):
        if not os.getenv("OPENAI_API_KEY"):
            print("❌ Error: OPENAI_API_KEY not set but required for OpenAI models")
            print("   Set it in your .env file or export OPENAI_API_KEY=your-key")
            sys.exit(1)
    else:
        # Generic check - at least one should be set
        if not os.getenv("OPENAI_API_KEY") and not os.getenv("ANTHROPIC_API_KEY"):
            print("⚠️  Warning: No API keys found. Agent may fail.")
            print("   Set OPENAI_API_KEY or ANTHROPIC_API_KEY in your .env file")

    # Check for Langfuse credentials (optional but recommended)
    langfuse_keys = ["LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_HOST"]
    langfuse_configured = all(os.getenv(key) for key in langfuse_keys)

    if not langfuse_configured:
        print("ℹ️  Note: Langfuse tracing not configured (optional)")
        print("   Set LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST for observability")
        print()

    lm = dspy.LM(model)
    dspy.configure(lm=lm)

    print(f"🧠 Model: {model}")
    if langfuse_configured:
        print("📊 Tracing: Enabled (Langfuse)")
    print()


def main():
    parser = argparse.ArgumentParser(
        "adl-agent", description="Autonomous coding agent with DSPy + Langfuse"
    )
    parser.add_argument("task", nargs="?", help="Engineering task description")
    parser.add_argument("--repo", help="Path to target repository")
    parser.add_argument(
        "--allow",
        nargs="+",
        default=["src/**/*.py", "tests/**/*.py"],
        help="Glob patterns for allowed files",
    )
    parser.add_argument("--branch-prefix", default="agent", help="Branch name prefix")
    parser.add_argument("--dry-run", action="store_true", help="Generate patch but don't apply")
    parser.add_argument("--open-pr", action="store_true", help="Open PR (requires gh CLI)")
    parser.add_argument("--version", action="version", version=f"adl-agent {__version__}")
    args = parser.parse_args()

    # Check required arguments
    if not args.task:
        parser.error("task is required")
    if not args.repo:
        parser.error("--repo is required")

    repo = pathlib.Path(args.repo).resolve()

    if not repo.exists() or not (repo / ".git").exists():
        print(f"❌ Error: {repo} is not a git repository")
        sys.exit(1)

    # Setup DSPy
    setup_dspy()

    # Save current branch
    try:
        current_branch = run_command(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=str(repo)
        ).stdout.strip()
    except subprocess.CalledProcessError:
        current_branch = "main"

    # Create branch name
    import re

    safe_task = re.sub(r"[^\w\s-]", "", args.task)
    safe_task = re.sub(r"[-\s]+", "-", safe_task)
    branch = f"{args.branch_prefix}/{safe_task.lower()[:50]}"

    print(f"🌿 Creating branch: {branch}")

    # Try to create branch, handle if it exists
    try:
        run_command(["git", "checkout", "-b", branch], cwd=str(repo))
    except subprocess.CalledProcessError:
        # Branch might exist, try to check it out
        try:
            run_command(["git", "checkout", branch], cwd=str(repo))
            print("⚠️  Branch already exists, checked it out")
        except subprocess.CalledProcessError as e:
            print(f"❌ Error: Could not create or checkout branch: {e}")
            print(f"   You may have uncommitted changes. Staying on {current_branch}")
            # Continue without switching branches
            branch = current_branch

    # Initialize agent with observability
    observability = create_observability("code-agent-generate", configure_lm=False)
    agent = CodeAgent(observability=observability)

    # Generate and test patch
    print(f"🤖 Agent working on task: {args.task}")
    print(f"📁 Repository: {repo}")
    print(f"📋 Allowed patterns: {args.allow}")
    print()

    patch, tests_passed, output = make_patch_and_test(
        task=args.task,
        repo_path=str(repo),
        allow_globs=args.allow,
        agent=agent,
        dry_run=args.dry_run,
    )

    print(output)
    print()

    if not patch:
        print("❌ No patch generated. Check logs.")
        sys.exit(2)

    if args.dry_run:
        print("✅ Dry run complete. Patch:")
        print(patch[:500] + "..." if len(patch) > 500 else patch)
        sys.exit(0)

    # Commit if tests passed
    if tests_passed:
        print("✅ Tests passed! Creating commit...")
        try:
            run_command(["git", "add", "-A"], cwd=str(repo))
            commit_msg = f"agent: {args.task}\n\n🤖 Generated by ADL Coding Agent"
            run_command(["git", "commit", "-m", commit_msg], cwd=str(repo))
            print(f"✅ Commit created on branch: {branch}")

            if args.open_pr:
                print("🚀 Opening PR...")
                # Ensure label exists
                try:
                    run_command(
                        ["gh", "label", "create", "agent-generated", "--color", "E99695"],
                        cwd=str(repo),
                        check=False,
                    )
                except Exception:
                    pass  # Label may already exist

                # Push branch
                run_command(["git", "push", "-u", "origin", branch], cwd=str(repo))

                # Create PR
                run_command(
                    ["gh", "pr", "create", "--fill", "--label", "agent-generated"], cwd=str(repo)
                )
                print("✅ PR opened successfully!")
        except subprocess.CalledProcessError as e:
            print(f"❌ Git operation failed: {e}")
            sys.exit(1)
    else:
        print("❌ Tests failed. Branch left for manual review.")
        print(f"   Run: cd {repo} && git diff")
        sys.exit(1)


if __name__ == "__main__":
    main()
