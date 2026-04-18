#!/usr/bin/env python3
"""Verify Cursor rule adaptations maintain core policy integrity."""

from pathlib import Path

def main():
    print("Verifying Cursor rule adaptations...\n")

    c = Path("AI_POLICY_CURSOR.md").read_text()
    r = Path(".cursorrules").read_text()

    checks = [
        ("AI_POLICY.md referenced", "AI_POLICY.md" in c),
        ("Single source of truth", "single source of truth" in c.lower()),
        ("Workflow keywords", all(k in r for k in ["ANALYST", "ARCHITECT", "DEVELOPER", "QA_TESTER", "CODE_REVIEWER", "@save"])),
        ("Safety rules", all(k in r for k in ["silent breaking", "unrelated modifications", "minimal reversible", "REQUIRE `.env`"])),
        ("Agent mapping table", "|" in Path(".qwen/agents/cursor_adapters.md").read_text()),
    ]

    ok = all(v for _, v in checks)
    for name, passed in checks:
        print(f"{'✓' if passed else '✗'} {name}")

    if not ok:
        raise SystemExit(1)
    print("\nAll verifications passed.")

if __name__ == "__main__":
    main()
