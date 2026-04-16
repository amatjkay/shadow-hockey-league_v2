# Debug Skill

When to use: bugs, crashes, unexpected behavior.

Core instructions:
- Reproduce the bug and write a failing test first.
- Form 3 hypotheses, each with confirm/invalidation signals.
- Log key state before fix; verify with test.
- Keep changes minimal; run full test suite after.

Template:
1. Reproduce steps.
2. Hypothesis A/B/C with signals.
3. Diagnostic commands/logs.
4. Fix and test.