import { LinearAuth } from "../../auth.js";
import { LinearGraphQLClient } from "../../graphql/client.js";
import { AuthHandler } from "../../features/auth/handlers/auth.handler.js";
import { IssueHandler } from "../../features/issues/handlers/issue.handler.js";
import { ProjectHandler } from "../../features/projects/handlers/project.handler.js";
import { TeamHandler } from "../../features/teams/handlers/team.handler.js";
import { UserHandler } from "../../features/users/handlers/user.handler.js";
import { CommentHandler } from "../../features/comments/handlers/comment.handler.js";
export declare class HandlerFactory {
    private authHandler;
    private issueHandler;
    private projectHandler;
    private teamHandler;
    private userHandler;
    private commentHandler;
    constructor(auth: LinearAuth, graphqlClient?: LinearGraphQLClient);
    /**
     * Gets the appropriate handler for a given tool name.
     */
    getHandlerForTool(toolName: string): {
        handler: AuthHandler | IssueHandler | ProjectHandler | TeamHandler | UserHandler | CommentHandler;
        method: string;
    };
}
