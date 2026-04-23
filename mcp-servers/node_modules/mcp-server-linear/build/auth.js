import { LinearClient } from '@linear/sdk';
import { McpError, ErrorCode } from '@modelcontextprotocol/sdk/types.js';
export class LinearAuth {
    constructor() { }
    getAuthorizationUrl() {
        if (!this.config || this.config.type !== 'oauth') {
            throw new McpError(ErrorCode.InvalidRequest, 'OAuth config not initialized');
        }
        const params = new URLSearchParams({
            client_id: this.config.clientId,
            redirect_uri: this.config.redirectUri,
            response_type: 'code',
            scope: 'read,write,issues:create,offline_access',
            actor: 'application', // Enable OAuth Actor Authorization
            state: this.generateState(),
            access_type: 'offline',
        });
        return `${LinearAuth.OAUTH_AUTH_URL}/authorize?${params.toString()}`;
    }
    async handleCallback(code) {
        if (!this.config || this.config.type !== 'oauth') {
            throw new McpError(ErrorCode.InvalidRequest, 'OAuth config not initialized');
        }
        try {
            const params = new URLSearchParams({
                grant_type: 'authorization_code',
                client_id: this.config.clientId,
                client_secret: this.config.clientSecret,
                redirect_uri: this.config.redirectUri,
                code,
                access_type: 'offline'
            });
            const response = await fetch(`${LinearAuth.OAUTH_TOKEN_URL}/oauth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: params.toString()
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Token request failed: ${response.statusText}. Response: ${errorText}`);
            }
            const data = await response.json();
            this.tokenData = {
                accessToken: data.access_token,
                refreshToken: data.refresh_token,
                expiresAt: Date.now() + data.expires_in * 1000,
            };
            this.linearClient = new LinearClient({
                accessToken: this.tokenData.accessToken,
            });
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `OAuth token exchange failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    async refreshAccessToken() {
        if (!this.config || this.config.type !== 'oauth' || !this.tokenData?.refreshToken) {
            throw new McpError(ErrorCode.InvalidRequest, 'OAuth not initialized or no refresh token available');
        }
        try {
            const params = new URLSearchParams({
                grant_type: 'refresh_token',
                client_id: this.config.clientId,
                client_secret: this.config.clientSecret,
                refresh_token: this.tokenData.refreshToken
            });
            const response = await fetch(`${LinearAuth.OAUTH_TOKEN_URL}/oauth/token`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                },
                body: params.toString()
            });
            if (!response.ok) {
                const errorText = await response.text();
                throw new Error(`Token refresh failed: ${response.statusText}. Response: ${errorText}`);
            }
            const data = await response.json();
            this.tokenData = {
                accessToken: data.access_token,
                refreshToken: data.refresh_token,
                expiresAt: Date.now() + data.expires_in * 1000,
            };
            this.linearClient = new LinearClient({
                accessToken: this.tokenData.accessToken,
            });
        }
        catch (error) {
            throw new McpError(ErrorCode.InternalError, `Token refresh failed: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }
    initialize(config) {
        if (config.type === 'pat') {
            // Personal Access Token flow
            this.tokenData = {
                accessToken: config.accessToken,
                refreshToken: '', // Not needed for PAT
                expiresAt: Number.MAX_SAFE_INTEGER, // PATs don't expire
            };
            if (config.accessToken.includes("_api_")) {
                this.linearClient = new LinearClient({
                    apiKey: config.accessToken,
                });
                return;
            }
            this.linearClient = new LinearClient({
                accessToken: config.accessToken,
            });
        }
        else {
            // OAuth flow
            if (!config.clientId || !config.clientSecret || !config.redirectUri) {
                throw new McpError(ErrorCode.InvalidParams, 'Missing required OAuth parameters: clientId, clientSecret, redirectUri');
            }
            this.config = config;
        }
    }
    getClient() {
        if (!this.linearClient) {
            throw new McpError(ErrorCode.InvalidRequest, 'Linear client not initialized');
        }
        return this.linearClient;
    }
    isAuthenticated() {
        return !!this.linearClient && !!this.tokenData;
    }
    needsTokenRefresh() {
        if (!this.tokenData || !this.config || this.config.type === 'pat')
            return false;
        return Date.now() >= this.tokenData.expiresAt - 300000; // Refresh 5 minutes before expiry
    }
    // For testing purposes
    setTokenData(tokenData) {
        this.tokenData = tokenData;
        this.linearClient = new LinearClient({
            accessToken: tokenData.accessToken,
        });
    }
    generateState() {
        return Math.random().toString(36).substring(2, 15);
    }
}
LinearAuth.OAUTH_AUTH_URL = 'https://linear.app/oauth';
LinearAuth.OAUTH_TOKEN_URL = 'https://api.linear.app';
//# sourceMappingURL=auth.js.map