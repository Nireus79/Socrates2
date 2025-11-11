/**
 * Socrates2 VS Code Extension
 *
 * Main entry point for the extension.
 * Initializes views, commands, and core functionality.
 */

import * as vscode from 'vscode';
import { SocratesApiClient } from './api/client';
import { AuthenticationService } from './api/auth';
import { ProjectBrowserProvider } from './views/projectBrowser';
import { SpecificationViewerProvider } from './views/specificationViewer';
import { ActivityViewProvider } from './views/activityView';
import { StorageService } from './utils/storage';
import { Logger } from './utils/logger';

let context: vscode.ExtensionContext;
let apiClient: SocratesApiClient;
let authService: AuthenticationService;
let storage: StorageService;
let logger: Logger;

// View providers
let projectBrowserProvider: ProjectBrowserProvider;
let specificationViewerProvider: SpecificationViewerProvider;
let activityViewProvider: ActivityViewProvider;

/**
 * Activate the extension
 */
export async function activate(ctx: vscode.ExtensionContext) {
  context = ctx;
  logger = new Logger('socrates');
  storage = new StorageService(context);

  logger.info('Socrates2 extension activating...');

  try {
    // Initialize services
    const config = vscode.workspace.getConfiguration('socrates');
    const apiUrl = config.get<string>('apiUrl') || 'http://localhost:8000';

    apiClient = new SocratesApiClient(apiUrl, storage);
    authService = new AuthenticationService(apiClient, storage);

    // Initialize view providers
    projectBrowserProvider = new ProjectBrowserProvider(apiClient, storage, logger);
    specificationViewerProvider = new SpecificationViewerProvider(apiClient, storage, logger);
    activityViewProvider = new ActivityViewProvider(apiClient, storage, logger);

    // Register tree view providers
    vscode.window.registerTreeDataProvider('projects', projectBrowserProvider);
    vscode.window.registerTreeDataProvider('specifications', specificationViewerProvider);
    vscode.window.registerTreeDataProvider('activity', activityViewProvider);

    // Register commands
    registerCommands(context);

    // Update authentication status
    await updateAuthStatus();

    // Start auto-sync if enabled
    const autoSync = config.get<boolean>('autoSync', true);
    if (autoSync) {
      startAutoSync();
    }

    // Listen for configuration changes
    vscode.workspace.onDidChangeConfiguration((event) => {
      if (event.affectsConfiguration('socrates')) {
        onConfigurationChanged();
      }
    });

    logger.info('Socrates2 extension activated successfully');
  } catch (error) {
    logger.error(`Failed to activate extension: ${error}`);
    vscode.window.showErrorMessage('Failed to activate Socrates2 extension');
  }
}

/**
 * Deactivate the extension
 */
export function deactivate() {
  logger.info('Socrates2 extension deactivating...');
}

/**
 * Register all commands
 */
function registerCommands(ctx: vscode.ExtensionContext) {
  const commands = [
    // Authentication
    {
      command: 'socrates.authenticate',
      handler: authenticateCommand,
    },
    {
      command: 'socrates.logout',
      handler: logoutCommand,
    },

    // Projects
    {
      command: 'socrates.refreshProjects',
      handler: refreshProjectsCommand,
    },
    {
      command: 'socrates.createProject',
      handler: createProjectCommand,
    },
    {
      command: 'socrates.openProject',
      handler: openProjectCommand,
    },

    // Specifications
    {
      command: 'socrates.refreshSpecifications',
      handler: refreshSpecificationsCommand,
    },
    {
      command: 'socrates.viewSpecification',
      handler: viewSpecificationCommand,
    },
    {
      command: 'socrates.generateCode',
      handler: generateCodeCommand,
    },
    {
      command: 'socrates.searchSpecifications',
      handler: searchSpecificationsCommand,
    },

    // Conflicts
    {
      command: 'socrates.viewConflicts',
      handler: viewConflictsCommand,
    },

    // Activity
    {
      command: 'socrates.showActivity',
      handler: showActivityCommand,
    },

    // Settings
    {
      command: 'socrates.openSettings',
      handler: openSettingsCommand,
    },
  ];

  for (const { command, handler } of commands) {
    ctx.subscriptions.push(
      vscode.commands.registerCommand(command, handler)
    );
  }
}

/**
 * Command: Authenticate user
 */
async function authenticateCommand() {
  try {
    const success = await authService.authenticate();
    if (success) {
      vscode.window.showInformationMessage('Successfully signed in to Socrates2');
      await updateAuthStatus();
      projectBrowserProvider.refresh();
    } else {
      vscode.window.showErrorMessage('Authentication failed');
    }
  } catch (error) {
    logger.error(`Authentication error: ${error}`);
    vscode.window.showErrorMessage(`Authentication error: ${error}`);
  }
}

/**
 * Command: Logout user
 */
async function logoutCommand() {
  try {
    await authService.logout();
    vscode.window.showInformationMessage('Signed out from Socrates2');
    await updateAuthStatus();
    projectBrowserProvider.refresh();
  } catch (error) {
    logger.error(`Logout error: ${error}`);
    vscode.window.showErrorMessage(`Logout error: ${error}`);
  }
}

/**
 * Command: Refresh projects list
 */
