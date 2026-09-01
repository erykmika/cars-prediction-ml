# AI Code Review Rules

## General Principles

1. **Focus on Changed Code Only** - Only report issues in lines that were added or modified in this PR.
2. **Actionable Feedback** - Every finding must include a specific suggested fix.
3. **High Confidence Only** - Only report issues you are confident about (>= 0.85 confidence).
4. **No Style Nitpicks** - Do not comment on subjective style preferences unless they violate project conventions.

## Code Quality Issues to Report

### Critical (Severity: critical)
- Security vulnerabilities (SQL injection, XSS, path traversal, hardcoded secrets)
- Data loss or corruption bugs
- Authentication/authorization bypasses
- Unhandled exceptions that crash the application

### High (Severity: high)
- Logic errors that produce incorrect results
- Performance issues with O(n²) or worse complexity in hot paths
- Memory leaks or resource leaks
- Missing error handling for external API calls
- Race conditions

### Medium (Severity: medium)
- Incorrect type hints or missing type annotations
- Violations of project-specific patterns (e.g., not using Pydantic models for API schemas)
- Dead code or unreachable code
- Inefficient database queries (N+1, missing indexes)
- Missing input validation

### Low (Severity: low)
- Minor code duplication that could be refactored
- Missing docstrings for public functions
- Inconsistent naming within the changed code
- Unused imports in modified files

## Project-Specific Rules

### Python / FastAPI (api/)
- Use Pydantic models for all request/response schemas
- All API endpoints must have proper error handling with HTTPException
- Database sessions must be properly managed (use dependency injection)
- Validate all user inputs before database operations
- Use async/await correctly for I/O operations

### ML Training (training/)
- Validate data schemas before training
- Log model metrics and hyperparameters
- Handle missing/invalid data gracefully
- Use proper train/validation/test splits
- Save model artifacts with versioning

### General Python
- Follow PEP 8 (enforced by ruff)
- Use type hints for all function signatures
- Prefer `pathlib` over `os.path`
- Use `asyncio` for concurrent I/O
- Avoid mutable default arguments

## What NOT to Report

- Missing comments on obvious code
- Variable naming that follows conventions but isn't your preference
- Refactoring suggestions that don't fix a bug
- Issues in unchanged code
- Speculative issues without evidence in the diff