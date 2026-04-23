import { BaseHandler } from '../../../core/handlers/base.handler.js';
/**
 * Handler for user-related operations.
 * Manages retrieving user information and settings.
 */
export class UserHandler extends BaseHandler {
    constructor(auth, graphqlClient) {
        super(auth, graphqlClient);
    }
    /**
     * Gets information about the currently authenticated user.
     */
    async handleGetUser(args) {
        try {
            const client = this.verifyAuth();
            const result = await client.getCurrentUser();
            return this.createJsonResponse(result);
        }
        catch (error) {
            this.handleError(error, 'get user info');
        }
    }
}
//# sourceMappingURL=user.handler.js.map