async function refreshProjectsCommand() {
  try {
    projectBrowserProvider.refresh();
    vscode.window.showInformationMessage('Projects refreshed');
  } catch (error) {
    logger.error(`Refresh error: ${error}`);
  }
}

/**
 * Command: Create new project
 */
async function createProjectCommand() {
  try {
    const isAuthenticated = await authService.isAuthenticated();
    if (!isAuthenticated) {
      vscode.window.showErrorMessage('Please sign in first');
      return;
    }

    const projectName = await vscode.window.showInputBox({
      prompt: 'Project name',
      placeHolder: 'My Project',
    });

    if (!projectName) {
      return;
    }

    const description = await vscode.window.showInputBox({
      prompt: 'Project description (optional)',
      placeHolder: 'Project description...',
    });

    // TODO: Call API to create project
    vscode.window.showInformationMessage(`Creating project: ${projectName}`);
    projectBrowserProvider.refresh();
  } catch (error) {
    logger.error(`Create project error: ${error}`);
    vscode.window.showErrorMessage(`Failed to create project: ${error}`);
  }
}

/**
 * Command: Open project
 */
async function openProjectCommand(item: any) {
  try {
    logger.info(`Opening project: ${item.id}`);
    // TODO: Open project details or load its specifications
  } catch (error) {
    logger.error(`Open project error: ${error}`);
  }
}

/**
 * Command: Refresh specifications
 */
async function refreshSpecificationsCommand() {
  try {
    specificationViewerProvider.refresh();
    vscode.window.showInformationMessage('Specifications refreshed');
  } catch (error) {
    logger.error(`Refresh specifications error: ${error}`);
  }
}

/**
 * Command: View specification details
 */
async function viewSpecificationCommand(item: any) {
  try {
    logger.info(`Viewing specification: ${item.id}`);
    // TODO: Show specification details in a panel
  } catch (error) {
    logger.error(`View specification error: ${error}`);
  }
}

/**
 * Command: Generate code from specification
 */
async function generateCodeCommand(item?: any) {
  try {
    const isAuthenticated = await authService.isAuthenticated();
    if (!isAuthenticated) {
      vscode.window.showErrorMessage('Please sign in first');
      return;
    }

    // TODO: Show code generation dialog
    vscode.window.showInformationMessage('Code generation feature coming soon');
  } catch (error) {
    logger.error(`Code generation error: ${error}`);
    vscode.window.showErrorMessage(`Code generation error: ${error}`);
  }
}

/**
 * Command: Search specifications
 */
async function searchSpecificationsCommand() {
  try {
    const query = await vscode.window.showInputBox({
      prompt: 'Search specifications',
      placeHolder: 'Enter search query...',
    });

    if (!query) {
      return;
    }

    logger.info(`Searching specifications: ${query}`);
    // TODO: Implement search functionality
  } catch (error) {
    logger.error(`Search error: ${error}`);
  }
}

/**
 * Command: View conflicts
 */
async function viewConflictsCommand() {
  try {
    const isAuthenticated = await authService.isAuthenticated();
    if (!isAuthenticated) {
      vscode.window.showErrorMessage('Please sign in first');
      return;
    }

    logger.info('Viewing specification conflicts');
    // TODO: Show conflicts in a panel
  } catch (error) {
    logger.error(`View conflicts error: ${error}`);
  }
}

/**
 * Command: Show team activity
 */
async function showActivityCommand() {
  try {
    activityViewProvider.refresh();
  } catch (error) {
    logger.error(`Show activity error: ${error}`);
  }
}

/**
 * Command: Open settings
 */
async function openSettingsCommand() {
  try {
    vscode.commands.executeCommand('workbench.action.openSettings', 'socrates');
  } catch (error) {
    logger.error(`Open settings error: ${error}`);
  }
}

/**
 * Update authentication status context variable
 */
async function updateAuthStatus() {
  try {
    const isAuthenticated = await authService.isAuthenticated();
    vscode.commands.executeCommand('setContext', 'socrates.authenticated', isAuthenticated);
  } catch (error) {
    logger.error(`Failed to update auth status: ${error}`);
  }
}

/**
 * Handle configuration changes
 */
function onConfigurationChanged() {
  logger.info('Configuration changed');

  const config = vscode.workspace.getConfiguration('socrates');
  const autoSync = config.get<boolean>('autoSync', true);

  if (autoSync) {
    startAutoSync();
  } else {
    stopAutoSync();
  }
}

let syncInterval: NodeJS.Timeout | undefined;

/**
 * Start auto-sync timer
 */
function startAutoSync() {
  if (syncInterval) {
    return; // Already running
  }

  const config = vscode.workspace.getConfiguration('socrates');
  const interval = config.get<number>('syncInterval', 30000);

  syncInterval = setInterval(async () => {
    try {
      projectBrowserProvider.refresh();
      specificationViewerProvider.refresh();
      activityViewProvider.refresh();
    } catch (error) {
      logger.error(`Auto-sync error: ${error}`);
    }
  }, interval);

  logger.info(`Auto-sync started with interval ${interval}ms`);
}

/**
 * Stop auto-sync timer
 */
function stopAutoSync() {
  if (syncInterval) {
    clearInterval(syncInterval);
    syncInterval = undefined;
    logger.info('Auto-sync stopped');
  }
}
