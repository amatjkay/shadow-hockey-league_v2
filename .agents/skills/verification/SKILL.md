# Skill: Stability Verification

## Goal

Automate verification of system stability, performance, and data integrity.

## Workflow

1. **Linting**:
   - Run `make lint` (Flake8).
   - Run `mypy .` (Type checking).

2. **Testing**:
   - Run `make test` (Pytest).
   - Verify coverage: `pytest --cov`.

3. **Performance Audit**:
   - Run `make benchmark` (`scripts/benchmark.py`).
   - Targets: Leaderboard generation < 1ms.

4. **Data Integrity**:
   - Run `make audit` (`scripts/audit_data.py`).
   - Targets: 100% formula consistency.
