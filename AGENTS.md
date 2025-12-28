# advanced-yaml Agent Guidelines

This document provides comprehensive instructions for AI agents operating within the `advanced-yaml` repository. Follow these guidelines strictly to ensure code quality, consistency, and stability.

## 1. Environment & Toolchain

The project uses **uv** for dependency management and task execution. All commands should be executed via `uv run`.

### Core Commands
| Action | Command | Description |
|--------|---------|-------------|
| **Unit Tests** | `uv run pytest` | Run all unit tests with coverage |
| **BDD Tests** | `uv run behave` | Run acceptance tests (feature files) |
| **Linting** | `uv run ruff check src tests` | Check for linting errors |
| **Formatting** | `uv run ruff format src tests` | Auto-format code |
| **Type Check** | `uv run pyright` | Run static type checking |
| **Build** | `uv run python -m build` | Build the package |
| **Docs** | `uv run mkdocs build` | Build documentation site |
| **All CI** | `./ci.sh all` | Run full CI pipeline (test, format, lint, type, bdd, build) |

### Running Specific Tests
*   **Single Test File:** `uv run pytest tests/yasl/test_yasl.py`
*   **Single Test Function:** `uv run pytest tests/yasl/test_yasl.py::test_load_schema`
*   **Specific BDD Feature:** `uv run behave features/yasl/yasl_basic.feature`

## 2. Code Style & Conventions

### Python Standards
*   **Style Guide:** Adhere strictly to **PEP 8**.
*   **Formatter:** We use `ruff`. Always run `uv run ruff format` before submitting changes.
*   **Imports:**
    *   Sort imports using `ruff` (automated).
    *   Use absolute imports for internal modules (e.g., `from yasl.core import Schema` instead of `from .core import Schema`).
    *   Group standard library, third-party, and local imports separately.

### Type Safety
*   **Strong Typing:** All new code **must** include type hints.
*   **Validation:** Use `pydantic` for data validation and schema definitions where appropriate.
*   **Check:** Verify types with `uv run pyright`.
*   **Generics:** Use modern generic syntax (e.g., `list[str]` instead of `List[str]`) where supported by Python 3.12+.

### Naming Conventions
*   **Variables/Functions:** `snake_case` (e.g., `validate_schema`, `user_input`)
*   **Classes:** `PascalCase` (e.g., `SchemaValidator`, `QueryEngine`)
*   **Constants:** `UPPER_CASE` (e.g., `MAX_RETRIES`, `DEFAULT_CONFIG`)
*   **Private Members:** Prefix with `_` (e.g., `_internal_cache`)

### Error Handling
*   **Exceptions:** Use specific, custom exception classes (inherit from `Exception` or base project exceptions) rather than generic `Exception`.
*   **Context:** Catch exceptions narrowly and provide context when re-raising.
*   **Fail Fast:** Validate inputs early.

## 3. Project Structure

The project is modularized by functionality:
*   `src/yasl/`: **YASL** (YAML Advanced Scripting Language) - Schema definition & verification.
*   `src/yaql/`: **YAQL** (YAML Advanced Query Language) - Querying capabilities.
*   `src/yarl/`: **YARL** (YAML Advanced Reporting Language) - Analysis & reporting.
*   `src/yatl/`: **YATL** (YAML Advanced Transformation Language) - Structure transformation.
*   `tests/`: Unit tests mirroring the `src` structure.
*   `features/`: Gherkin feature files for BDD.

## 4. Testing Guidelines

*   **TDD/BDD:** Adopt a Test-Driven or Behavior-Driven approach. Write the test or feature file *before* implementing the logic.
*   **Coverage:** Maintain high test coverage (fail under 75% is configured).
*   **Mocking:** Use `unittest.mock` or `pytest-mock` to isolate external dependencies (filesystem, network).
*   **Fixtures:** Use `pytest` fixtures for setup/teardown and reusable test data.

## 5. Documentation & Comments

*   **Docstrings:** Use Google-style docstrings for public modules, classes, and methods.
*   **Why vs. What:** Comments should explain *why* a complex piece of logic exists, not *what* the code is doing (the code should be self-documenting).
*   **No Chat:** Do not add conversational comments or signature blocks.

## 6. Workflow Checklist for Agents

1.  **Analyze:** Read related files and `AGENTS.md` before starting.
2.  **Safety:** If modifying filesystem/running shell commands, explain the impact first.
3.  **Plan:** Formulate a plan involving necessary changes and test coverage.
4.  **Implement:** Write code, following the conventions above.
5.  **Verify:**
    *   Run format: `uv run ruff format src tests`
    *   Run lint: `uv run ruff check src tests`
    *   Run type check: `uv run pyright`
    *   Run tests: `uv run pytest` (and `uv run behave` if applicable)
6.  **Refine:** Fix any issues found during verification.

## 7. Copilot/AI Specifics

*   **Context:** Consider the surrounding code and project structure.
*   **Dependencies:** Do not introduce new dependencies without explicit instruction. Use existing libraries (`ruamel.yaml`, `pydantic`, etc.).
*   **Hallucinations:** Verify library APIs (especially `ruamel.yaml` quirks) before generating code.
