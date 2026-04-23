import { BaseHandler } from '../../../core/handlers/base.handler.js';
import { BaseToolResponse } from '../../../core/interfaces/tool-handler.interface.js';
import { LinearAuth } from '../../../auth.js';
import { LinearGraphQLClient } from '../../../graphql/client.js';
/**
 * Handler for authentication-related operations.
 * Manages both OAuth and Personal Access Token (PAT) authentication flows.
 */
export declare class AuthHandler extends BaseHandler {
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Initializes OAuth flow with Linear.
     */
    handleAuth(args: any): Promise<BaseToolResponse>;
    /**
     * Handles OAuth callback after user authorization.
     */
    handleAuthCallback(args: any): Promise<BaseToolResponse>;
}
