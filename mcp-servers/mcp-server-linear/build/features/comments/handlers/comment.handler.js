import { BaseHandler } from "../../../core/handlers/base.handler.js";
import { CREATE_COMMENT, UPDATE_COMMENT, DELETE_COMMENT, RESOLVE_COMMENT, UNRESOLVE_COMMENT, CREATE_CUSTOMER_NEED_FROM_ATTACHMENT, } from "../../../graphql/mutations/comment.mutations.js";
export class CommentHandler extends BaseHandler {
    async handleCommentCreate(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["body", "issueId"]);
            const response = await client.execute(CREATE_COMMENT, {
                input: {
                    body: args.body,
                    issueId: args.issueId,
                },
            });
            return this.createJsonResponse(response.commentCreate);
        }
        catch (error) {
            return this.handleError(error, "create comment");
        }
    }
    async handleCommentUpdate(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["id", "input"]);
            this.validateRequiredParams(args.input, ["body"]);
            const response = await client.execute(UPDATE_COMMENT, {
                id: args.id,
                input: args.input,
            });
            return this.createJsonResponse(response.commentUpdate);
        }
        catch (error) {
            return this.handleError(error, "update comment");
        }
    }
    async handleCommentDelete(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["id"]);
            const response = await client.execute(DELETE_COMMENT, {
                id: args.id,
            });
            return this.createJsonResponse(response.commentDelete);
        }
        catch (error) {
            return this.handleError(error, "delete comment");
        }
    }
    async handleCommentResolve(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["id"]);
            const response = await client.execute(RESOLVE_COMMENT, {
                id: args.id,
                resolvingCommentId: args.resolvingCommentId,
            });
            return this.createJsonResponse(response.commentResolve);
        }
        catch (error) {
            return this.handleError(error, "resolve comment");
        }
    }
    async handleCommentUnresolve(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["id"]);
            const response = await client.execute(UNRESOLVE_COMMENT, {
                id: args.id,
            });
            return this.createJsonResponse(response.commentUnresolve);
        }
        catch (error) {
            return this.handleError(error, "unresolve comment");
        }
    }
    async handleCustomerNeedCreateFromAttachment(args) {
        try {
            const client = this.verifyAuth();
            this.validateRequiredParams(args, ["attachmentId"]);
            const response = await client.execute(CREATE_CUSTOMER_NEED_FROM_ATTACHMENT, {
                input: args,
            });
            return this.createJsonResponse(response.customerNeedCreateFromAttachment);
        }
        catch (error) {
            return this.handleError(error, "create customer need from attachment");
        }
    }
}
//# sourceMappingURL=comment.handler.js.map