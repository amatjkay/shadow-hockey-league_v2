export class LinearGraphQLClient {
    constructor(linearClient) {
        this.linearClient = linearClient;
    }
    async execute(document, variables) {
        const graphQLClient = this.linearClient.client;
        try {
            const response = await graphQLClient.rawRequest(document.loc?.source.body || "", variables);
            return response.data;
        }
        catch (error) {
            if (error instanceof Error) {
                throw new Error(`GraphQL operation failed: ${error.message}`);
            }
            throw error;
        }
    }
    // Create single issue
    async createIssue(input) {
        const { CREATE_ISSUE_MUTATION } = await import("./mutations.js");
        return this.execute(CREATE_ISSUE_MUTATION, { input });
    }
    // Create multiple issues
    async createIssues(issues) {
        const { CREATE_BATCH_ISSUES } = await import("./mutations.js");
        return this.execute(CREATE_BATCH_ISSUES, {
            input: { issues },
        });
    }
    // Create a project
    async createProject(input) {
        const { CREATE_PROJECT } = await import("./mutations.js");
        return this.execute(CREATE_PROJECT, { input });
    }
    // Helper method to create a project with associated issues
    async createProjectWithIssues(projectInput, issues) {
        // Create project first
        const projectResult = await this.createProject(projectInput);
        if (!projectResult.projectCreate.success) {
            throw new Error("Failed to create project");
        }
        // Then create issues with project ID
        const issuesWithProject = issues.map((issue) => ({
            ...issue,
            projectId: projectResult.projectCreate.project.id,
        }));
        const issuesResult = await this.createIssues(issuesWithProject);
        if (!issuesResult.issueBatchCreate.success) {
            throw new Error("Failed to create issues");
        }
        return {
            projectCreate: projectResult.projectCreate,
            issueBatchCreate: issuesResult.issueBatchCreate,
        };
    }
    // Update a single issue
    async updateIssue(id, input) {
        const { UPDATE_ISSUE_MUTATION } = await import("./mutations.js");
        return this.execute(UPDATE_ISSUE_MUTATION, {
            id,
            input,
        });
    }
    // Bulk update issues
    async updateIssues(ids, input) {
        // Handle bulk updates one at a time since the API only supports single updates
        const updates = await Promise.all(ids.map((id) => this.updateIssue(id, input)));
        return updates[0]; // Return the first response as they should all be similar
    }
    // Create multiple labels
    async createIssueLabels(labels) {
        const { CREATE_ISSUE_LABELS } = await import("./mutations.js");
        return this.execute(CREATE_ISSUE_LABELS, { labels });
    }
    // Search issues with pagination
    async searchIssues(filter, first = 50, after, orderBy = "updatedAt") {
        // Use GET_ISSUES_BY_IDENTIFIER for identifier searches
        if (filter?.identifier?.in) {
            const { GET_ISSUES_BY_IDENTIFIER } = await import("./queries.js");
            // Extract numbers from identifiers (e.g., "78" from "MIC-78") and convert to Float
            const numbers = filter.identifier.in.map((id) => parseFloat(id.split("-")[1]));
            return this.execute(GET_ISSUES_BY_IDENTIFIER, {
                numbers,
            });
        }
        // Use regular search query for other filters
        const { SEARCH_ISSUES_QUERY } = await import("./queries.js");
        return this.execute(SEARCH_ISSUES_QUERY, {
            filter,
            first,
            after,
            orderBy,
        });
    }
    // Get teams with their states and labels
    async getTeams() {
        const { GET_TEAMS_QUERY } = await import("./queries.js");
        return this.execute(GET_TEAMS_QUERY);
    }
    // Get current user info
    async getCurrentUser() {
        const { GET_USER_QUERY } = await import("./queries.js");
        return this.execute(GET_USER_QUERY);
    }
    // Get project info
    async getProject(id) {
        const { GET_PROJECT_QUERY } = await import("./queries.js");
        return this.execute(GET_PROJECT_QUERY, { id });
    }
    // Search projects
    async searchProjects(filter) {
        const { SEARCH_PROJECTS_QUERY } = await import("./queries.js");
        return this.execute(SEARCH_PROJECTS_QUERY, {
            filter,
        });
    }
    // Delete a single issue
    async deleteIssue(id) {
        const { DELETE_ISSUE_MUTATION } = await import("./mutations.js");
        return this.execute(DELETE_ISSUE_MUTATION, {
            id,
        });
    }
    // Get project milestones
    async getProjectMilestones(projectId, filter, first, after, last, before, includeArchived, orderBy) {
        const { GET_PROJECT_MILESTONES } = await import("./queries.js");
        return this.execute(GET_PROJECT_MILESTONES, {
            projectId,
            filter,
            first,
            after,
            last,
            before,
            includeArchived,
            orderBy,
        });
    }
    // Create a project milestone
    async createProjectMilestone(input) {
        const { CREATE_PROJECT_MILESTONE } = await import("./mutations.js");
        return this.execute(CREATE_PROJECT_MILESTONE, { input });
    }
    // Update a project milestone
    async updateProjectMilestone(id, input) {
        const { UPDATE_PROJECT_MILESTONE } = await import("./mutations.js");
        return this.execute(UPDATE_PROJECT_MILESTONE, { id, input });
    }
    // Delete a project milestone
    async deleteProjectMilestone(id) {
        const { DELETE_PROJECT_MILESTONE } = await import("./mutations.js");
        return this.execute(DELETE_PROJECT_MILESTONE, { id });
    }
}
//# sourceMappingURL=client.js.map