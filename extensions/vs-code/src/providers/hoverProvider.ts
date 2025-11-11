/**
 * Hover Documentation Provider
 *
 * Shows specification details on hover
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Specification } from '../api/client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class SocratesHoverProvider implements vscode.HoverProvider {
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;
  private specificationCache: Map<string, Specification> = new Map();

  constructor(
    apiClient: SocratesApiClient,
    storage: StorageService
  ) {
    this.apiClient = apiClient;
    this.storage = storage;
    this.logger = new Logger('HoverProvider');
  }

  /**
   * Provide hover information
   */
  async provideHover(
    document: vscode.TextDocument,
    position: vscode.Position,
    token: vscode.CancellationToken
  ): Promise<vscode.Hover | undefined> {
    try {
      // Get word at position
      const word = document.getWordRangeAtPosition(position);
      if (!word) {
        return undefined;
      }

      const specKey = document.getText(word);
      const projectId = this.storage.getSelectedProject();

      if (!projectId) {
        return undefined;
      }

      // Check if this might be a specification key
      if (!this.isLikelySpecKey(specKey)) {
        return undefined;
      }

      // Get specification details
      const spec = await this.getSpecificationByKey(projectId, specKey);
      if (!spec) {
        return undefined;
      }

      // Create hover content
      const content = this.createHoverContent(spec);
      return new vscode.Hover(content, word);
    } catch (error) {
      this.logger.debug(`Hover error: ${error}`);
      return undefined;
    }
  }

  /**
   * Get specification by key
   */
  private async getSpecificationByKey(
    projectId: string,
    key: string
  ): Promise<Specification | undefined> {
    try {
      // Check cache first
      if (this.specificationCache.has(key)) {
        return this.specificationCache.get(key);
      }

      // Fetch from API
      const specs = await this.apiClient.getSpecifications(projectId);
      const spec = specs.find((s) => s.key === key);

      if (spec) {
        this.specificationCache.set(key, spec);
      }

      return spec;
    } catch (error) {
      this.logger.error(`Failed to get specification: ${error}`);
      return undefined;
    }
  }

  /**
   * Create hover content from specification
   */
  private createHoverContent(spec: Specification): vscode.MarkdownString {
    const markdown = new vscode.MarkdownString();

    // Title
    markdown.appendMarkdown(`### ${spec.key}\n\n`);

    // Category badge
    markdown.appendMarkdown(
      `**Category:** \`${spec.category}\` | `
    );

    // Value
    markdown.appendMarkdown(`**Value:** \`${spec.value}\`\n\n`);

    // Content if available
    if (spec.content) {
      markdown.appendMarkdown(
        `**Description:**\n\n${this.escapeMarkdown(spec.content)}\n\n`
      );
    }

    // Metadata
    const createdDate = new Date(spec.created_at).toLocaleDateString();
    markdown.appendMarkdown(
      `**Created:** ${createdDate} | **ID:** \`${spec.id}\`\n\n`
    );

    // Suggested actions
    markdown.appendMarkdown(
      `[View Details](command:socrates.viewSpecification?${encodeURIComponent(
        JSON.stringify(spec.id)
      )}) | ` +
      `[Generate Code](command:socrates.generateCode?${encodeURIComponent(
        JSON.stringify(spec.id)
      )})`
    );

    markdown.isTrusted = true;
    return markdown;
  }

  /**
   * Check if string is likely a specification key
   */
  private isLikelySpecKey(word: string): boolean {
    // Skip if too short or contains spaces
    if (word.length < 3 || /\s/.test(word)) {
      return false;
    }

    // Skip common programming keywords
    const keywords = [
      'function',
      'class',
      'const',
      'let',
      'var',
      'def',
      'if',
      'else',
      'for',
      'while',
      'return',
      'import',
      'export',
      'async',
      'await',
      'this',
      'self',
    ];

    return !keywords.includes(word.toLowerCase());
  }

  /**
   * Clear cache
   */
  clearCache(): void {
    this.specificationCache.clear();
  }

  /**
   * Escape markdown special characters
   */
  private escapeMarkdown(text: string): string {
    return text
      .replace(/\\/g, '\\\\')
      .replace(/\*/g, '\\*')
      .replace(/\[/g, '\\[')
      .replace(/\]/g, '\\]')
      .replace(/\(/g, '\\(')
      .replace(/\)/g, '\\)');
  }
}
