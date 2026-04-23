import { LinearClient } from '@linear/sdk';
/**
 * Solution Attempts:
 *
 * 1. OAuth Flow with Browser (Initial Attempt)
 * - Used browser redirect and local server for OAuth flow
 * - Issues: Browser extensions interfering, CORS issues
 * - Status: Failed - Browser extensions and CORS blocking requests
 *
 * 2. Personal Access Token (Current Attempt)
 * - Using PAT for initial integration tests
 * - Simpler approach without browser interaction
 * - Status: Working - Successfully authenticates and makes API calls
 *
 * 3. Direct OAuth Token Exchange (Current Attempt)
 * - Using form-urlencoded content type as required by Linear
 * - Status: In Progress - Testing token exchange
 */
export interface OAuthConfig {
    type: 'oauth';
    clientId: string;
    clientSecret: string;
    redirectUri: string;
}
export interface PersonalAccessTokenConfig {
    type: 'pat';
    accessToken: string;
}
export type AuthConfig = OAuthConfig | PersonalAccessTokenConfig;
export interface TokenData {
    accessToken: string;
    refreshToken: string;
    expiresAt: number;
}
export declare class LinearAuth {
    private static readonly OAUTH_AUTH_URL;
    private static readonly OAUTH_TOKEN_URL;
    private config?;
    private tokenData?;
    private linearClient?;
    constructor();
    getAuthorizationUrl(): string;
    handleCallback(code: string): Promise<void>;
    refreshAccessToken(): Promise<void>;
    initialize(config: AuthConfig): void;
    getClient(): LinearClient;
    isAuthenticated(): boolean;
    needsTokenRefresh(): boolean;
    setTokenData(tokenData: TokenData): void;
    private generateState;
}
