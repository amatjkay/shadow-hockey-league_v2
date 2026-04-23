import { LinearClient } from "@linear/sdk";
import { DocumentNode } from "graphql";
import { CreateIssueInput, CreateIssueResponse, UpdateIssueInput, UpdateIssueResponse, SearchIssuesInput, SearchIssuesResponse, DeleteIssueResponse, IssueBatchResponse } from "../features/issues/types/issue.types.js";
import { ProjectInput, ProjectResponse, SearchProjectsResponse, ProjectFilter, GetProjectMilestonesResponse, ProjectMilestone } from "../features/projects/types/project.types.js";
import { TeamResponse, LabelInput, LabelResponse } from "../features/teams/types/team.types.js";
import { UserResponse } from "../features/users/types/user.types.js";
export declare class LinearGraphQLClient {
    private linearClient;
    constructor(linearClient: LinearClient);
    execute<T, V extends Record<string, unknown> = Record<string, unknown>>(document: DocumentNode, variables?: V): Promise<T>;
    createIssue(input: CreateIssueInput): Promise<CreateIssueResponse>;
    createIssues(issues: CreateIssueInput[]): Promise<IssueBatchResponse>;
    createProject(input: ProjectInput): Promise<ProjectResponse>;
    createProjectWithIssues(projectInput: ProjectInput, issues: CreateIssueInput[]): Promise<ProjectResponse>;
    updateIssue(id: string, input: UpdateIssueInput): Promise<UpdateIssueResponse>;
    updateIssues(ids: string[], input: UpdateIssueInput): Promise<UpdateIssueResponse>;
    createIssueLabels(labels: LabelInput[]): Promise<LabelResponse>;
    searchIssues(filter: SearchIssuesInput["filter"], first?: number, after?: string, orderBy?: string): Promise<SearchIssuesResponse>;
    getTeams(): Promise<TeamResponse>;
    getCurrentUser(): Promise<UserResponse>;
    getProject(id: string): Promise<ProjectResponse>;
    searchProjects(filter?: ProjectFilter): Promise<SearchProjectsResponse>;
    deleteIssue(id: string): Promise<DeleteIssueResponse>;
    getProjectMilestones(projectId: string, filter?: Record<string, any>, first?: number, after?: string, last?: number, before?: string, includeArchived?: boolean, orderBy?: string): Promise<GetProjectMilestonesResponse>;
    createProjectMilestone(input: {
        projectId: string;
        name: string;
        description?: string;
        targetDate?: string;
        sortOrder?: number;
    }): Promise<{
        projectMilestoneCreate: {
            success: boolean;
            milestone: ProjectMilestone;
        };
    }>;
    updateProjectMilestone(id: string, input: {
        name?: string;
        description?: string;
        targetDate?: string;
        sortOrder?: number;
    }): Promise<{
        projectMilestoneUpdate: {
            success: boolean;
            milestone: ProjectMilestone;
        };
    }>;
    deleteProjectMilestone(id: string): Promise<{
        projectMilestoneDelete: {
            success: boolean;
        };
    }>;
}
