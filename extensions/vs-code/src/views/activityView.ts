/**
 * Activity View Provider
 *
 * Displays team activity feed
 */

import * as vscode from 'vscode';
import { SocratesApiClient, Activity } from '../api/client';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export class ActivityViewProvider implements vscode.TreeDataProvider<ActivityItem> {
  private apiClient: SocratesApiClient;
  private storage: StorageService;
  private logger: Logger;

  private _onDidChangeTreeData: vscode.EventEmitter<
    ActivityItem | undefined | null | void
  > = new vscode.EventEmitter<ActivityItem | undefined | null | void>();
  readonly onDidChangeTreeData: vscode.Event<
    ActivityItem | undefined | null | void
  > = this._onDidChangeTreeData.event;

  private activities: Activity[] = [];
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
  getTreeItem(element: ActivityItem): vscode.TreeItem {
    return element;
  }

  /**
   * Get children
   */
  getChildren(element?: ActivityItem): Thenable<ActivityItem[]> {
    if (!element) {
      return Promise.resolve(this.getActivityItems());
    }
    return Promise.resolve([]);
  }

  /**
   * Get activity items for display
   */
  private getActivityItems(): ActivityItem[] {
    const projectId = this.storage.getSelectedProject();

    if (!projectId) {
      return [
        new ActivityItem(
          'Select a project first',
          vscode.TreeItemCollapsibleState.None,
          'no-project'
        ),
      ];
    }

    if (this.loading) {
      return [
        new ActivityItem(
          'Loading...',
          vscode.TreeItemCollapsibleState.None,
          'loading'
        ),
      ];
    }

    if (this.error) {
      return [
        new ActivityItem(
          `Error: ${this.error.message}`,
          vscode.TreeItemCollapsibleState.None,
          'error'
        ),
      ];
    }

    if (this.activities.length === 0) {
      return [
        new ActivityItem(
          'No recent activity',
          vscode.TreeItemCollapsibleState.None,
          'no-activity'
        ),
      ];
    }

    return this.activities.map(
      (activity) =>
        new ActivityItem(
          activity.description,
          vscode.TreeItemCollapsibleState.None,
          'activity',
          {
            activityId: activity.id,
            actionType: activity.action_type,
            timestamp: activity.created_at,
          }
        )
    );
  }

  /**
   * Load activity for project
   */
  async loadActivity(projectId: string): Promise<void> {
    this.loading = true;
    this.error = null;
    this._onDidChangeTreeData.fire();

    try {
      this.activities = await this.apiClient.getActivity(projectId, 50);
      this.logger.info(`Loaded ${this.activities.length} activities`);
    } catch (error) {
      this.error = error instanceof Error ? error : new Error(String(error));
      this.logger.error(`Failed to load activity: ${error}`);
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
      this.loadActivity(projectId);
    } else {
      this._onDidChangeTreeData.fire();
    }
  }
}

/**
 * Activity tree item
 */
export class ActivityItem extends vscode.TreeItem {
  public activityId?: string;
  public actionType?: string;
  public timestamp?: string;

  constructor(
    label: string,
    collapsibleState: vscode.TreeItemCollapsibleState,
    type: 'activity' | 'loading' | 'error' | 'no-activity' | 'no-project',
    data?: any
  ) {
    super(label, collapsibleState);

    this.activityId = data?.activityId;
    this.actionType = data?.actionType;
    this.timestamp = data?.timestamp;

    this.contextValue = type;

    switch (type) {
      case 'activity':
        this.iconPath = new vscode.ThemeIcon('history');
        this.description = this.formatTimestamp(data?.timestamp);
        this.tooltip = new vscode.MarkdownString(
          `**${label}**\n\nType: ${data?.actionType}\n\nTime: ${data?.timestamp}`
        );
        break;
      case 'loading':
        this.iconPath = new vscode.ThemeIcon('loading~spin');
        break;
      case 'error':
        this.iconPath = new vscode.ThemeIcon('error');
        break;
      case 'no-activity':
      case 'no-project':
        this.iconPath = new vscode.ThemeIcon('info');
        break;
    }
  }

  /**
   * Format timestamp to relative time
   */
  private formatTimestamp(timestamp?: string): string {
    if (!timestamp) {
      return '';
    }

    const date = new Date(timestamp);
    const now = new Date();
    const diff = now.getTime() - date.getTime();

    const minutes = Math.floor(diff / 60000);
    const hours = Math.floor(diff / 3600000);
    const days = Math.floor(diff / 86400000);

    if (minutes < 1) return 'just now';
    if (minutes < 60) return `${minutes}m ago`;
    if (hours < 24) return `${hours}h ago`;
    if (days < 7) return `${days}d ago`;

    return date.toLocaleDateString();
  }
}
