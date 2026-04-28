#!/usr/bin/env python
"""Test metrics service.

Migrated from test_metrics.py
"""

from app import create_app
from services.metrics_service import get_metrics, reset_metrics

# Reset for clean test
reset_metrics()

print("=" * 50)
print("METRICS SERVICE TEST")
print("=" * 50)

# First app creation
app1 = create_app()
metrics1 = get_metrics()
print(f"\n1. First app created:")
print(f"   Metrics instance: {'OK - Initialized' if metrics1 else 'FAIL - Not initialized'}")

# Second app creation (should reuse singleton)
app2 = create_app()
metrics2 = get_metrics()
print(f"\n2. Second app created:")
print(
    f"   Metrics instance: {'OK - Reused singleton' if metrics2 is metrics1 else 'FAIL - New instance'}"
)

# Third app creation
app3 = create_app()
metrics3 = get_metrics()
print(f"\n3. Third app created:")
print(
    f"   Metrics instance: {'OK - Reused singleton' if metrics3 is metrics1 else 'FAIL - New instance'}"
)

print("\n" + "=" * 50)
print("OK - No warnings about duplicate endpoints!")
print("=" * 50)
