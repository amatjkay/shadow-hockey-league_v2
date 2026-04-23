import { BaseHandler } from "../../../core/handlers/base.handler.js";
import { BaseToolResponse } from "../../../core/interfaces/tool-handler.interface.js";
import { LinearAuth } from "../../../auth.js";
import { LinearGraphQLClient } from "../../../graphql/client.js";
import { IssueHandlerMethods, CreateIssueInput, CreateIssuesInput, BulkUpdateIssuesInput, SearchIssuesInput, SearchIssuesByIdentifierInput, DeleteIssueInput, GetIssueInput, EditIssueInput } from "../types/issue.types.js";
/**
 * Handler for issue-related operations.
 * Manages creating, updating, searching, and deleting issues.
 */
export declare class IssueHandler extends BaseHandler implements IssueHandlerMethods {
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Creates a single issue.
     */
    handleCreateIssue(args: CreateIssueInput): Promise<BaseToolResponse>;
    /**
     * Creates multiple issues in bulk.
     */
    handleCreateIssues(args: CreateIssuesInput): Promise<BaseToolResponse>;
    /**
     * Updates multiple issues in bulk.
     */
    handleBulkUpdateIssues(args: BulkUpdateIssuesInput): Promise<BaseToolResponse>;
    /**
     * Searches for issues with filtering and pagination.
     */
    handleSearchIssues(args: SearchIssuesInput): Promise<BaseToolResponse>;
    /**
     * Search for issues by their identifiers (e.g., ["MIC-78", "MIC-79"])
     */
    handleSearchIssuesByIdentifier(args: SearchIssuesByIdentifierInput): Promise<BaseToolResponse>;
    /**
     * Get a single issue by identifier, including all comments
     */
    handleGetIssue(args: GetIssueInput): Promise<BaseToolResponse>;
    /**
     * Deletes a single issue.
     */
    handleDeleteIssue(args: DeleteIssueInput): Promise<BaseToolResponse>;
    /**
     * Edits a single issue.
     */
    handleEditIssue(args: EditIssueInput): Promise<BaseToolResponse>;
}
