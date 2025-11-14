#!/usr/bin/env python3
"""
Customize the Observable Agent Starter template for your new project.

This script automates the manual customization steps:
- Renames src/observable_agent_starter to src/yourproject
- Updates all imports throughout the codebase
- Updates pyproject.toml metadata
- Updates CI workflow references
- Updates README badges

Usage:
    python scripts/customize_template.py --name yourproject --author "Your Name" --email you@example.com
"""

import argparse
import re
import shutil
import sys
from pathlib import Path


def get_project_root() -> Path:
    """Get the project root directory."""
    return Path(__file__).parent.parent


def validate_project_name(name: str) -> bool:
    """Validate that project name is a valid Python package name."""
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        print(f"Error: Project name '{name}' must be lowercase, start with a letter,")
        print("and contain only letters, numbers, and underscores.")
        return False
    return True


def rename_package_directory(old_name: str, new_name: str, root: Path) -> bool:
    """Rename the package directory from old_name to new_name."""
    old_path = root / "src" / old_name
    new_path = root / "src" / new_name

    if not old_path.exists():
        print(f"Error: Source directory {old_path} does not exist.")
        return False

    if new_path.exists():
        print(f"Error: Target directory {new_path} already exists.")
        return False

    print(f"Renaming {old_path} -> {new_path}")
    shutil.move(str(old_path), str(new_path))
    return True


def update_imports_in_file(file_path: Path, old_name: str, new_name: str) -> None:
    """Update import statements in a single file."""
    content = file_path.read_text()

    # Replace import statements
    patterns = [
        (rf"from {old_name}", f"from {new_name}"),
        (rf"import {old_name}", f"import {new_name}"),
    ]

    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)

    file_path.write_text(content)


def update_all_imports(old_name: str, new_name: str, root: Path) -> None:
    """Update all import statements throughout the codebase."""
    print("\nUpdating imports in Python files...")

    # Directories to exclude
    exclude_dirs = {".git", ".venv", "venv", "__pycache__", ".pytest_cache", "node_modules", ".tox"}

    for py_file in root.rglob("*.py"):
        # Skip files in excluded directories
        if any(excluded in py_file.parts for excluded in exclude_dirs):
            continue

        update_imports_in_file(py_file, old_name, new_name)
        print(f"  Updated: {py_file.relative_to(root)}")


def update_pyproject_toml(
    new_name: str, author: str, email: str, description: str, root: Path
) -> None:
    """Update pyproject.toml with new project metadata."""
    print("\nUpdating pyproject.toml...")

    pyproject_path = root / "pyproject.toml"
    content = pyproject_path.read_text()

    # Update name
    content = re.sub(r'name = "observable-agent-starter"', f'name = "{new_name}"', content)

    # Update version to 0.1.0 (fresh start)
    content = re.sub(r'version = "[^"]+"', 'version = "0.1.0"', content)

    # Update description
    content = re.sub(r'description = "[^"]+"', f'description = "{description}"', content)

    # Update author
    content = re.sub(
        r"authors = \[.*?\]",
        f'authors = [\n  {{ name = "{author}", email = "{email}" }}\n]',
        content,
        flags=re.DOTALL,
    )

    # Update package path (Hatch uses paths relative to src/)
    content = re.sub(
        r'packages = \["observable_agent_starter"\]', f'packages = ["{new_name}"]', content
    )

    # Update script entry point
    content = re.sub(
        r'observable-agent = "observable_agent_starter\.cli:main"',
        f'{new_name} = "{new_name}.cli:main"',
        content,
    )

    # Update coverage source
    content = re.sub(r'source = \["src"\]', f'source = ["src/{new_name}"]', content)

    pyproject_path.write_text(content)
    print("  Updated: pyproject.toml")


def update_ci_workflow(new_name: str, root: Path) -> None:
    """Update GitHub Actions CI workflow."""
    print("\nUpdating CI workflow...")

    ci_path = root / ".github" / "workflows" / "ci.yml"
    if not ci_path.exists():
        print(f"  Warning: {ci_path} not found, skipping")
        return

    content = ci_path.read_text()

    # Update coverage flags
    content = re.sub(r"flags: observable-agent-starter", f"flags: {new_name}", content)

    # Update --cov argument
    content = re.sub(r"--cov=observable_agent_starter", f"--cov={new_name}", content)

    ci_path.write_text(content)
    print("  Updated: .github/workflows/ci.yml")


