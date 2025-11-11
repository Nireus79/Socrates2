/**
 * Configuration Panel for Socrates2 VS Code Extension
 *
 * Web-based UI for managing extension settings and configuration
 */

import * as vscode from 'vscode';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class ConfigurationPanel {
  private panel?: vscode.WebviewPanel;
  private storage: StorageService;
  private logger: Logger;

  constructor(storage: StorageService) {
    this.storage = storage;
    this.logger = new Logger('ConfigPanel');
  }

  /**
   * Show configuration panel
   */
  show(context: vscode.ExtensionContext): void {
    if (this.panel) {
      this.panel.reveal(vscode.ViewColumn.One);
      return;
    }

    // Create panel
    this.panel = vscode.window.createWebviewPanel(
      'socratesConfig',
      'Socrates2 Settings',
      vscode.ViewColumn.One,
      {
        enableScripts: true,
        retainContextWhenHidden: true,
        localResourceRoots: [vscode.Uri.joinPath(context.extensionUri, 'media')],
      }
    );

    // Set HTML content
    this.panel.webview.html = this.getWebviewContent();

    // Handle messages from webview
    this.panel.webview.onDidReceiveMessage(
      (message) => this.handleMessage(message),
      undefined,
      context.subscriptions
    );

    // Handle panel closed
    this.panel.onDidDispose(
      () => {
        this.panel = undefined;
      },
      undefined,
      context.subscriptions
    );

    this.logger.info('Configuration panel opened');
  }

  /**
   * Handle messages from webview
   */
  private async handleMessage(message: any): Promise<void> {
    const { command, data } = message;

    try {
      switch (command) {
        case 'setApiUrl':
          await this.storage.setApiUrl(data.apiUrl);
          this.sendMessage({ command: 'showNotification', text: 'API URL updated' });
          break;

        case 'getApiUrl':
          this.sendMessage({
            command: 'apiUrl',
            value: this.storage.getApiUrl(),
          });
          break;

        case 'setAutoSync':
          const config = vscode.workspace.getConfiguration('socrates');
          await config.update('autoSync', data.enabled, vscode.ConfigurationTarget.Global);
          this.sendMessage({ command: 'showNotification', text: 'Auto-sync setting updated' });
          break;

        case 'setSyncInterval':
          const cfg = vscode.workspace.getConfiguration('socrates');
          await cfg.update('syncInterval', data.interval, vscode.ConfigurationTarget.Global);
          this.sendMessage({ command: 'showNotification', text: 'Sync interval updated' });
          break;

        case 'setCodeGenLanguage':
          const config2 = vscode.workspace.getConfiguration('socrates');
          await config2.update('codeGenLanguage', data.language, vscode.ConfigurationTarget.Global);
          this.sendMessage({ command: 'showNotification', text: 'Code generation language updated' });
          break;

        case 'getConfig':
          this.sendMessage({
            command: 'config',
            value: {
              apiUrl: this.storage.getApiUrl(),
              autoSync: vscode.workspace.getConfiguration('socrates').get('autoSync', true),
              syncInterval: vscode.workspace.getConfiguration('socrates').get('syncInterval', 30000),
              codeGenLanguage: vscode.workspace.getConfiguration('socrates').get('codeGenLanguage', 'auto-detect'),
            },
          });
          break;

        case 'logout':
          await this.storage.clearToken();
          await this.storage.clearUser();
          this.sendMessage({ command: 'showNotification', text: 'Logged out successfully' });
          break;

        case 'getUser':
          const user = this.storage.getUser();
          this.sendMessage({
            command: 'user',
            value: user,
          });
          break;

        default:
          this.logger.warning(`Unknown command: ${command}`);
      }
    } catch (error) {
      this.logger.error(`Error handling message: ${error}`);
      this.sendMessage({ command: 'showError', text: `Error: ${error}` });
    }
  }

  /**
   * Send message to webview
   */
  private sendMessage(message: any): void {
    if (this.panel) {
      this.panel.webview.postMessage(message);
    }
  }

  /**
   * Get webview HTML content
   */
  private getWebviewContent(): string {
    return `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <meta name="viewport" content="width=device-width, initial-scale=1.0">
          <title>Socrates2 Settings</title>
          <style>
            * {
              box-sizing: border-box;
            }

            body {
              font-family: var(--vscode-font-family);
              font-size: var(--vscode-font-size);
              color: var(--vscode-foreground);
              background-color: var(--vscode-editor-background);
              padding: 20px;
              margin: 0;
            }

            .container {
              max-width: 600px;
              margin: 0 auto;
            }

            h1 {
              margin-top: 0;
              color: var(--vscode-foreground);
              font-size: 24px;
            }

            .section {
              margin-bottom: 30px;
              padding-bottom: 20px;
              border-bottom: 1px solid var(--vscode-editor-lineHighlightBackground);
            }

            .section:last-child {
              border-bottom: none;
            }

            .section h2 {
              font-size: 16px;
              font-weight: 600;
              margin-top: 0;
              margin-bottom: 15px;
              color: var(--vscode-foreground);
            }

            .form-group {
              margin-bottom: 15px;
            }

            label {
              display: block;
              margin-bottom: 5px;
              font-weight: 500;
              color: var(--vscode-foreground);
            }

            input[type="text"],
            input[type="number"],
            select {
              width: 100%;
              padding: 8px 12px;
              background-color: var(--vscode-input-background);
              color: var(--vscode-input-foreground);
              border: 1px solid var(--vscode-input-border);
              border-radius: 4px;
              font-family: var(--vscode-font-family);
              font-size: var(--vscode-font-size);
            }

            input[type="text"]:focus,
            input[type="number"]:focus,
            select:focus {
              outline: none;
              border-color: var(--vscode-focusBorder);
              box-shadow: 0 0 0 1px var(--vscode-focusBorder);
            }

            input[type="checkbox"] {
              margin-right: 8px;
            }

            .checkbox-group {
              display: flex;
              align-items: center;
            }

            .button-group {
              display: flex;
              gap: 10px;
              margin-top: 20px;
            }

            button {
              flex: 1;
              padding: 10px 16px;
              background-color: var(--vscode-button-background);
              color: var(--vscode-button-foreground);
              border: none;
              border-radius: 4px;
              cursor: pointer;
              font-family: var(--vscode-font-family);
              font-size: var(--vscode-font-size);
              font-weight: 500;
              transition: background-color 0.2s;
            }

            button:hover {
              background-color: var(--vscode-button-hoverBackground);
            }

            button.secondary {
              background-color: var(--vscode-button-secondaryBackground);
              color: var(--vscode-button-secondaryForeground);
            }

            button.secondary:hover {
              background-color: var(--vscode-button-secondaryHoverBackground);
            }

            .help-text {
              font-size: 12px;
              color: var(--vscode-descriptionForeground);
              margin-top: 5px;
            }

            .user-info {
              padding: 10px;
              background-color: var(--vscode-editor-lineHighlightBackground);
              border-radius: 4px;
              margin-bottom: 15px;
            }

            .status-message {
              padding: 10px 12px;
              border-radius: 4px;
              margin-bottom: 15px;
              display: none;
            }

            .status-message.success {
              background-color: var(--vscode-notificationCenterHeader-background);
              color: var(--vscode-terminal-ansiGreen);
              display: block;
            }

            .status-message.error {
              background-color: var(--vscode-notificationCenterHeader-background);
              color: var(--vscode-terminal-ansiRed);
              display: block;
            }
          </style>
        </head>
        <body>
          <div class="container">
            <h1>Socrates2 Configuration</h1>

            <div id="statusMessage" class="status-message"></div>

            <div class="section">
              <h2>Account</h2>
              <div id="userInfo" class="user-info" style="display:none;">
                <strong>Logged in as:</strong> <span id="userEmail"></span>
              </div>
              <div id="notLoggedIn" class="user-info" style="display:none;">
                Not logged in. Use the "Sign In" command to authenticate.
              </div>
              <div class="button-group">
                <button id="logoutBtn" class="secondary" style="display:none;">Logout</button>
              </div>
            </div>

            <div class="section">
              <h2>API Configuration</h2>
              <div class="form-group">
                <label for="apiUrl">API Server URL</label>
                <input type="text" id="apiUrl" placeholder="http://localhost:8000">
                <div class="help-text">The URL of your Socrates2 API server</div>
              </div>
            </div>

            <div class="section">
              <h2>Synchronization</h2>
              <div class="form-group">
                <div class="checkbox-group">
                  <input type="checkbox" id="autoSync">
                  <label for="autoSync">Enable automatic synchronization</label>
                </div>
                <div class="help-text">Automatically refresh data from the server</div>
              </div>

              <div class="form-group">
                <label for="syncInterval">Synchronization interval (ms)</label>
                <input type="number" id="syncInterval" min="5000" max="300000" step="5000">
                <div class="help-text">How often to refresh data (minimum 5 seconds)</div>
              </div>
            </div>

            <div class="section">
              <h2>Code Generation</h2>
              <div class="form-group">
                <label for="codeGenLanguage">Default code generation language</label>
                <select id="codeGenLanguage">
                  <option value="auto-detect">Auto-detect from file</option>
                  <option value="python">Python</option>
                  <option value="javascript">JavaScript</option>
                  <option value="go">Go</option>
                  <option value="java">Java</option>
                </select>
                <div class="help-text">Default language when generating code</div>
              </div>
            </div>

            <div class="section">
              <h2>Actions</h2>
              <div class="button-group">
                <button id="saveBtn">Save Settings</button>
                <button id="resetBtn" class="secondary">Reset to Defaults</button>
              </div>
            </div>
          </div>

          <script>
            const vscode = acquireVsCodeApi();

            // Request current config on load
            window.addEventListener('load', () => {
              vscode.postMessage({ command: 'getConfig' });
              vscode.postMessage({ command: 'getUser' });
            });

            // Handle messages from extension
            window.addEventListener('message', (event) => {
              const { command, value, text } = event.data;

              if (command === 'config') {
                document.getElementById('apiUrl').value = value.apiUrl;
                document.getElementById('autoSync').checked = value.autoSync;
                document.getElementById('syncInterval').value = value.syncInterval;
                document.getElementById('codeGenLanguage').value = value.codeGenLanguage;
              }

              if (command === 'user' && value) {
                document.getElementById('userInfo').style.display = 'block';
                document.getElementById('notLoggedIn').style.display = 'none';
                document.getElementById('userEmail').textContent = value.email || 'Unknown';
                document.getElementById('logoutBtn').style.display = 'block';
              } else if (command === 'user') {
                document.getElementById('userInfo').style.display = 'none';
                document.getElementById('notLoggedIn').style.display = 'block';
                document.getElementById('logoutBtn').style.display = 'none';
              }

              if (command === 'showNotification') {
                showMessage(text, 'success');
              }

              if (command === 'showError') {
                showMessage(text, 'error');
              }
            });

            // Save button
            document.getElementById('saveBtn').addEventListener('click', () => {
              const apiUrl = document.getElementById('apiUrl').value;
              const autoSync = document.getElementById('autoSync').checked;
              const syncInterval = parseInt(document.getElementById('syncInterval').value);
              const codeGenLanguage = document.getElementById('codeGenLanguage').value;

              vscode.postMessage({ command: 'setApiUrl', data: { apiUrl } });
              vscode.postMessage({ command: 'setAutoSync', data: { enabled: autoSync } });
              vscode.postMessage({ command: 'setSyncInterval', data: { interval: syncInterval } });
              vscode.postMessage({ command: 'setCodeGenLanguage', data: { language: codeGenLanguage } });
            });

            // Logout button
            document.getElementById('logoutBtn').addEventListener('click', () => {
              if (confirm('Are you sure you want to logout?')) {
                vscode.postMessage({ command: 'logout' });
              }
            });

            // Reset button
            document.getElementById('resetBtn').addEventListener('click', () => {
              if (confirm('Reset all settings to defaults?')) {
                document.getElementById('apiUrl').value = 'http://localhost:8000';
                document.getElementById('autoSync').checked = true;
                document.getElementById('syncInterval').value = 30000;
                document.getElementById('codeGenLanguage').value = 'auto-detect';
                showMessage('Settings reset to defaults', 'success');
              }
            });

            function showMessage(text, type) {
              const el = document.getElementById('statusMessage');
              el.textContent = text;
              el.className = 'status-message ' + type;
              setTimeout(() => {
                el.style.display = 'none';
              }, 3000);
            }
          </script>
        </body>
      </html>
    `;
  }

  /**
   * Dispose resources
   */
  dispose(): void {
    if (this.panel) {
      this.panel.dispose();
    }
  }
}
