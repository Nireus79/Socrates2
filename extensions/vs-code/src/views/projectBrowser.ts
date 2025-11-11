/**
 * Project Browser View Provider
 *
 * Displays list of user projects in tree view
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Project } from '../api/client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class ProjectBrowserProvider
  implements vscode.TreeDataProvider<ProjectItem>
{
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;

  private _onDidChangeTreeData: vscode.EventEmitter<
    ProjectItem | undefined | null | void
  > = new vscode.EventEmitter<ProjectItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    ProjectItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private projects: Project[] = [];
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

    // Load projects on initialization
    this.loadProjects();
  }

  /**
   * Get tree item
   */
  getTreeItem(element: ProjectItem): vscode.TreeItem {
    return element;
  }

  /**
   * Get children
   */
  getChildren(element?: ProjectItem): Thenable<ProjectItem[]> {
    // If root, return projects
    if (!element) {
      return Promise.resolve(this.getProjectItems());
    }

    // If project item, return no children (leaf node)
    return Promise.resolve([]);
  }

  /**
   * Get project items for display
   */
  private getProjectItems(): ProjectItem[] {
    if (this.loading) {
      return [
        new ProjectItem(
          'Loading...',
          vscode.TreeItemCollapsibleState.None,
          'loading'
        ),
      ];
    }

    if (this.error) {
      return [
        new ProjectItem(
          `Error: ${this.error.message}`,
          vscode.TreeItemCollapsibleState.None,
          'error'
        ),
      ];
    }

    if (this.projects.length === 0) {
      return [
        new ProjectItem(
          'No projects found. Create one to get started!',
          vscode.TreeItemCollapsibleState.None,
          'no-projects'
        ),
      ];
    }

    return this.projects.map(
      (project) =>
        new ProjectItem(
          project.name,
          vscode.TreeItemCollapsibleState.None,
          'project',
          {
            projectId: project.id,
            description: project.description,
            maturityScore: project.maturity_score,
            status: project.status,
          }
        )
    );
  }

  /**
   * Load projects from API
   */
  private async loadProjects(): Promise<void> {
    this.loading = true;
    this.error = null;
    this._onDidChangeTreeData.fire();

    try {
      this.projects = await this.apiClient.getProjects();
      this.logger.info(`Loaded ${this.projects.length} projects`);
    } catch (error) {
      this.error = error instanceof Error ? error : new Error(String(error));
      this.logger.error(`Failed to load projects: ${error}`);
    } finally {
      this.loading = false;
      this._onDidChangeTreeData.fire();
    }
  }

  /**
   * Refresh the tree
   */
  refresh(): void {
    this.loadProjects();
  }

  /**
   * Get selected project
   */
  getSelectedProject(): string | null {
    return this.storage.getSelectedProject();
  }

  /**
   * Set selected project
   */
  setSelectedProject(projectId: string): void {
    this.storage.setSelectedProject(projectId);
    this._onDidChangeTreeData.fire();
  }
}

/**
 * Project tree item
 */
export class ProjectItem extends vscode.TreeItem {
  public projectId?: string;
  public description?: string;
  public maturityScore?: number;
  public status?: string;

  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    type: 'project' | 'loading' | 'error' | 'no-projects',
    data?: any
  ) {
    super(label, collapsibleState);

    this.projectId = data?.projectId;
    this.description = data?.description;
    this.maturityScore = data?.maturityScore;
    this.status = data?.status;

    // Set context value for conditional commands
    this.contextValue = type;

    // Set icon based on type
    switch (type) {
      case 'project':
        this.iconPath = new vscode.ThemeIcon('folder');
        this.tooltip = new vscode.MarkdownString(
          `**${label}**\n\n${data?.description || 'No description'}\n\nMaturity: ${data?.maturityScore || 0}%`
        );
        this.command = {
          command: 'socrates.openProject',
          title: 'Open Project',
          arguments: [this],
        };
        break;
      case 'loading':
        this.iconPath = new vscode.ThemeIcon('loading~spin');
        break;
      case 'error':
        this.iconPath = new vscode.ThemeIcon('error');
        break;
      case 'no-projects':
        this.iconPath = new vscode.ThemeIcon('info');
        break;
    }
  }
}
