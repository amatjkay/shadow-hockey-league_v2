# Skill: System Stability Verification

## Description
One-command check to ensure the system is stable, performant, and consistent.

## Steps
1. **Linting**: Run `make lint` (isort, black, flake8, mypy).
2. **Testing**: Run `make test` (pytest).
3. **Audit**: Run `make audit` (data integrity).
4. **Performance**: Run `make benchmark` (latency check).

## Output
A summary report confirming all checks passed or identifying specific failures.
