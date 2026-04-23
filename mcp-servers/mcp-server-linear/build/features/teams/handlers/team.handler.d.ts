import { BaseHandler } from '../../../core/handlers/base.handler.js';
import { BaseToolResponse } from '../../../core/interfaces/tool-handler.interface.js';
import { LinearAuth } from '../../../auth.js';
import { LinearGraphQLClient } from '../../../graphql/client.js';
/**
 * Handler for team-related operations.
 * Manages retrieving team information, states, and labels.
 */
export declare class TeamHandler extends BaseHandler {
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Gets information about all teams, including their states and labels.
     */
    handleGetTeams(args: any): Promise<BaseToolResponse>;
}
