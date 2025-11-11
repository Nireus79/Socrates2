/**
 * Test Helper Utilities
 *
 * Utility functions and helpers for testing
 */

import * as vscode from 'vscode';

/**
 * Create a mock text editor
 */
export const createMockTextEditor = (
  content: string = ''
): Partial<vscode.TextEditor> => ({
  document: {
    uri: vscode.Uri.file('/test/file.ts'),
    isUntitled: false,
    languageId: 'typescript',
    version: 1,
    isDirty: false,
    isClosed: false,
    getText: jest.fn(() => content),
    getWordRangeAtPosition: jest.fn(),
    lineAt: jest.fn(),
    lineCount: content.split('\n').length,
    save: jest.fn(),
    validateRange: jest.fn(),
    validatePosition: jest.fn(),
    offsetAt: jest.fn(),
    positionAt: jest.fn(),
  } as any,
  selection: {
    active: { line: 0, character: 0 },
    anchor: { line: 0, character: 0 },
    start: { line: 0, character: 0 },
    end: { line: 0, character: 0 },
    isActive: false,
    isEmpty: true,
    isSingleLine: true,
    contains: jest.fn(),
    intersection: jest.fn(),
    union: jest.fn(),
    with: jest.fn(),
    isEqual: jest.fn(),
  } as any,
  edit: jest.fn(() => Promise.resolve(true)),
  insertSnippet: jest.fn(() => Promise.resolve(true)),
  setDecorations: jest.fn(),
  revealRange: jest.fn(),
  show: jest.fn(),
  hide: jest.fn(),
});

/**
 * Create a mock workspace folder
 */
export const createMockWorkspaceFolder = (
  name: string = 'test-workspace',
  uri: vscode.Uri = vscode.Uri.file('/workspace')
): vscode.WorkspaceFolder => ({
  uri,
  name,
  index: 0,
});

/**
 * Create a mock status bar item
 */
export const createMockStatusBarItem = (): Partial<vscode.StatusBarItem> => ({
  alignment: vscode.StatusBarAlignment.Left,
  priority: 100,
  text: '',
  tooltip: undefined,
  color: undefined,
  backgroundColor: undefined,
  command: undefined,
  accessibilityInformation: undefined,
  show: jest.fn(),
  hide: jest.fn(),
  dispose: jest.fn(),
});

/**
 * Create a mock progress
 */
export const createMockProgress = () => ({
  report: jest.fn((value: { message?: string; increment?: number }) => {
    // Mock progress report
  }),
});

/**
 * Create a mock cancellation token
 */
export const createMockCancellationToken = (): Partial<vscode.CancellationToken> => ({
  isCancellationRequested: false,
  onCancellationRequested: jest.fn(() => ({ dispose: () => {} })),
});

/**
 * Wait for condition to be true
 */
export const waitFor = async (
  condition: () => boolean,
  timeout: number = 5000,
  checkInterval: number = 50
): Promise<void> => {
  const startTime = Date.now();
  while (!condition()) {
    if (Date.now() - startTime > timeout) {
      throw new Error('Timeout waiting for condition');
    }
    await new Promise((resolve) => setTimeout(resolve, checkInterval));
  }
};

/**
 * Delay execution
 */
export const delay = (ms: number): Promise<void> =>
  new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Create a mock command registration tracker
 */
export const createCommandTracker = () => {
  const registeredCommands: string[] = [];
  const handlers: Map<string, (...args: any[]) => any> = new Map();

  return {
    registerCommand: (command: string, handler: (...args: any[]) => any) => {
      registeredCommands.push(command);
      handlers.set(command, handler);
      return { dispose: () => {} };
    },
    executeCommand: (command: string, ...args: any[]) => {
      const handler = handlers.get(command);
      if (!handler) {
        throw new Error(`Command not found: ${command}`);
      }
      return handler(...args);
    },
    getRegisteredCommands: () => registeredCommands,
    isCommandRegistered: (command: string) => registeredCommands.includes(command),
  };
};

