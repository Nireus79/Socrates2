/**
 * Logger Utility Unit Tests
 *
 * Tests for structured logging functionality
 */

import * as vscode from 'vscode';
import { Logger, LogLevel } from '../../src/utils/logger';

describe('Logger', () => {
  let logger: Logger;
  let mockOutputChannel: jest.Mocked<vscode.OutputChannel>;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();
    jest.setSystemTime(new Date('2025-01-01T12:00:00Z'));

    mockOutputChannel = {
      name: 'Test Channel',
      append: jest.fn(),
      appendLine: jest.fn(),
      clear: jest.fn(),
      show: jest.fn(),
      hide: jest.fn(),
      dispose: jest.fn(),
    } as any;

    (vscode.window.createOutputChannel as jest.Mock).mockReturnValue(
      mockOutputChannel
    );

    logger = new Logger('TestLogger');
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Initialization', () => {
    it('should create output channel with logger name', () => {
      expect(vscode.window.createOutputChannel).toHaveBeenCalledWith(
        'Socrates2 - TestLogger'
      );
    });

    it('should set default log level to INFO', () => {
      expect((logger as any).logLevel).toBe(LogLevel.INFO);
    });
  });

  describe('Log Levels', () => {
    it('should have correct log level values', () => {
      expect(LogLevel.DEBUG).toBe(0);
      expect(LogLevel.INFO).toBe(1);
      expect(LogLevel.WARNING).toBe(2);
      expect(LogLevel.ERROR).toBe(3);
    });

    it('should set log level', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      expect((logger as any).logLevel).toBe(LogLevel.DEBUG);

      logger.setLogLevel(LogLevel.ERROR);
      expect((logger as any).logLevel).toBe(LogLevel.ERROR);
    });
  });

  describe('Debug Logging', () => {
    it('should log debug message when level allows', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      logger.debug('Debug message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('DEBUG')
      );
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('Debug message')
      );
    });

    it('should include timestamp in debug log', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      logger.debug('Test message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('2025-01-01T12:00:00')
      );
    });

    it('should log additional data with debug', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      logger.debug('Debug with data', { key: 'value' });

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('key')
      );
    });

    it('should not log debug when level is higher', () => {
      logger.setLogLevel(LogLevel.INFO);
      mockOutputChannel.appendLine.mockClear();

      logger.debug('This should not appear');

      expect(mockOutputChannel.appendLine).not.toHaveBeenCalled();
    });
  });

  describe('Info Logging', () => {
    it('should log info message', () => {
      logger.setLogLevel(LogLevel.INFO);
      logger.info('Info message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('INFO')
      );
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('Info message')
      );
    });

    it('should log additional data with info', () => {
      logger.setLogLevel(LogLevel.INFO);
      logger.info('Info with data', { status: 'active' });

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('status')
      );
    });

    it('should not log info when level is higher', () => {
      logger.setLogLevel(LogLevel.WARNING);
      mockOutputChannel.appendLine.mockClear();

      logger.info('This should not appear');

      expect(mockOutputChannel.appendLine).not.toHaveBeenCalled();
    });
  });

  describe('Warning Logging', () => {
    it('should log warning message', () => {
      logger.setLogLevel(LogLevel.WARNING);
      logger.warning('Warning message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('WARN')
      );
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('Warning message')
      );
    });

    it('should log additional data with warning', () => {
      logger.setLogLevel(LogLevel.WARNING);
      logger.warning('Warning with context', { code: 'WARN_001' });

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('code')
      );
    });

    it('should not log warning when level is higher', () => {
      logger.setLogLevel(LogLevel.ERROR);
      mockOutputChannel.appendLine.mockClear();

      logger.warning('This should not appear');

      expect(mockOutputChannel.appendLine).not.toHaveBeenCalled();
    });
  });

  describe('Error Logging', () => {
    it('should log error message', () => {
      logger.setLogLevel(LogLevel.ERROR);
      logger.error('Error message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('ERROR')
      );
      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('Error message')
      );
    });

    it('should log Error object with stack trace', () => {
      logger.setLogLevel(LogLevel.ERROR);
      const error = new Error('Test error');

      logger.error('An error occurred', error);

      const calls = mockOutputChannel.appendLine.mock.calls;
      const errorLog = calls.map((c) => c[0]).join('\n');

      expect(errorLog).toContain('Test error');
      expect(errorLog).toContain('stack');
    });

    it('should serialize non-Error objects', () => {
      logger.setLogLevel(LogLevel.ERROR);
      const errorData = { status: 500, message: 'Server error' };

      logger.error('Error occurred', errorData);

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('status')
      );
    });

    it('should handle errors at any log level', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      mockOutputChannel.appendLine.mockClear();

      logger.error('Error message');

      expect(mockOutputChannel.appendLine).toHaveBeenCalled();
    });
  });

  describe('Logger Name', () => {
    it('should include logger name in output', () => {
      logger.setLogLevel(LogLevel.INFO);
      logger.info('Test');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('TestLogger')
      );
    });

    it('should create distinct loggers for different names', () => {
      const logger1 = new Logger('Logger1');
      const logger2 = new Logger('Logger2');

      expect(vscode.window.createOutputChannel).toHaveBeenCalledWith(
        'Socrates2 - Logger1'
      );
      expect(vscode.window.createOutputChannel).toHaveBeenCalledWith(
        'Socrates2 - Logger2'
      );
    });
  });

  describe('Output Channel Management', () => {
    it('should show output channel', () => {
      logger.show();

      expect(mockOutputChannel.show).toHaveBeenCalled();
    });

    it('should clear output channel', () => {
      logger.clear();

      expect(mockOutputChannel.clear).toHaveBeenCalled();
    });

    it('should dispose output channel', () => {
      logger.dispose();

      expect(mockOutputChannel.dispose).toHaveBeenCalled();
    });
  });

  describe('Message Formatting', () => {
    it('should format messages with timestamp', () => {
      logger.setLogLevel(LogLevel.INFO);
      logger.info('Formatted message');

      const calls = (mockOutputChannel.appendLine as jest.Mock).mock.calls;
      const message = calls[0][0];

      expect(message).toMatch(/\[2025-01-01T12:00:00\]/);
      expect(message).toMatch(/\[INFO\]/);
      expect(message).toMatch(/\[TestLogger\]/);
    });

    it('should handle long messages', () => {
      logger.setLogLevel(LogLevel.INFO);
      const longMessage = 'a'.repeat(1000);

      logger.info(longMessage);

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('a'.repeat(100))
      );
    });

    it('should handle special characters', () => {
      logger.setLogLevel(LogLevel.INFO);
      logger.info('Message with special chars: @#$%^&*()');

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('@#$%^&*()')
      );
    });

    it('should handle newlines in messages', () => {
      logger.setLogLevel(LogLevel.INFO);
      const multilineMessage = 'Line 1\nLine 2\nLine 3';

      logger.info(multilineMessage);

      expect(mockOutputChannel.appendLine).toHaveBeenCalled();
    });
  });

  describe('Data Serialization', () => {
    it('should serialize objects as JSON', () => {
      logger.setLogLevel(LogLevel.INFO);
      const obj = { name: 'test', count: 42 };

      logger.info('Object log', obj);

      expect(mockOutputChannel.appendLine).toHaveBeenCalledWith(
        expect.stringContaining('name')
      );
    });

    it('should handle undefined data', () => {
      logger.setLogLevel(LogLevel.INFO);

      logger.info('Message without data');

      expect(mockOutputChannel.appendLine).toHaveBeenCalled();
    });

    it('should handle null data', () => {
      logger.setLogLevel(LogLevel.INFO);

      logger.info('Message with null', null);

      expect(mockOutputChannel.appendLine).toHaveBeenCalled();
    });

    it('should handle circular references gracefully', () => {
      logger.setLogLevel(LogLevel.INFO);
      const obj: any = { a: 1 };
      obj.self = obj;

      logger.info('Circular object', obj);

      expect(mockOutputChannel.appendLine).toHaveBeenCalled();
    });
  });

  describe('Console Output in Debug Mode', () => {
    it('should log to console when in DEBUG level', () => {
      logger.setLogLevel(LogLevel.DEBUG);
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      logger.debug('Debug console message');

      expect(consoleSpy).toHaveBeenCalled();

      consoleSpy.mockRestore();
    });

    it('should not log to console in other levels', () => {
      logger.setLogLevel(LogLevel.INFO);
      const consoleSpy = jest.spyOn(console, 'log').mockImplementation();

      logger.info('Info message');

      expect(consoleSpy).not.toHaveBeenCalled();

      consoleSpy.mockRestore();
    });
  });

  describe('Performance', () => {
    it('should handle high volume logging', () => {
      logger.setLogLevel(LogLevel.DEBUG);

      for (let i = 0; i < 1000; i++) {
        logger.info(`Message ${i}`);
      }

      expect(mockOutputChannel.appendLine).toHaveBeenCalledTimes(1000);
    });

    it('should skip logging when level does not allow', () => {
      logger.setLogLevel(LogLevel.ERROR);

      for (let i = 0; i < 100; i++) {
        logger.debug(`Debug ${i}`);
      }

      expect(mockOutputChannel.appendLine).not.toHaveBeenCalled();
    });
  });
});
