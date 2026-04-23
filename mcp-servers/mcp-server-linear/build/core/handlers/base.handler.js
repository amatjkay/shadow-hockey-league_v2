import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
/**
 * Base handler class that implements common authentication and error handling logic.
 * All feature-specific handlers should extend this class.
 */
export class BaseHandler {
    constructor(auth, graphqlClient) {
        this.auth = auth;
        this.graphqlClient = graphqlClient;
    }
    /**
     * Verifies authentication and returns the GraphQL client.
     * Should be called at the start of each handler method.
     */
    verifyAuth() {
        if (!this.auth.isAuthenticated() || !this.graphqlClient) {
            throw new McpError(ErrorCode.InvalidRequest, 'Not authenticated. Call linear_auth first.');
        }
        if (this.auth.needsTokenRefresh()) {
            this.auth.refreshAccessToken();
        }
        return this.graphqlClient;
    }
    /**
     * Creates a successful response with the given text content.
     */
    createResponse(text) {
        return {
            content: [
                {
                    type: 'text',
                    text,
                },
            ],
        };
    }
    /**
     * Creates a JSON response with the given data.
     */
    createJsonResponse(data) {
        return this.createResponse(JSON.stringify(data, null, 2));
    }
    /**
     * Handles errors consistently across all handlers.
     */
    handleError(error, operation) {
        throw new McpError(ErrorCode.InternalError, `Failed to ${operation}: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
    /**
     * Validates that required parameters are present.
     * @param params The parameters object to validate
     * @param required Array of required parameter names
     * @throws {McpError} If any required parameters are missing
     */
    validateRequiredParams(params, required) {
        const missing = required.filter(param => !params[param]);
        if (missing.length > 0) {
            throw new McpError(ErrorCode.InvalidParams, `Missing required parameters: ${missing.join(', ')}`);
        }
    }
}
//# sourceMappingURL=base.handler.js.map