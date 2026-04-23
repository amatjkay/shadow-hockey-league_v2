# Decision Log

## 2026-04-23: Removal of mcp-servers from Git
- **Decision**: Remove `mcp-servers/` directory from version control.
- **Rationale**: The directory contains thousands of node modules and dependencies that bloat the repository, leading to extremely slow git operations and deployment times.
- **Alternative**: MCP servers should be managed as global tools or external dependencies.
- **Status**: Implemented.
