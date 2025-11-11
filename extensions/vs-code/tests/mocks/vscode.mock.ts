/**
 * VS Code API Mock Utilities
 *
 * Helper functions for mocking VS Code API in tests
 */

import * as vscode from 'vscode';

export const createMockExtensionContext = (): Partial<vscode.ExtensionContext> => ({
  extensionUri: { fsPath: '/test/extension', path: '/test/extension', scheme: 'file' } as any,
  extensionPath: '/test/extension',
  storagePath: '/test/storage',
  globalStoragePath: '/test/global-storage',
  logPath: '/test/logs',
  secrets: {
    get: jest.fn(),
    store: jest.fn(),
    delete: jest.fn(),
    onDidChange: jest.fn(() => ({ dispose: () => {} })),
  } as any,
  globalState: {
    get: jest.fn(),
    update: jest.fn(),
    keys: jest.fn(() => []),
    setKeysForSync: jest.fn(),
  } as any,
  workspaceState: {
    get: jest.fn(),
    update: jest.fn(),
    keys: jest.fn(() => []),
    setKeysForSync: jest.fn(),
  } as any,
  subscriptions: [],
});

export const createMockOutputChannel = (): vscode.OutputChannel => ({
  name: 'Test Channel',
  append: jest.fn(),
  appendLine: jest.fn(),
  clear: jest.fn(),
  show: jest.fn(),
  hide: jest.fn(),
  dispose: jest.fn(),
  replace: jest.fn(),
});

export const createMockTreeItem = (
  label: string,
  collapsibleState: vscode.TreeItemCollapsibleState = vscode.TreeItemCollapsibleState.None
): vscode.TreeItem => ({
  label,
  collapsibleState,
  description: undefined,
  iconPath: undefined,
  tooltip: undefined,
  command: undefined,
  contextValue: undefined,
});

export const createMockPosition = (line: number, character: number): vscode.Position => ({
  line,
  character,
  isBefore: jest.fn(),
  isBeforeOrEqual: jest.fn(),
  isAfter: jest.fn(),
  isAfterOrEqual: jest.fn(),
  isEqual: jest.fn(),
  compareTo: jest.fn(),
  translate: jest.fn(),
  with: jest.fn(),
});

export const createMockRange = (
  startLine: number,
  startChar: number,
  endLine: number,
  endChar: number
): vscode.Range => ({
  start: createMockPosition(startLine, startChar),
  end: createMockPosition(endLine, endChar),
  isEmpty: false,
  isSingleLine: startLine === endLine,
  contains: jest.fn(),
  intersection: jest.fn(),
  union: jest.fn(),
  with: jest.fn(),
  isEqual: jest.fn(),
});

export const createMockTextDocument = (
  uri: vscode.Uri = vscode.Uri.file('/test/file.ts'),
  content: string = 'test content'
): Partial<vscode.TextDocument> => ({
  uri,
  isUntitled: false,
  languageId: 'typescript',
  version: 1,
  isDirty: false,
  isClosed: false,
  getText: jest.fn(() => content),
  getWordRangeAtPosition: jest.fn(),
  lineAt: jest.fn((line: number) => ({
    lineNumber: line,
    text: content.split('\n')[line] || '',
    range: createMockRange(line, 0, line, 100),
    rangeIncludingLineBreak: createMockRange(line, 0, line, 100),
    firstNonWhitespaceCharacterIndex: 0,
    isEmptyOrWhitespace: false,
  })),
  lineCount: content.split('\n').length,
  save: jest.fn(),
  validateRange: jest.fn(),
  validatePosition: jest.fn(),
  offsetAt: jest.fn(),
  positionAt: jest.fn(),
});

export const createMockHover = (
  contents: Array<vscode.MarkedString | vscode.MarkdownString>
): vscode.Hover => ({
  contents,
  range: undefined,
});

export const createMockDiagnostic = (
  range: vscode.Range,
  message: string,
  severity: vscode.DiagnosticSeverity = vscode.DiagnosticSeverity.Error
): vscode.Diagnostic => ({
  range,
  message,
  severity,
  code: undefined,
  source: 'Socrates2',
  relatedInformation: undefined,
  tags: undefined,
});
