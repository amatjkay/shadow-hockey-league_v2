import { BaseHandler } from "../../../core/handlers/base.handler.js";
import { BaseToolResponse } from "../../../core/interfaces/tool-handler.interface.js";
import { CommentCreateInput, CommentUpdateInput, CommentDeleteInput, CommentResolveInput, CommentUnresolveInput, CustomerNeedCreateFromAttachmentInput } from "../types/comment.types.js";
export declare class CommentHandler extends BaseHandler {
    handleCommentCreate(args: CommentCreateInput): Promise<BaseToolResponse>;
    handleCommentUpdate(args: {
        id: string;
        input: CommentUpdateInput;
    }): Promise<BaseToolResponse>;
    handleCommentDelete(args: CommentDeleteInput): Promise<BaseToolResponse>;
    handleCommentResolve(args: CommentResolveInput): Promise<BaseToolResponse>;
    handleCommentUnresolve(args: CommentUnresolveInput): Promise<BaseToolResponse>;
    handleCustomerNeedCreateFromAttachment(args: CustomerNeedCreateFromAttachmentInput): Promise<BaseToolResponse>;
}
