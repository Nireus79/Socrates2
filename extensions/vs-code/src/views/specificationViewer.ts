/**
 * Specification Viewer View Provider
 *
 * Displays specifications for the selected project
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Specification } from '../api/client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class SpecificationViewerProvider
  implements vscode.TreeDataProvider<SpecificationItem>
{
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;

  private _onDidChangeTreeData: vscode.EventEmitter<
    SpecificationItem | undefined | null | void
  > = new vscode.EventEmitter<
    SpecificationItem | undefined | null | void
  >();
  readonly onDidChangeTreeData: vscode.Event<
    SpecificationItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private specifications: Specification[] = [];
  private loading = false;
  private error: Error | null = null;

  constructor(
    apiClient: SocratesApiClient,
    storage: StorageService,
    logger: Logger
  ) {
    this.apiClient = apiClient;
    this.storage = storage;
    this.logger = logger;
  }

  /**
   * Get tree item
   */
  getTreeItem(element: SpecificationItem): vscode.TreeItem {
    return element;
  }

  /**
   * Get children
   */
  getChildren(element?: SpecificationItem): Thenable<SpecificationItem[]> {
    if (!element) {
      return Promise.resolve(this.getSpecificationItems());
    }
    return Promise.resolve([]);
  }

  /**
   * Get specification items for display
   */
  private getSpecificationItems(): SpecificationItem[] {
    const projectId = this.storage.getSelectedProject();

    if (!projectId) {
      return [
        new SpecificationItem(
          'Select a project first',
          vscode.TreeItemCollapsibleState.None,
          'no-project'
        ),
      ];
    }

    if (this.loading) {
      return [
        new SpecificationItem(
          'Loading...',
          vscode.TreeItemCollapsibleState.None,
          'loading'
        ),
      ];
    }

    if (this.error) {
      return [
        new SpecificationItem(
          `Error: ${this.error.message}`,
          vscode.TreeItemCollapsibleState.None,
          'error'
        ),
      ];
    }

    if (this.specifications.length === 0) {
      return [
        new SpecificationItem(
          'No specifications found',
          vscode.TreeItemCollapsibleState.None,
          'no-specs'
        ),
      ];
    }

    // Group specifications by category
    const grouped = new Map<string, Specification[]>();
    for (const spec of this.specifications) {
      if (!grouped.has(spec.category)) {
        grouped.set(spec.category, []);
      }
      grouped.get(spec.category)!.push(spec);
    }

    const items: SpecificationItem[] = [];
    for (const [category, specs] of grouped) {
      items.push(
        new SpecificationItem(
          category,
          vscode.TreeItemCollapsibleState.Collapsed,
          'category'
        )
      );

      for (const spec of specs) {
        items.push(
          new SpecificationItem(
            spec.key,
            vscode.TreeItemCollapsibleState.None,
            'specification',
            {
              specId: spec.id,
              category: spec.category,
              value: spec.value,
            }
          )
        );
      }
    }

    return items;
  }

  /**
   * Load specifications for project
   */
  async loadSpecifications(projectId: string): Promise<void> {
    this.loading = true;
    this.error = null;
    this._onDidChangeTreeData.fire();

    try {
      this.specifications = await this.apiClient.getSpecifications(projectId);
      this.logger.info(`Loaded ${this.specifications.length} specifications`);
    } catch (error) {
      this.error = error instanceof Error ? error : new Error(String(error));
      this.logger.error(`Failed to load specifications: ${error}`);
    } finally {
      this.loading = false;
      this._onDidChangeTreeData.fire();
    }
  }

  /**
   * Refresh the tree
   */
  refresh(): void {
    const projectId = this.storage.getSelectedProject();
    if (projectId) {
      this.loadSpecifications(projectId);
    } else {
      this._onDidChangeTreeData.fire();
    }
  }
}

/**
 * Specification tree item
 */
export class SpecificationItem extends vscode.TreeItem {
  public specId?: string;
  public category?: string;
  public value?: string;

  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    type: 'specification' | 'category' | 'loading' | 'error' | 'no-specs' | 'no-project',
    data?: any
  ) {
    super(label, collapsibleState);

    this.specId = data?.specId;
    this.category = data?.category;
    this.value = data?.value;

    this.contextValue = type;

    switch (type) {
      case 'specification':
        this.iconPath = new vscode.ThemeIcon('symbol-variable');
        this.description = data?.value;
        this.tooltip = new vscode.MarkdownString(
          `**${label}**\n\nCategory: ${data?.category}\n\nValue: ${data?.value}`
        );
        this.command = {
          command: 'socrates.viewSpecification',
          title: 'View Details',
          arguments: [this],
        };
        break;
      case 'category':
        this.iconPath = new vscode.ThemeIcon('folder');
        break;
      case 'loading':
        this.iconPath = new vscode.ThemeIcon('loading~spin');
        break;
      case 'error':
        this.iconPath = new vscode.ThemeIcon('error');
        break;
      case 'no-specs':
      case 'no-project':
        this.iconPath = new vscode.ThemeIcon('info');
        break;
    }
  }
}