def update_readme(new_name: str, author: str, root: Path) -> None:
    """Update README.md badges and references."""
    print("\nUpdating README.md...")

    readme_path = root / "README.md"
    content = readme_path.read_text()

    # Update title
    content = re.sub(
        r"# Observable Agent Starter", f'# {new_name.replace("_", " ").title()}', content, count=1
    )

    # Update repo references in badges (update these with your actual GitHub username)
    # Note: User will need to manually update the GitHub org/username
    content = re.sub(r"ammons-datalabs/observable-agent-starter", f"{author}/{new_name}", content)

    # Update package name references
    content = re.sub(r"observable-agent-starter", new_name, content)

    content = re.sub(r"observable_agent_starter", new_name, content)

    readme_path.write_text(content)
    print("  Updated: README.md")


def update_init_version(new_name: str, root: Path) -> None:
    """Update __version__ in __init__.py."""
    print("\nUpdating __init__.py version...")

    init_path = root / "src" / new_name / "__init__.py"
    if not init_path.exists():
        print(f"  Warning: {init_path} not found, skipping")
        return

    content = init_path.read_text()

    # Update version to 0.1.0
    content = re.sub(r'__version__ = "[^"]+"', '__version__ = "0.1.0"', content)

    init_path.write_text(content)
    print(f"  Updated: {init_path.relative_to(root)}")


def update_cli(new_name: str, root: Path) -> None:
    """Update CLI prog name and print statements."""
    print("\nUpdating CLI prog name...")

    cli_path = root / "src" / new_name / "cli.py"
    if not cli_path.exists():
        print(f"  Warning: {cli_path} not found, skipping")
        return

    content = cli_path.read_text()

    # Update prog argument in ArgumentParser
    content = re.sub(r'prog="observable-agent"', f'prog="{new_name}"', content)

    # Update print statement
    content = re.sub(
        r'print\(f"observable-agent v\{__version__\}"\)',
        f'print(f"{new_name} v{{__version__}}")',
        content,
    )

    cli_path.write_text(content)
    print(f"  Updated: {cli_path.relative_to(root)}")


def update_makefile(new_name: str, root: Path) -> None:
    """Update Makefile coverage target and remove non-existent modules."""
    print("\nUpdating Makefile...")

    makefile_path = root / "Makefile"
    if not makefile_path.exists():
        print(f"  Warning: {makefile_path} not found, skipping")
        return

    content = makefile_path.read_text()

    # Update coverage target
    content = re.sub(r"--cov=observable_agent_starter", f"--cov={new_name}", content)

    # Comment out non-existent module references
    content = re.sub(
        r"^(\s*\$\(PYTHON\) -m observable_agent_starter\.agents\.routing)",
        r"# \1  # Template: Customize with your module",
        content,
        flags=re.MULTILINE,
    )

    content = re.sub(
        r"^(\s*\$\(VENV\)/bin/uvicorn observable_agent_starter\.servers\.api:app)",
        r"# \1  # Template: Customize with your module",
        content,
        flags=re.MULTILINE,
    )

    makefile_path.write_text(content)
    print("  Updated: Makefile")


def update_documentation_files(old_name: str, new_name: str, root: Path) -> None:
    """Update import examples in documentation files."""
    print("\nUpdating documentation files...")

    doc_files = [
        root / "docs" / "architecture.md",
        root / "docs" / "how-to" / "extend-observability-provider.md",
        root / "CONTRIBUTING.md",
    ]

    for doc_file in doc_files:
        if not doc_file.exists():
            print(f"  Warning: {doc_file} not found, skipping")
            continue

        content = doc_file.read_text()

        # Update import statements and package references
        content = re.sub(rf"\bfrom {old_name}\b", f"from {new_name}", content)

        content = re.sub(rf"\bimport {old_name}\b", f"import {new_name}", content)

        # Update path references
        content = re.sub(rf"\bsrc/{old_name}/", f"src/{new_name}/", content)

        # Update package name with dashes
        content = re.sub(r"\bobservable-agent-starter\b", new_name.replace("_", "-"), content)

        doc_file.write_text(content)
        print(f"  Updated: {doc_file.relative_to(root)}")


