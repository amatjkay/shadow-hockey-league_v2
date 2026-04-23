/**
 * This file contains the schema definitions for all MCP tools exposed by the Linear server.
 * These schemas define the input parameters and validation rules for each tool.
 */
export declare const toolSchemas: {
    [x: string]: {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                code: {
                    type: string;
                    description: string;
                };
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                title: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                description: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                teamId: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                parentId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                labelIds: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                    optional: boolean;
                };
                assigneeId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                priority: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                createAsUser: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                displayIconUrl: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                project: {
                    type: string;
                    properties: {
                        name: {
                            type: string;
                            description: string;
                        };
                        description: {
                            type: string;
                            description: string;
                        };
                        teamIds: {
                            type: string;
                            items: {
                                type: string;
                            };
                            description: string;
                            minItems: number;
                        };
                    };
                    required: string[];
                };
                issues: {
                    type: string;
                    items: {
                        type: string;
                        properties: {
                            title: {
                                type: string;
                                description: string;
                            };
                            description: {
                                type: string;
                                description: string;
                            };
                            teamId: {
                                type: string;
                                description: string;
                            };
                            parentId?: undefined;
                            labelIds?: undefined;
                            assigneeId?: undefined;
                            priority?: undefined;
                            projectId?: undefined;
                            createAsUser?: undefined;
                            displayIconUrl?: undefined;
                        };
                        required: string[];
                    };
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples: {
            description: string;
            value: {
                project: {
                    name: string;
                    description: string;
                    teamIds: string[];
                };
                issues: {
                    title: string;
                    description: string;
                    teamId: string;
                }[];
            };
        }[];
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                issueIds: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                };
                update: {
                    type: string;
                    properties: {
                        stateId: {
                            type: string;
                            description: string;
                            optional: boolean;
                        };
                        assigneeId: {
                            type: string;
                            description: string;
                            optional: boolean;
                        };
                        priority: {
                            type: string;
                            description: string;
                            optional: boolean;
                        };
                    };
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                issueId: {
                    type: string;
                    description: string;
                };
                title: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                description: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                stateId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                priority: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                assigneeId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                labelIds: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                    optional: boolean;
                };
                projectId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                projectMilestoneId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                estimate: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                dueDate: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                parentId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                sortOrder: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                teamId?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                query: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                teamIds: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                    optional: boolean;
                };
                assigneeIds: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                    optional: boolean;
                };
                states: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                    optional: boolean;
                };
                priority: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                first: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                after: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                orderBy: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required?: undefined;
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                identifiers: {
                    type: string;
                    items: {
                        type: string;
                    };
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                identifier: {
                    type: string;
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required?: undefined;
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                id: {
                    type: string;
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                filter: {
                    type: string;
                    properties: {
                        status: {
                            type: string;
                            properties: {
                                eq: {
                                    type: string;
                                    description: string;
                                };
                                in: {
                                    type: string;
                                    items: {
                                        type: string;
                                    };
                                    description: string;
                                };
                                neq: {
                                    type: string;
                                    description: string;
                                };
                                nin: {
                                    type: string;
                                    items: {
                                        type: string;
                                    };
                                    description: string;
                                };
                            };
                            description: string;
                        };
                        projectMilestones: {
                            type: string;
                            description: string;
                        };
                        projectUpdates: {
                            type: string;
                            description: string;
                        };
                        nextProjectMilestone: {
                            type: string;
                            description: string;
                        };
                        completedProjectMilestones: {
                            type: string;
                            description: string;
                        };
                        name?: undefined;
                        targetDate?: undefined;
                        completed?: undefined;
                    };
                    description: string;
                    optional?: undefined;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required?: undefined;
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                issues: {
                    type: string;
                    items: {
                        type: string;
                        properties: {
                            title: {
                                type: string;
                                description: string;
                            };
                            description: {
                                type: string;
                                description: string;
                            };
                            teamId: {
                                type: string;
                                description: string;
                            };
                            parentId: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                            labelIds: {
                                type: string;
                                items: {
                                    type: string;
                                };
                                description: string;
                                optional: boolean;
                            };
                            assigneeId: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                            priority: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                            projectId: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                            createAsUser: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                            displayIconUrl: {
                                type: string;
                                description: string;
                                optional: boolean;
                            };
                        };
                        required: string[];
                    };
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                body: {
                    type: string;
                    description: string;
                };
                issueId: {
                    type: string;
                    description: string;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                id: {
                    type: string;
                    description: string;
                };
                input: {
                    type: string;
                    properties: {
                        body: {
                            type: string;
                            description: string;
                        };
                    };
                    required: string[];
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                filter?: undefined;
                body?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                id: {
                    type: string;
                    description: string;
                };
                resolvingCommentId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                attachmentId: {
                    type: string;
                    description: string;
                };
                title: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                description: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                teamId: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                projectId: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                filter: {
                    type: string;
                    properties: {
                        name: {
                            type: string;
                            properties: {
                                eq: {
                                    type: string;
                                    description: string;
                                };
                                contains: {
                                    type: string;
                                    description: string;
                                };
                            };
                            description: string;
                        };
                        targetDate: {
                            type: string;
                            properties: {
                                lt: {
                                    type: string;
                                    description: string;
                                };
                                gt: {
                                    type: string;
                                    description: string;
                                };
                            };
                            description: string;
                        };
                        completed: {
                            type: string;
                            description: string;
                        };
                        status?: undefined;
                        projectMilestones?: undefined;
                        projectUpdates?: undefined;
                        nextProjectMilestone?: undefined;
                        completedProjectMilestones?: undefined;
                    };
                    description: string;
                    optional: boolean;
                };
                first: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                after: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                last: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                before: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                includeArchived: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                orderBy: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                title?: undefined;
                description?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                sortOrder?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                name?: undefined;
                targetDate?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                projectId: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                name: {
                    type: string;
                    description: string;
                    optional?: undefined;
                };
                description: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                targetDate: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                sortOrder: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                title?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                id?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    } | {
        name: string;
        description: string;
        inputSchema: {
            type: string;
            properties: {
                id: {
                    type: string;
                    description: string;
                };
                name: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                description: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                targetDate: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                sortOrder: {
                    type: string;
                    description: string;
                    optional: boolean;
                };
                code?: undefined;
                title?: undefined;
                teamId?: undefined;
                parentId?: undefined;
                labelIds?: undefined;
                assigneeId?: undefined;
                priority?: undefined;
                createAsUser?: undefined;
                displayIconUrl?: undefined;
                project?: undefined;
                issues?: undefined;
                issueIds?: undefined;
                update?: undefined;
                issueId?: undefined;
                stateId?: undefined;
                projectId?: undefined;
                projectMilestoneId?: undefined;
                estimate?: undefined;
                dueDate?: undefined;
                query?: undefined;
                teamIds?: undefined;
                assigneeIds?: undefined;
                states?: undefined;
                first?: undefined;
                after?: undefined;
                orderBy?: undefined;
                identifiers?: undefined;
                identifier?: undefined;
                filter?: undefined;
                body?: undefined;
                input?: undefined;
                resolvingCommentId?: undefined;
                attachmentId?: undefined;
                last?: undefined;
                before?: undefined;
                includeArchived?: undefined;
            };
            required: string[];
        };
        examples?: undefined;
    };
};
