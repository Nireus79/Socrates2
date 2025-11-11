/**
 * Jest Test Setup File
 *
 * Global test configuration and mocks
 */

// Mock VS Code API globally
jest.mock('vscode', () => ({
  window: {
    showInformationMessage: jest.fn(),
    showErrorMessage: jest.fn(),
    showWarningMessage: jest.fn(),
    showInputBox: jest.fn(),
    showQuickPick: jest.fn(),
    showOpenDialog: jest.fn(),
    withProgress: jest.fn((options, task) => task()),
    createOutputChannel: jest.fn(() => ({
      appendLine: jest.fn(),
      show: jest.fn(),
      dispose: jest.fn(),
      clear: jest.fn(),
    })),
  },
  commands: {
    registerCommand: jest.fn(),
    executeCommand: jest.fn(),
  },
  workspace: {
    getConfiguration: jest.fn(() => ({
      get: jest.fn(),
      update: jest.fn(),
      has: jest.fn(),
    })),
    onDidChangeConfiguration: jest.fn(() => ({
      dispose: jest.fn(),
    })),
    openTextDocument: jest.fn(),
    workspaceFolders: [],
  },
  languages: {
    registerHoverProvider: jest.fn(),
    registerCodeActionProvider: jest.fn(),
  },
  ViewColumn: {
    One: 1,
    Two: 2,
    Three: 3,
    Beside: -2,
  },
  Uri: {
    file: jest.fn((path) => ({ path, scheme: 'file', fsPath: path })),
    parse: jest.fn((uri) => ({ path: uri, scheme: 'file', fsPath: uri })),
  },
  StatusBarAlignment: {
    Left: 1,
    Right: 2,
  },
  TreeItemCollapsibleState: {
    None: 0,
    Collapsed: 1,
    Expanded: 2,
  },
  TreeItem: class TreeItem {
    constructor(public label: string, public collapsibleState?: any) {}
  },
  EventEmitter: class EventEmitter {
    private listeners: Array<(event: any) => void> = [];

    get event() {
      return (listener: (event: any) => void) => {
        this.listeners.push(listener);
        return { dispose: () => {} };
      };
    }

    fire(event?: any) {
      this.listeners.forEach((listener) => listener(event));
    }
  },
  ThemeIcon: class ThemeIcon {
    constructor(public id: string) {}
  },
  MarkdownString: class MarkdownString {
    constructor(public value: string) {}
  },
}), { virtual: true });

// Suppress console output during tests (optional)
global.console = {
  ...console,
  log: jest.fn(),
  debug: jest.fn(),
  info: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};