def update_init_docstring(new_name: str, root: Path) -> None:
    """Update package docstring in __init__.py."""
    print("\nUpdating __init__.py docstring...")

    init_path = root / "src" / new_name / "__init__.py"
    if not init_path.exists():
        print(f"  Warning: {init_path} not found, skipping")
        return

    content = init_path.read_text()

    # Update docstring to be generic
    content = re.sub(
        r'"""Observable Agent Starter - DSPy agent framework with observability\."""',
        f'"""{new_name} - LLM agent with Langfuse observability."""',
        content,
    )

    init_path.write_text(content)
    print(f"  Updated: {init_path.relative_to(root)}")


def update_example_dependencies(new_name: str, root: Path) -> None:
    """Update example pyproject.toml dependencies - comment out with install instructions."""
    print("\nUpdating example dependencies...")

    example_pyprojects = [
        root / "examples" / "coding_agent" / "pyproject.toml",
        root / "examples" / "influencer_assistant" / "pyproject.toml",
    ]

    for pyproject in example_pyprojects:
        if not pyproject.exists():
            print(f"  Warning: {pyproject} not found, skipping")
            continue

        content = pyproject.read_text()

        # Comment out observable-agent-starter dependency with instructions
        content = re.sub(
            r'(\s+)"observable-agent-starter",',
            r"\1# Parent package dependency - install with: pip install -e ../..",
            content,
        )

        pyproject.write_text(content)
        print(f"  Updated: {pyproject.relative_to(root)}")


def create_env_example(root: Path) -> None:
    """Create .env.example if it doesn't exist."""
    env_example = root / ".env.example"
    if env_example.exists():
        return

    print("\nCreating .env.example...")
    env_example.write_text("""# OpenAI Configuration
OPENAI_API_KEY=your-api-key-here
OPENAI_BASE_URL=https://api.openai.com/v1
OPENAI_TEMPERATURE=0.7

# Langfuse Configuration (Optional - comment out to disable)
LANGFUSE_PUBLIC_KEY=your-public-key
LANGFUSE_SECRET_KEY=your-secret-key
LANGFUSE_HOST=https://cloud.langfuse.com
""")
    print("  Created: .env.example")


def main(argv: list[str] | None = None) -> int:
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Customize the Observable Agent Starter template for your project"
    )
    parser.add_argument(
        "--name",
        required=True,
        help="New project name (lowercase, underscores allowed, e.g., 'my_project')",
    )
    parser.add_argument("--author", required=True, help="Your name or GitHub username")
    parser.add_argument("--email", required=True, help="Your email address")
    parser.add_argument("--description", default="", help="Project description (optional)")

    args = parser.parse_args(argv)

    # Validate project name
    if not validate_project_name(args.name):
        return 1

    # Set default description if not provided
    description = args.description or f"{args.name} - Built with Observable Agent Starter"

    root = get_project_root()
    old_name = "observable_agent_starter"

    print("\nCustomizing Observable Agent Starter template")
    print(f"  New project name: {args.name}")
    print(f"  Author: {args.author} <{args.email}>")
    print(f"  Description: {description}")
    print()

    # Confirm before proceeding
    response = input("Proceed with customization? [y/N]: ")
    if response.lower() != "y":
        print("Cancelled.")
        return 1

    try:
        # Step 1: Rename package directory
        if not rename_package_directory(old_name, args.name, root):
            return 1

        # Step 2: Update all imports
        update_all_imports(old_name, args.name, root)

        # Step 3: Update pyproject.toml
        update_pyproject_toml(args.name, args.author, args.email, description, root)

        # Step 4: Update CI workflow
        update_ci_workflow(args.name, root)

        # Step 5: Update README
        update_readme(args.name, args.author, root)

        # Step 6: Update __init__.py version and docstring
        update_init_version(args.name, root)
        update_init_docstring(args.name, root)

        # Step 7: Update CLI prog name
        update_cli(args.name, root)

        # Step 8: Update Makefile
        update_makefile(args.name, root)

        # Step 9: Update documentation files
        update_documentation_files(old_name, args.name, root)

        # Step 10: Update example dependencies
        update_example_dependencies(args.name, root)

        # Step 11: Create .env.example
        create_env_example(root)

        print("\nCustomization complete!")
        print("\nNext steps:")
        print("  1. Review changes: git diff")
        print("  2. Update README.md with your project description")
        print("  3. Copy .env.example to .env and add your API keys")
        print("  4. Install: make dev")
        print("  5. Test: make test")
        print(f"  6. Verify CLI works: {args.name} --version")
        print("  7. Commit: git add . && git commit -m 'chore: customize template'")

        return 0

    except Exception as e:
        print(f"\nError during customization: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
