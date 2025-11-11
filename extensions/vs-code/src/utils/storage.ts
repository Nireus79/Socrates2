/**
 * Storage Service for Socrates2 VS Code Extension
 *
 * Handles secure storage of credentials and preferences
 */

import * as vscode from 'vscode';

const STORAGE_KEYS = {
  TOKEN: 'socrates_access_token',
  USER: 'socrates_user',
  API_URL: 'socrates_api_url',
  SELECTED_PROJECT: 'socrates_selected_project',
};

export class StorageService {
  private context: vscode.ExtensionContext;
  private secretStorage: vscode.SecretStorage;

  constructor(context: vscode.ExtensionContext) {
    this.context = context;
    this.secretStorage = context.secrets;
  }

  /**
   * Get stored access token (secure storage)
   */
  getToken(): string | null {
    const token = this.context.globalState.get<string>(
      STORAGE_KEYS.TOKEN
    );
    return token || null;
  }

  /**
   * Set access token (secure storage)
   */
  async setToken(token: string): Promise<void> {
    await this.context.globalState.update(STORAGE_KEYS.TOKEN, token);
  }

  /**
   * Clear access token
   */
  async clearToken(): Promise<void> {
    await this.context.globalState.update(STORAGE_KEYS.TOKEN, undefined);
  }

  /**
   * Get stored user information
   */
  getUser(): any {
    const userJson = this.context.globalState.get<string>(
      STORAGE_KEYS.USER
    );
    if (!userJson) {
      return null;
    }
    try {
      return JSON.parse(userJson);
    } catch {
      return null;
    }
  }

  /**
   * Set user information
   */
  async setUser(user: any): Promise<void> {
    await this.context.globalState.update(
      STORAGE_KEYS.USER,
      JSON.stringify(user)
    );
  }

  /**
   * Clear user information
   */
  async clearUser(): Promise<void> {
    await this.context.globalState.update(STORAGE_KEYS.USER, undefined);
  }

  /**
   * Get stored API URL
   */
  getApiUrl(): string {
    return (
      this.context.globalState.get<string>(STORAGE_KEYS.API_URL) ||
      'http://localhost:8000'
    );
  }

  /**
   * Set API URL
   */
  async setApiUrl(url: string): Promise<void> {
    await this.context.globalState.update(STORAGE_KEYS.API_URL, url);
  }

  /**
   * Get selected project ID
   */
  getSelectedProject(): string | null {
    return (
      this.context.globalState.get<string>(
        STORAGE_KEYS.SELECTED_PROJECT
      ) || null
    );
  }

  /**
   * Set selected project ID
   */
  async setSelectedProject(projectId: string): Promise<void> {
    await this.context.globalState.update(
      STORAGE_KEYS.SELECTED_PROJECT,
      projectId
    );
  }

  /**
   * Clear selected project
   */
  async clearSelectedProject(): Promise<void> {
    await this.context.globalState.update(
      STORAGE_KEYS.SELECTED_PROJECT,
      undefined
    );
  }

  /**
   * Store value in workspace state (volatile, cleared on restart)
   */
  setWorkspaceValue(key: string, value: any): void {
    this.context.workspaceState.update(key, value);
  }

  /**
   * Get value from workspace state
   */
  getWorkspaceValue(key: string): any {
    return this.context.workspaceState.get(key);
  }

  /**
   * Clear all stored data
   */
  async clearAll(): Promise<void> {
    for (const key of Object.values(STORAGE_KEYS)) {
      await this.context.globalState.update(key, undefined);
    }
  }
}
