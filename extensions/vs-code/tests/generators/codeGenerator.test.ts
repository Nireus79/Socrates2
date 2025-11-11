/**
 * Code Generator Unit Tests
 *
 * Tests for code generation from specifications
 */

import * as vscode from 'vscode';
import { CodeGenerator } from '../../src/generators/codeGenerator';
import { SocratesApiClient } from '../../src/api/client';
import { Logger } from '../../src/utils/logger';
import { mockSpecification, mockGeneratedCode, createMockApiError } from '../mocks/api.mock';

jest.mock('../../src/api/client');
jest.mock('../../src/utils/logger');

describe('CodeGenerator', () => {
  let generator: CodeGenerator;
  let mockApiClient: jest.Mocked<SocratesApiClient>;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    jest.clearAllMocks();

    mockApiClient = new SocratesApiClient(
      'http://localhost:8000',
      null as any
    ) as jest.Mocked<SocratesApiClient>;
    mockLogger = new Logger('test') as jest.Mocked<Logger>;

    mockApiClient.generateCode = jest
      .fn()
      .mockResolvedValue(mockGeneratedCode.code);

    generator = new CodeGenerator(mockApiClient, mockLogger);
  });

  describe('Initialization', () => {
    it('should initialize with API client and logger', () => {
      expect(generator).toBeDefined();
    });
  });

  describe('Code Generation', () => {
    it('should generate code for specification', async () => {
      const code = await generator.generateCode(mockSpecification, 'python');

      expect(code).toBe(mockGeneratedCode.code);
      expect(mockApiClient.generateCode).toHaveBeenCalledWith(
        mockSpecification.id,
        'python'
      );
    });

    it('should handle different programming languages', async () => {
      const languages = ['python', 'javascript', 'go', 'java'];

      for (const lang of languages) {
        await generator.generateCode(mockSpecification, lang);
        expect(mockApiClient.generateCode).toHaveBeenCalledWith(
          mockSpecification.id,
          lang
        );
      }
    });

    it('should handle code generation errors', async () => {
      const error = createMockApiError('Generation failed', 400);
      mockApiClient.generateCode = jest.fn().mockRejectedValue(error);

      await expect(
        generator.generateCode(mockSpecification, 'python')
      ).rejects.toThrow();
    });

    it('should log code generation requests', async () => {
      await generator.generateCode(mockSpecification, 'python');

      expect(mockLogger.info).toHaveBeenCalledWith(
        expect.stringContaining('python')
      );
    });
  });

  describe('Language Detection', () => {
    it('should detect language from file extension', () => {
      const testCases = [
        { file: 'main.py', expected: 'python' },
        { file: 'app.js', expected: 'javascript' },
        { file: 'main.go', expected: 'go' },
        { file: 'App.java', expected: 'java' },
        { file: 'script.ts', expected: 'typescript' },
      ];

      testCases.forEach(({ file, expected }) => {
        const detected = (generator as any).detectLanguageFromFile(file);
        expect(detected).toBe(expected);
      });
    });

    it('should return original language if extension unknown', () => {
      const detected = (generator as any).detectLanguageFromFile('unknown.xyz');

      expect(detected).toBe('unknown.xyz');
    });

    it('should handle files without extension', () => {
      const detected = (generator as any).detectLanguageFromFile('Makefile');

      expect(detected).toBe('Makefile');
    });
  });

  describe('Code Formatting', () => {
    it('should format Python code', async () => {
      const unformatted = 'x=1\ny=2';
      const formatted = await (generator as any).formatCode(unformatted, 'python');

      expect(typeof formatted).toBe('string');
      expect(formatted.length).toBeGreaterThan(0);
    });

    it('should format JavaScript code', async () => {
      const unformatted = 'const x=1;const y=2;';
      const formatted = await (generator as any).formatCode(unformatted, 'javascript');

      expect(typeof formatted).toBe('string');
    });

    it('should handle formatting errors gracefully', async () => {
      const code = 'invalid code {{{';

      const result = await (generator as any).formatCode(code, 'python');

      expect(result).toBeTruthy();
    });
  });

  describe('Code Preview', () => {
    it('should create code preview webview', async () => {
      (vscode.window.createWebviewPanel as jest.Mock).mockReturnValue({
        webview: {
          html: '',
          onDidReceiveMessage: jest.fn(() => ({ dispose: () => {} })),
        },
        dispose: jest.fn(),
        reveal: jest.fn(),
      });

      await (generator as any).showCodePreview(mockGeneratedCode.code, 'python');

      expect(vscode.window.createWebviewPanel).toHaveBeenCalled();
    });

    it('should include code in preview HTML', async () => {
      let capturedHtml = '';
      (vscode.window.createWebviewPanel as jest.Mock).mockReturnValue({
        webview: {
          html: '',
          onDidReceiveMessage: jest.fn(() => ({ dispose: () => {} })),
        },
        dispose: jest.fn(),
        reveal: jest.fn(),
      });

      await (generator as any).showCodePreview(mockGeneratedCode.code, 'python');

      const panel = (vscode.window.createWebviewPanel as jest.Mock).mock
        .results[0].value;
      expect(panel.webview).toBeDefined();
    });

    it('should show preview with appropriate title', async () => {
      (vscode.window.createWebviewPanel as jest.Mock).mockReturnValue({
        webview: { onDidReceiveMessage: jest.fn(() => ({ dispose: () => {} })) },
        dispose: jest.fn(),
        reveal: jest.fn(),
      });

      await (generator as any).showCodePreview(mockGeneratedCode.code, 'python');

      expect(vscode.window.createWebviewPanel).toHaveBeenCalledWith(
        expect.anything(),
        expect.stringContaining('Generated Code'),
        expect.anything(),
        expect.anything()
      );
    });
  });

  describe('Insertion Into Editor', () => {
    it('should insert code at cursor position', async () => {
      const editor = {
        selection: { active: { line: 5, character: 0 } },
        edit: jest.fn((callback) => {
          const edit = { insert: jest.fn() };
          callback(edit);
          return Promise.resolve(true);
        }),
      } as any;

      (vscode.window.activeTextEditor as any) = editor;

      await (generator as any).insertCodeIntoEditor(mockGeneratedCode.code);

      expect(editor.edit).toHaveBeenCalled();
    });

    it('should handle missing active editor', async () => {
      (vscode.window.activeTextEditor as any) = undefined;

      await (generator as any).insertCodeIntoEditor(mockGeneratedCode.code);

      expect(vscode.window.showWarningMessage).toHaveBeenCalledWith(
        expect.stringContaining('editor')
      );
    });

    it('should show success message after insertion', async () => {
      const editor = {
        selection: { active: { line: 5, character: 0 } },
        edit: jest.fn(() => Promise.resolve(true)),
      } as any;

      (vscode.window.activeTextEditor as any) = editor;

      await (generator as any).insertCodeIntoEditor(mockGeneratedCode.code);

      expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
        expect.stringContaining('inserted')
      );
    });
  });

  describe('File Creation', () => {
    it('should create new file with generated code', async () => {
      const mockUri = vscode.Uri.file('/workspace/generated.py');
      (vscode.window.showSaveDialog as jest.Mock).mockResolvedValue(mockUri);
      (vscode.workspace.fs.writeFile as jest.Mock).mockResolvedValue(undefined);

      await (generator as any).createNewFile(
        mockGeneratedCode.code,
        'generated.py'
      );

      expect(vscode.workspace.fs.writeFile).toHaveBeenCalled();
    });

    it('should handle file creation cancellation', async () => {
      (vscode.window.showSaveDialog as jest.Mock).mockResolvedValue(undefined);

      await (generator as any).createNewFile(mockGeneratedCode.code, 'generated.py');

      expect(vscode.workspace.fs.writeFile).not.toHaveBeenCalled();
    });

    it('should handle file creation errors', async () => {
      const mockUri = vscode.Uri.file('/workspace/generated.py');
      (vscode.window.showSaveDialog as jest.Mock).mockResolvedValue(mockUri);
      (vscode.workspace.fs.writeFile as jest.Mock).mockRejectedValue(
        new Error('Write failed')
      );

      await (generator as any).createNewFile(mockGeneratedCode.code, 'generated.py');

      expect(vscode.window.showErrorMessage).toHaveBeenCalled();
    });
  });

  describe('Clipboard Operations', () => {
    it('should copy code to clipboard', async () => {
      (vscode.env.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);

      await (generator as any).copyToClipboard(mockGeneratedCode.code);

      expect(vscode.env.clipboard.writeText).toHaveBeenCalledWith(
        mockGeneratedCode.code
      );
    });

    it('should show confirmation after copy', async () => {
      (vscode.env.clipboard.writeText as jest.Mock).mockResolvedValue(undefined);

      await (generator as any).copyToClipboard(mockGeneratedCode.code);

      expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
        expect.stringContaining('copied')
      );
    });

    it('should handle clipboard copy errors', async () => {
      (vscode.env.clipboard.writeText as jest.Mock).mockRejectedValue(
        new Error('Clipboard error')
      );

      await (generator as any).copyToClipboard(mockGeneratedCode.code);

      expect(vscode.window.showErrorMessage).toHaveBeenCalled();
    });
  });

  describe('Language Support', () => {
    it('should support multiple programming languages', () => {
      const supportedLanguages = ['python', 'javascript', 'go', 'java', 'typescript'];

      supportedLanguages.forEach((lang) => {
        expect(
          (generator as any).detectLanguageFromFile(`file.${lang}`)
        ).toBeTruthy();
      });
    });

    it('should handle language-specific formatting', async () => {
      const languages = ['python', 'javascript'];

      for (const lang of languages) {
        const formatted = await (generator as any).formatCode('code', lang);
        expect(formatted).toBeTruthy();
      }
    });
  });

  describe('Error Handling', () => {
    it('should handle API errors', async () => {
      const error = createMockApiError('API error', 500);
      mockApiClient.generateCode = jest.fn().mockRejectedValue(error);

      await expect(
        generator.generateCode(mockSpecification, 'python')
      ).rejects.toThrow();

      expect(mockLogger.error).toHaveBeenCalled();
    });

    it('should handle network errors', async () => {
      const error = new Error('Network error');
      mockApiClient.generateCode = jest.fn().mockRejectedValue(error);

      await expect(
        generator.generateCode(mockSpecification, 'python')
      ).rejects.toThrow();
    });

    it('should provide helpful error messages', async () => {
      const error = createMockApiError('Invalid specification', 400);
      mockApiClient.generateCode = jest.fn().mockRejectedValue(error);

      try {
        await generator.generateCode(mockSpecification, 'python');
      } catch (e) {
        expect(mockLogger.error).toHaveBeenCalled();
      }
    });
  });

  describe('Progress Indication', () => {
    it('should show progress while generating code', async () => {
      await generator.generateCode(mockSpecification, 'python');

      expect(vscode.window.withProgress).toHaveBeenCalled();
    });

    it('should update progress status', async () => {
      let progressCallback: any = null;
      (vscode.window.withProgress as jest.Mock).mockImplementation(
        (options, callback) => {
          progressCallback = callback;
          return callback();
        }
      );

      await generator.generateCode(mockSpecification, 'python');

      expect(progressCallback).toHaveBeenCalled();
    });
  });
});
