/**
 * Specification Conflict Detection Provider
 *
 * Detects and displays conflicts in editor decorations and diagnostics
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Conflict } from '../api/client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class ConflictProvider {
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;

  private diagnosticCollection: vscode.DiagnosticCollection;
  private decorationType: vscode.TextEditorDecorationType;

  constructor(
    apiClient: SocratesApiClient,
    storage: StorageService,
    context: vscode.ExtensionContext
  ) {
    this.apiClient = apiClient;
    this.storage = storage;
    this.logger = new Logger('ConflictProvider');

    // Create diagnostic collection
    this.diagnosticCollection = vscode.languages.createDiagnosticCollection(
      'socrates-conflicts'
    );

    // Create decoration type for conflict warnings
    this.decorationType = vscode.window.createTextEditorDecorationType({
      backgroundColor: new vscode.ThemeColor('editor.warningBackground'),
      borderColor: new vscode.ThemeColor('editor.warningBorder'),
      borderStyle: 'dashed',
      borderWidth: '1px',
      isWholeLine: false,
      overviewRulerColor: new vscode.ThemeColor('editorWarning.foreground'),
      overviewRulerLane: vscode.OverviewRulerLane.Right,
    });

    context.subscriptions.push(this.diagnosticCollection);
    context.subscriptions.push(this.decorationType);
  }

  /**
   * Check and display conflicts for active project
   */
  async checkConflicts(): Promise<void> {
    try {
      const projectId = this.storage.getSelectedProject();
      if (!projectId) {
        this.diagnosticCollection.clear();
        return;
      }

      const conflicts = await this.apiClient.getConflicts(projectId);
      if (conflicts.length === 0) {
        this.diagnosticCollection.clear();
        this.clearAllDecorations();
        return;
      }

      // Create diagnostics for each conflict
      const diagnostics: { [key: string]: vscode.Diagnostic[] } = {};

      for (const conflict of conflicts) {
        const diagnostic = this.createConflictDiagnostic(conflict);
        const editor = vscode.window.activeTextEditor;

        if (editor) {
          const key = editor.document.uri.toString();
          if (!diagnostics[key]) {
            diagnostics[key] = [];
          }
          diagnostics[key].push(diagnostic);
        }
      }

      // Apply diagnostics
      for (const [uri, diags] of Object.entries(diagnostics)) {
        this.diagnosticCollection.set(vscode.Uri.parse(uri), diags);
      }

      // Update decorations in active editor
      if (vscode.window.activeTextEditor) {
        await this.updateDecorationsForConflicts(
          vscode.window.activeTextEditor,
          conflicts
        );
      }

      // Show conflict count in status bar
      this.showConflictStatus(conflicts.length);
    } catch (error) {
      this.logger.error(`Failed to check conflicts: ${error}`);
    }
  }

  /**
   * Create diagnostic for conflict
   */
  private createConflictDiagnostic(conflict: Conflict): vscode.Diagnostic {
    const range = new vscode.Range(0, 0, 0, 1);

    const diagnostic = new vscode.Diagnostic(
      range,
      `Specification conflict: ${conflict.description}`,
      vscode.DiagnosticSeverity.Warning
    );

    diagnostic.code = {
      value: `conflict-${conflict.id}`,
      target: vscode.Uri.parse(
        `https://localhost:8000/conflicts/${conflict.id}`
      ),
    };

    diagnostic.source = 'Socrates2';
    diagnostic.relatedInformation = [
      new vscode.DiagnosticRelatedInformation(
        new vscode.Location(vscode.window.activeTextEditor?.document.uri || vscode.Uri.parse('file:///unknown'), range),
        `Severity: ${conflict.severity}`
      ),
    ];

    return diagnostic;
  }

  /**
   * Update editor decorations for conflicts
   */
  private async updateDecorationsForConflicts(
    editor: vscode.TextEditor,
    conflicts: Conflict[]
  ): Promise<void> {
    const decorations: vscode.DecorationOptions[] = [];

    for (const conflict of conflicts) {
      // Find text matching specification IDs in document
      const ranges = this.findSpecificationReferences(
        editor.document,
        conflict.spec1_id
      );

      for (const range of ranges) {
        decorations.push({
          range,
          hoverMessage: new vscode.MarkdownString(
            `**Conflict:** ${conflict.description}\n\nSeverity: ${conflict.severity}`
          ),
        });
      }
    }

    editor.setDecorations(this.decorationType, decorations);
  }

  /**
   * Find specification references in document
   */
  private findSpecificationReferences(
    document: vscode.TextDocument,
    specId: string
  ): vscode.Range[] {
    const ranges: vscode.Range[] = [];
    const text = document.getText();

    // Simple pattern matching - could be enhanced
    const pattern = new RegExp(`\\b${specId}\\b`, 'g');
    let match;

    while ((match = pattern.exec(text)) !== null) {
      const startPos = document.positionAt(match.index);
      const endPos = document.positionAt(match.index + match[0].length);
      ranges.push(new vscode.Range(startPos, endPos));
    }

    return ranges;
  }

  /**
   * Clear all decorations
   */
  private clearAllDecorations(): void {
    for (const editor of vscode.window.visibleTextEditors) {
      editor.setDecorations(this.decorationType, []);
    }
  }

  /**
   * Show conflict count in status bar
   */
  private showConflictStatus(count: number): void {
    if (count > 0) {
      const statusBar = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
      );
      statusBar.text = `$(warning) ${count} Specification Conflicts`;
      statusBar.command = 'socrates.viewConflicts';
      statusBar.show();
    }
  }

  /**
   * Dispose resources
   */
  dispose(): void {
    this.diagnosticCollection.dispose();
    this.decorationType.dispose();
  }
}
