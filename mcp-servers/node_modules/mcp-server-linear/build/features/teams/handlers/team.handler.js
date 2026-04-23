import { BaseHandler } from '../../../core/handlers/base.handler.js';
/**
 * Handler for team-related operations.
 * Manages retrieving team information, states, and labels.
 */
export class TeamHandler extends BaseHandler {
    constructor(auth, graphqlClient) {
        super(auth, graphqlClient);
    }
    /**
     * Gets information about all teams, including their states and labels.
     */
    async handleGetTeams(args) {
        try {
            const client = this.verifyAuth();
            const result = await client.getTeams();
            return this.createJsonResponse(result);
        }
        catch (error) {
            this.handleError(error, 'get teams');
        }
    }
}
//# sourceMappingURL=team.handler.js.map