/**
 * Authentication Service for Socrates2 VS Code Extension
 *
 * Handles user login, logout, and token management
 */

import * as vscode from 'vscode';
import { SocratesApiClient } from './client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export interface LoginResponse {
  access_token: string;
  token_type: string;
  user: any;
}

export class AuthenticationService {
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;

  constructor(apiClient: SocratesApiClient, storage: StorageService) {
    this.apiClient = apiClient;
    this.storage = storage;
    this.logger = new Logger('AuthenticationService');
  }

  /**
   * Check if user is authenticated
   */
  async isAuthenticated(): Promise<boolean> {
    try {
      // Check if token exists
      const token = this.storage.getToken();
      if (!token) {
        return false;
      }

      // Verify token by making API call
      const user = await this.apiClient.getCurrentUser();
      return !!user;
    } catch (error) {
      this.logger.debug(`Not authenticated: ${error}`);
      return false;
    }
  }

  /**
   * Authenticate user with email and password
   */
  async authenticate(): Promise<boolean> {
    try {
      // Prompt for email
      const email = await vscode.window.showInputBox({
        prompt: 'Email address',
        placeHolder: 'user@example.com',
        ignoreFocusOut: true,
      });

      if (!email) {
        return false;
      }

      // Prompt for password
      const password = await vscode.window.showInputBox({
        prompt: 'Password',
        password: true,
        ignoreFocusOut: true,
      });

      if (!password) {
        return false;
      }

      // Show progress
      return vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: 'Signing in to Socrates2...',
          cancellable: false,
        },
        async () => {
          const success = await this.performLogin(email, password);
          return success;
        }
      );
    } catch (error) {
      this.logger.error(`Authentication error: ${error}`);
      return false;
    }
  }

  /**
   * Perform login with email and password
   */
  private async performLogin(email: string, password: string): Promise<boolean> {
    try {
      // TODO: Call login API endpoint
      // For now, use a mock implementation
      const response = await this.loginMock(email, password);

      if (response && response.access_token) {
        // Store token
        this.storage.setToken(response.access_token);

        // Store user info
        if (response.user) {
          this.storage.setUser(response.user);
        }

        this.logger.info(`Logged in as ${email}`);
        return true;
      }

      return false;
    } catch (error) {
      this.logger.error(`Login failed: ${error}`);
      return false;
    }
  }

  /**
   * Mock login for development
   * In production, this would call the actual API endpoint
   */
  private async loginMock(email: string, password: string): Promise<LoginResponse> {
    // Simulate API call delay
    await new Promise((resolve) => setTimeout(resolve, 1000));

    // For demo, accept any email/password
    // In production, this would be an actual API call
    return {
      access_token: `token_${Date.now()}`,
      token_type: 'bearer',
      user: {
        id: `user_${Date.now()}`,
        email,
        name: email.split('@')[0],
      },
    };
  }

  /**
   * Logout user
   */
  async logout(): Promise<boolean> {
    try {
      // TODO: Call logout API endpoint if needed

      // Clear stored credentials
      this.storage.clearToken();
      this.storage.clearUser();

      this.logger.info('Logged out');
      return true;
    } catch (error) {
      this.logger.error(`Logout error: ${error}`);
      return false;
    }
  }

  /**
   * Get stored user information
   */
  getStoredUser(): any {
    return this.storage.getUser();
  }

  /**
   * Get stored token
   */
  getToken(): string | null {
    return this.storage.getToken();
  }

  /**
   * Refresh access token
   */
  async refreshToken(): Promise<boolean> {
    try {
      // TODO: Call refresh token endpoint
      this.logger.info('Token refreshed');
      return true;
    } catch (error) {
      this.logger.error(`Token refresh failed: ${error}`);
      return false;
    }
  }
}
