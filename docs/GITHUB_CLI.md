# GitHub CLI Essential Commands for AI

Use these commands via `run_command` to interact with the repository.

## 1. Workflows & Actions (CI/CD)
- `gh run list --limit 5` : List recent workflow runs.
- `gh run view [ID] --log` : View logs for a specific failed run.
- `gh run watch [ID]` : Monitor a running workflow.

## 2. Pull Requests
- `gh pr list` : View open PRs.
- `gh pr create --title "[Title]" --body "[Body]"` : Create a new PR from current branch.
- `gh pr status` : Check status of the current branch PR.
- `gh pr view [ID] --web` : (Inform user) Open PR in browser.

## 3. Issues
- `gh issue list` : List open issues.
- `gh issue create --title "[Title]" --body "[Body]"` : Create a new task/bug report.
- `gh issue view [ID]` : Read issue details and comments.

## 4. Repository Info
- `gh repo view --web` : (Inform user) Open repo on GitHub.
- `gh auth status` : Verify login.