/**
 * Create a mock event emitter
 */
export const createMockEventEmitter = <T>() => {
  const listeners: Array<(event: T) => void> = [];

  return {
    event: (listener: (event: T) => void) => {
      listeners.push(listener);
      return { dispose: () => {} };
    },
    fire: (event: T) => {
      listeners.forEach((listener) => listener(event));
    },
    getListeners: () => listeners,
  };
};

/**
 * Assert that a function was called with specific arguments
 */
export const assertCalledWith = (
  mockFn: jest.Mock,
  expectedArgs: any[],
  callIndex: number = 0
): void => {
  const actualCall = mockFn.mock.calls[callIndex];
  if (!actualCall) {
    throw new Error(`Mock function was not called at index ${callIndex}`);
  }
  expect(actualCall).toEqual(expectedArgs);
};

/**
 * Create a test timeout
 */
export const createTimeout = (ms: number): Promise<void> =>
  new Promise((_, reject) =>
    setTimeout(() => reject(new Error(`Timeout after ${ms}ms`)), ms)
  );

/**
 * Assert async function throws error
 */
export const assertThrowsAsync = async (
  fn: () => Promise<any>,
  errorMessage?: string
): Promise<Error> => {
  try {
    await fn();
    throw new Error('Expected async function to throw');
  } catch (error) {
    if (errorMessage && !String(error).includes(errorMessage)) {
      throw new Error(
        `Expected error message to include "${errorMessage}" but got: ${error}`
      );
    }
    return error as Error;
  }
};

/**
 * Create a mock file system
 */
export const createMockFileSystem = () => {
  const files: Map<string, string> = new Map();

  return {
    writeFile: jest.fn((uri: vscode.Uri, content: Uint8Array) => {
      files.set(uri.fsPath, new TextDecoder().decode(content));
      return Promise.resolve(undefined);
    }),
    readFile: jest.fn((uri: vscode.Uri) => {
      const content = files.get(uri.fsPath);
      if (!content) {
        return Promise.reject(new Error('File not found'));
      }
      return Promise.resolve(new TextEncoder().encode(content));
    }),
    delete: jest.fn((uri: vscode.Uri) => {
      files.delete(uri.fsPath);
      return Promise.resolve(undefined);
    }),
    createDirectory: jest.fn(() => Promise.resolve(undefined)),
    getFiles: () => files,
  };
};

/**
 * Create test data builders
 */
export const testDataBuilder = {
  user: (overrides = {}) => ({
    id: 'test-user',
    email: 'test@example.com',
    name: 'Test User',
    role: 'user',
    created_at: new Date().toISOString(),
    ...overrides,
  }),

  project: (overrides = {}) => ({
    id: 'test-project',
    name: 'Test Project',
    description: 'Test project description',
    owner_id: 'test-user',
    status: 'active',
    maturity_score: 50,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  specification: (overrides = {}) => ({
    id: 'test-spec',
    project_id: 'test-project',
    key: 'test.spec',
    value: 'test value',
    category: 'Test',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    ...overrides,
  }),

  conflict: (overrides = {}) => ({
    id: 'test-conflict',
    project_id: 'test-project',
    specification_id: 'test-spec',
    type: 'test_conflict',
    severity: 'medium',
    message: 'Test conflict message',
    resolved: false,
    created_at: new Date().toISOString(),
    ...overrides,
  }),

  activity: (overrides = {}) => ({
    id: 'test-activity',
    project_id: 'test-project',
    user_id: 'test-user',
    action: 'test_action',
    description: 'Test activity',
    timestamp: new Date().toISOString(),
    ...overrides,
  }),
};

/**
 * Create a test suite context
 */
export const createTestContext = () => {
  const workspace = createMockWorkspaceFolder();
  const editor = createMockTextEditor();
  const progress = createMockProgress();
  const cancellationToken = createMockCancellationToken();
  const commandTracker = createCommandTracker();

  return {
    workspace,
    editor,
    progress,
    cancellationToken,
    commandTracker,
  };
};
