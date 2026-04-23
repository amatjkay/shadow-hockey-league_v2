import { LinearAuth } from '../../auth.js';
import { LinearGraphQLClient } from '../../graphql/client.js';
import { BaseToolResponse } from '../interfaces/tool-handler.interface.js';
/**
 * Base handler class that implements common authentication and error handling logic.
 * All feature-specific handlers should extend this class.
 */
export declare abstract class BaseHandler {
    protected readonly auth: LinearAuth;
    protected readonly graphqlClient: LinearGraphQLClient | undefined;
    constructor(auth: LinearAuth, graphqlClient: LinearGraphQLClient | undefined);
    /**
     * Verifies authentication and returns the GraphQL client.
     * Should be called at the start of each handler method.
     */
    protected verifyAuth(): LinearGraphQLClient;
    /**
     * Creates a successful response with the given text content.
     */
    protected createResponse(text: string): BaseToolResponse;
    /**
     * Creates a JSON response with the given data.
     */
    protected createJsonResponse(data: unknown): BaseToolResponse;
    /**
     * Handles errors consistently across all handlers.
     */
    protected handleError(error: unknown, operation: string): never;
    /**
     * Validates that required parameters are present.
     * @param params The parameters object to validate
     * @param required Array of required parameter names
     * @throws {McpError} If any required parameters are missing
     */
    protected validateRequiredParams<T>(params: T, required: Array<keyof T & string>): void;
}
