# Contributing to Observable Agent Starter

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## Quick Start

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/observable-agent-starter.git
cd observable-agent-starter

# 2. Set up development environment
make dev

# 3. Install pre-commit hooks
make precommit

# 4. Run tests
make test
```

## Development Workflow

### 1. Create a Branch

```bash
git checkout -b feature/your-feature-name
```

Use prefixes:
- `feat/` - New features
- `fix/` - Bug fixes
- `docs/` - Documentation changes
- `test/` - Test additions or fixes
- `refactor/` - Code refactoring
- `ci/` - CI/CD changes

### 2. Make Changes

Follow these guidelines:

- **Test-Driven Development**: Write tests before implementing functionality when practical
- **Code Coverage**: Maintain 85%+ coverage for core framework code
- **Code Style**: Run `make lint` before committing
- **Type Checking**: Run `make type` to verify type annotations

### 3. Run Quality Checks

```bash
# Run all checks
make lint          # Ruff linting
make type          # Pyright type checking
make test          # All tests
make coverage      # Generate coverage report
```

### 4. Commit Your Changes

Follow conventional commit format:

```
type: brief description

Detailed explanation if needed

- Bullet points for specifics
- Reference issues with #123
```

**Commit types:**
- `feat` - New feature
- `fix` - Bug fix
- `docs` - Documentation
- `test` - Test changes
- `refactor` - Code refactoring
- `ci` - CI/CD changes
- `chore` - Maintenance tasks

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
```

Create a PR with:
- Clear title describing the change
- Description of what and why
- Reference any related issues
- Screenshots/logs if relevant

## Code Standards

### Python Style

- Follow existing code patterns
- Use type hints for function signatures
- Maximum line length: 100 characters
- Use Ruff for linting and formatting

### Testing

- Write tests for all new functionality
- Test edge cases and error conditions
- Use descriptive test names: `test_function_does_what_when_condition`
- Maintain 85%+ coverage for core code

Example test structure:

```python
def test_configure_lm_with_api_key(monkeypatch):
    """Should configure LM when API key is set."""
    monkeypatch.setenv("OPENAI_API_KEY", "test-key")

    result = configure_lm_from_env()

    assert result is True
```

### Documentation

- Update README.md if adding features
- Add docstrings to public functions
- Update relevant docs/ files
- Include code examples for new features

## Project Structure

```
observable-agent-starter/
├── src/observable_agent_starter/  # Core framework
│   ├── base_agent.py              # BaseAgent implementation
│   ├── config.py                  # Configuration utilities
│   └── __init__.py
├── examples/                       # Example implementations
│   ├── coding_agent/              # Code generation example
│   └── influencer_assistant/      # Content ideation example
├── tests/                          # Framework tests
├── docs/                           # Documentation
└── .github/workflows/              # CI/CD workflows
```

## Testing Guidelines

### Core Framework Tests

Located in `tests/`:
- Must maintain 85%+ coverage
- Run on every PR via CI
- Test both happy paths and edge cases

### Example Tests

Located in `examples/*/tests/`:
- Test example-specific functionality
- No coverage requirements
- Should pass in CI

### Running Tests

```bash
# Core framework tests only
pytest tests/ -v

# All tests (includes examples)
make test

# With coverage
make coverage

# Specific test file
pytest tests/test_config.py -v
```

## Pull Request Process

1. **Before Submitting:**
   - All tests pass locally
   - Pre-commit hooks pass
   - Coverage maintained at 85%+
   - Documentation updated

2. **PR Requirements:**
   - Clear description of changes
   - Tests for new functionality
   - No unrelated changes
   - Conventional commit format

3. **Review Process:**
   - CI checks must pass
   - At least one maintainer approval
   - Address review comments
   - Squash commits if requested

4. **After Merge:**
   - Delete your branch
   - Pull latest main
   - Celebrate your contribution!

## Getting Help

- Open an issue for bugs or feature requests
- Ask questions in discussions
- Tag maintainers for urgent issues

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
