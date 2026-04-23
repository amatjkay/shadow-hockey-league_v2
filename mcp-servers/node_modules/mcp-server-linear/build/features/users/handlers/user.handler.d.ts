import { BaseHandler } from '../../../core/handlers/base.handler.js';
import { BaseToolResponse } from '../../../core/interfaces/tool-handler.interface.js';
import { LinearAuth } from '../../../auth.js';
import { LinearGraphQLClient } from '../../../graphql/client.js';
/**
 * Handler for user-related operations.
 * Manages retrieving user information and settings.
 */
export declare class UserHandler extends BaseHandler {
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Gets information about the currently authenticated user.
     */
    handleGetUser(args: any): Promise<BaseToolResponse>;
}
