import { BaseHandler } from "../../../core/handlers/base.handler.js";
import { BaseToolResponse } from "../../../core/interfaces/tool-handler.interface.js";
import { LinearAuth } from "../../../auth.js";
import { LinearGraphQLClient } from "../../../graphql/client.js";
/**
 * Handler for project-related operations.
 * Manages creating, searching, and retrieving project information.
 */
export declare class ProjectHandler extends BaseHandler {
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Creates a new project with associated issues.
     */
    /**
     * Creates a new project with associated issues
     * @example
     * ```typescript
     * const result = await handler.handleCreateProjectWithIssues({
     *   project: {
     *     name: "Q1 Planning",
     *     description: "Q1 2025 Planning Project",
     *     teamIds: ["team-id-1"], // Required: Array of team IDs
     *   },
     *   issues: [{
     *     title: "Project Setup",
     *     description: "Initial project setup tasks",
     *     teamId: "team-id-1"
     *   }]
     * });
     * ```
     */
    handleCreateProjectWithIssues(args: any): Promise<BaseToolResponse>;
    /**
     * Gets information about a specific project.
     */
    handleGetProject(args: any): Promise<BaseToolResponse>;
    /**
     * Lists all projects or searches with optional filters.
     */
    handleListProjects(args?: any): Promise<BaseToolResponse>;
    /**
     * Get project milestones with filtering and pagination
     */
    handleGetProjectMilestones(args: any): Promise<BaseToolResponse>;
    /**
     * Create a new project milestone
     */
    handleCreateProjectMilestone(args: any): Promise<BaseToolResponse>;
    /**
     * Update a project milestone
     */
    handleUpdateProjectMilestone(args: any): Promise<BaseToolResponse>;
    /**
     * Delete a project milestone
     */
    handleDeleteProjectMilestone(args: any): Promise<BaseToolResponse>;
}
