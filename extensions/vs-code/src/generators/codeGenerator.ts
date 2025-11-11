/**
 * Code Generation Manager for Socrates2 VS Code Extension
 *
 * Handles code generation from specifications with multiple language support
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Specification } from '../api/client';
import { Logger } from '../utils/logger';

export interface CodeGenerationOptions {
  language: string;
  specification: Specification;
  insertIntoEditor: boolean;
  createNewFile: boolean;
}

export interface GeneratedCode {
  code: string;
  language: string;
  lineCount: number;
  issues: string[];
}

export class CodeGenerator {
  private apiClient: SocratesApiClient;
  private logger: Logger;

  constructor(apiClient: SocratesApiClient) {
    this.apiClient = apiClient;
    this.logger = new Logger('CodeGenerator');
  }

  /**
   * Show code generation dialog
   */
  async showGenerationDialog(): Promise<CodeGenerationOptions | undefined> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('No active editor');
      return undefined;
    }

    // Get selected text or let user choose
    const selectedText = editor.document.getText(editor.selection);

    // Show language selection
    const languages = ['auto-detect', 'python', 'javascript', 'go', 'java'];
    const language = await vscode.window.showQuickPick(languages, {
      placeHolder: 'Select language for code generation',
      title: 'Code Generation Language',
    });

    if (!language) {
      return undefined;
    }

    // TODO: Would need to get specification from context
    // For now, return placeholder
    return {
      language,
      specification: {} as Specification,
      insertIntoEditor: true,
      createNewFile: false,
    };
  }

  /**
   * Generate code from specification
   */
  async generateCode(
    specification: Specification,
    language: string = 'auto-detect'
  ): Promise<GeneratedCode | undefined> {
    try {
      // Determine actual language if auto-detect
      let targetLanguage = language;
      if (language === 'auto-detect') {
        const editor = vscode.window.activeTextEditor;
        if (editor) {
          targetLanguage = this.detectLanguageFromFile(editor.document.languageId);
        } else {
          targetLanguage = 'python'; // Default
        }
      }

      // Show progress
      const result = await vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: `Generating ${targetLanguage} code...`,
          cancellable: false,
        },
        async () => {
          return await this.apiClient.generateCode(
            specification.id,
            targetLanguage,
            {
              category: specification.category,
              key: specification.key,
            }
          );
        }
      );

      this.logger.info(`Generated code for ${specification.key} in ${targetLanguage}`);

      return {
        code: result,
        language: targetLanguage,
        lineCount: result.split('\n').length,
        issues: [],
      };
    } catch (error) {
      this.logger.error(`Code generation failed: ${error}`);
      vscode.window.showErrorMessage(`Code generation failed: ${error}`);
      return undefined;
    }
  }

  /**
   * Insert generated code into editor
   */
  async insertCodeIntoEditor(generatedCode: GeneratedCode): Promise<boolean> {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
      vscode.window.showErrorMessage('No active editor');
      return false;
    }

    try {
      await editor.edit((editBuilder) => {
        const position = editor.selection.active;
        editBuilder.insert(position, generatedCode.code + '\n');
      });

      vscode.window.showInformationMessage(
        `Generated ${generatedCode.lineCount} lines of ${generatedCode.language} code`
      );

      return true;
    } catch (error) {
      this.logger.error(`Failed to insert code: ${error}`);
      vscode.window.showErrorMessage(`Failed to insert code: ${error}`);
      return false;
    }
  }

  /**
   * Create new file with generated code
   */
  async createNewFile(
    generatedCode: GeneratedCode,
    filename: string
  ): Promise<boolean> {
    try {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders) {
        vscode.window.showErrorMessage('No workspace folder open');
        return false;
      }

      const filePath = vscode.Uri.joinPath(
        workspaceFolders[0].uri,
        filename
      );

      // Create file with content
      const fileContent = new TextEncoder().encode(generatedCode.code);
      await vscode.workspace.fs.writeFile(filePath, fileContent);

      // Open the file
      const document = await vscode.workspace.openTextDocument(filePath);
      await vscode.window.showTextDocument(document);

      vscode.window.showInformationMessage(
        `Created file: ${filename}`
      );

      return true;
    } catch (error) {
      this.logger.error(`Failed to create file: ${error}`);
      vscode.window.showErrorMessage(`Failed to create file: ${error}`);
      return false;
    }
  }

  /**
   * Detect language from VS Code language ID
   */
  private detectLanguageFromFile(languageId: string): string {
    const languageMap: { [key: string]: string } = {
      'python': 'python',
      'javascript': 'javascript',
      'typescript': 'javascript',
      'go': 'go',
      'java': 'java',
      'cpp': 'javascript', // Default to JS for C++
      'csharp': 'javascript', // Default to JS for C#
      'ruby': 'python', // Default to Python for Ruby
      'php': 'javascript', // Default to JS for PHP
    };

    return languageMap[languageId] || 'python';
  }

  /**
   * Format generated code
   */
  async formatCode(
    code: string,
    language: string
  ): Promise<string> {
    try {
      // For now, just return as-is
      // In production, could call language-specific formatters
      // (black for Python, prettier for JS, etc.)
      return code;
    } catch (error) {
      this.logger.error(`Code formatting failed: ${error}`);
      return code; // Return unformatted if formatting fails
    }
  }

  /**
   * Copy code to clipboard
   */
  async copyToClipboard(code: string): Promise<boolean> {
    try {
      await vscode.env.clipboard.writeText(code);
      vscode.window.showInformationMessage('Code copied to clipboard');
      return true;
    } catch (error) {
      this.logger.error(`Failed to copy to clipboard: ${error}`);
      return false;
    }
  }

  /**
   * Show code preview in panel
   */
  async showCodePreview(generatedCode: GeneratedCode): Promise<void> {
    const panel = vscode.window.createWebviewPanel(
      'codePreview',
      'Generated Code Preview',
      vscode.ViewColumn.Side,
      {
        enableScripts: true,
        localResourceRoots: [],
      }
    );

    const syntaxHighlightedCode = this.escapeHtml(generatedCode.code);

    panel.webview.html = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="UTF-8">
          <title>Code Preview</title>
          <style>
            body {
              font-family: 'Courier New', monospace;
              margin: 0;
              padding: 20px;
              background-color: var(--vscode-editor-background);
              color: var(--vscode-editor-foreground);
            }
            .header {
              display: flex;
              justify-content: space-between;
              align-items: center;
              margin-bottom: 20px;
              padding-bottom: 10px;
              border-bottom: 1px solid var(--vscode-editor-lineHighlightBackground);
            }
            .title {
              font-size: 18px;
              font-weight: bold;
            }
            .actions {
              display: flex;
              gap: 10px;
            }
            button {
              background-color: var(--vscode-button-background);
              color: var(--vscode-button-foreground);
              border: none;
              padding: 8px 16px;
              border-radius: 4px;
              cursor: pointer;
              font-size: 14px;
            }
            button:hover {
              background-color: var(--vscode-button-hoverBackground);
            }
            .code-block {
              background-color: var(--vscode-editor-background);
              border: 1px solid var(--vscode-editor-lineHighlightBackground);
              border-radius: 4px;
              padding: 16px;
              overflow-x: auto;
              line-height: 1.5;
            }
            .line-number {
              display: inline-block;
              width: 30px;
              text-align: right;
              margin-right: 10px;
              color: var(--vscode-editorLineNumber-foreground);
              user-select: none;
            }
            .metadata {
              margin-top: 20px;
              padding: 10px;
              background-color: var(--vscode-editor-lineHighlightBackground);
              border-radius: 4px;
              font-size: 12px;
            }
          </style>
        </head>
        <body>
          <div class="header">
            <div class="title">${generatedCode.language} Code (${generatedCode.lineCount} lines)</div>
            <div class="actions">
              <button onclick="copyCode()">Copy</button>
              <button onclick="insertCode()">Insert</button>
            </div>
          </div>
          <div class="code-block"><code>${syntaxHighlightedCode}</code></div>
          <div class="metadata">
            ${generatedCode.issues.length > 0
              ? '<strong>Issues:</strong> ' + generatedCode.issues.join(', ')
              : '<strong>Status:</strong> No issues found'
            }
          </div>
          <script>
            function copyCode() {
              // Handled by VS Code command
              vscode.postMessage({ command: 'copy' });
            }
            function insertCode() {
              vscode.postMessage({ command: 'insert' });
            }
          </script>
        </body>
      </html>
    `;

    panel.webview.onDidReceiveMessage((message) => {
      if (message.command === 'copy') {
        this.copyToClipboard(generatedCode.code);
      } else if (message.command === 'insert') {
        this.insertCodeIntoEditor(generatedCode);
      }
    });
  }

  /**
   * Escape HTML special characters
   */
  private escapeHtml(text: string): string {
    const map: { [key: string]: string } = {
      '&': '&amp;',
      '<': '&lt;',
      '>': '&gt;',
      '"': '&quot;',
      "'": '&#039;',
    };
    return text.replace(/[&<>"']/g, (char) => map[char]);
  }
}
