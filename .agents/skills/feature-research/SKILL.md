# SKILL: Feature Research

## Purpose
A structured workflow for researching complex features before implementation by combining
web search, library documentation, and internal knowledge synthesis.

## When to Use
- Implementing a feature involving unfamiliar libraries or APIs
- Evaluating multiple approaches to solve a problem
- Upgrading dependencies and understanding breaking changes
- Investigating production issues with unclear root causes

## MCP Servers Used
- `duckduckgo` — Web search for articles, Stack Overflow, blog posts
- `context7` — Fresh, up-to-date library documentation
- `notebooklm` — Internal knowledge management and synthesis

---

## Workflow

### Step 1: Define the Research Question
Before searching, clearly articulate:
- **What** do we need to implement or understand?
- **Why** is research needed? (unfamiliar API, multiple approaches, etc.)
- **What** would a successful answer look like?

### Step 2: Check Internal Knowledge First
```
# Read existing project docs
Tool: filesystem → read docs/techContext.md
Tool: filesystem → read docs/decisionLog.md
Tool: filesystem → read .antigravityrules

# Check if NotebookLM has relevant notebooks
Tool: mcp_notebooklm_notebook_list

# Query existing notebooks if relevant
Tool: mcp_notebooklm_notebook_query
  notebook_id: "<id>"
  query: "<research question>"
```

### Step 3: Fetch Fresh Library Documentation
```
# Resolve the library ID
Tool: mcp_context7_resolve-library-id
  libraryName: "Flask"  # or whatever library
  query: "how to implement <feature>"

# Query the documentation
Tool: mcp_context7_query-docs
  libraryId: "<resolved_id>"
  query: "specific API usage question"
```

> **Rule:** Always use `context7` for library-specific questions rather than relying
> on training data. Libraries update frequently.

### Step 4: Web Search for Patterns and Examples
```
# Search for implementation patterns
Tool: mcp_duckduckgo_search
  query: "Flask <feature> best practices 2025"
  max_results: 5

# Read promising results
Tool: mcp_duckduckgo_fetch_content
  url: "<result_url>"
  max_length: 5000
```

### Step 5: Synthesize Findings
Create or update a NotebookLM notebook with research findings:
```
# Create research notebook
Tool: mcp_notebooklm_notebook_create
  title: "Research: <feature_name>"

# Add findings as sources
Tool: mcp_notebooklm_notebook_add_text
  notebook_id: "<id>"
  title: "Context7 Docs"
  content: "<documentation_content>"

Tool: mcp_notebooklm_notebook_add_url
  notebook_id: "<id>"
  url: "<relevant_article_url>"

# Ask synthesis questions
Tool: mcp_notebooklm_notebook_query
  notebook_id: "<id>"
  query: "What is the recommended approach for <feature>?"
```

### Step 6: Document Decision
Write findings to `docs/decisionLog.md` as an ADR:
- Context: What problem were we solving?
- Options considered: What approaches were evaluated?
- Decision: What was chosen and why?
- Consequences: What are the trade-offs?

### Step 7: Update Active Context
Update `docs/activeContext.md` with:
- Research summary
- Recommended approach
- Implementation plan for the Coder agent

---

## Best Practices

1. **Context7 first, DuckDuckGo second** — Library docs are more authoritative than blog posts
2. **Limit scope** — Don't fall into research rabbit holes; timebox to 3 search iterations
3. **Verify versions** — Ensure found examples match our dependency versions (check `requirements.txt`)
4. **Cross-reference** — If Context7 and a blog post disagree, trust the official docs
5. **Document everything** — Future agents should benefit from this research
