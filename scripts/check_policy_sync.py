#!/usr/bin/env python3
"""Check that AI policy is properly synchronized across all files."""

import sys
from pathlib import Path

errors = []

if not Path("AI_POLICY.md").exists():
    errors.append("Missing AI_POLICY.md")

if not Path("AGENTS.md").exists():
    errors.append("Missing AGENTS.md")

agents_dir = Path(".qwen/agents")
if agents_dir.exists():
    for file in agents_dir.glob("*.md"):
        text = file.read_text(encoding="utf-8")
        if "AI_POLICY.md" not in text:
            errors.append(f"Missing reference in {file.name}")

if errors:
    print("ERRORS:")
    for e in errors:
        print("-", e)
    sys.exit(1)

print("OK: policy sync valid")
