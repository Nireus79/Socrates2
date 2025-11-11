/**
 * Logger Utility for Socrates2 VS Code Extension
 *
 * Provides structured logging with levels
 */

import * as vscode from 'vscode';

export enum LogLevel {
  DEBUG = 0,
  INFO = 1,
  WARNING = 2,
  ERROR = 3,
}

export class Logger {
  private name: string;
  private outputChannel: vscode.OutputChannel;
  private logLevel: LogLevel = LogLevel.INFO;

  constructor(name: string) {
    this.name = name;
    this.outputChannel = vscode.window.createOutputChannel(
      `Socrates2 - ${name}`
    );
  }

  /**
   * Set log level
   */
  setLogLevel(level: LogLevel): void {
    this.logLevel = level;
  }

  /**
   * Log debug message
   */
  debug(message: string, data?: any): void {
    if (this.logLevel <= LogLevel.DEBUG) {
      this.log('DEBUG', message, data);
    }
  }

  /**
   * Log info message
   */
  info(message: string, data?: any): void {
    if (this.logLevel <= LogLevel.INFO) {
      this.log('INFO', message, data);
    }
  }

  /**
   * Log warning message
   */
  warning(message: string, data?: any): void {
    if (this.logLevel <= LogLevel.WARNING) {
      this.log('WARN', message, data);
    }
  }

  /**
   * Log error message
   */
  error(message: string, error?: any): void {
    if (this.logLevel <= LogLevel.ERROR) {
      let fullMessage = message;
      if (error instanceof Error) {
        fullMessage = `${message}: ${error.message}`;
        if (error.stack) {
          fullMessage += `\n${error.stack}`;
        }
      } else if (error) {
        fullMessage = `${message}: ${JSON.stringify(error)}`;
      }
      this.log('ERROR', fullMessage);
    }
  }

  /**
   * Internal log method
   */
  private log(level: string, message: string, data?: any): void {
    const timestamp = new Date().toISOString();
    const prefix = `[${timestamp}] [${level}] [${this.name}]`;

    const logMessage = data
      ? `${prefix} ${message} ${JSON.stringify(data)}`
      : `${prefix} ${message}`;

    this.outputChannel.appendLine(logMessage);

    // Also log to console in debug mode
    if (this.logLevel === LogLevel.DEBUG) {
      console.log(logMessage);
    }
  }

  /**
   * Show output channel
   */
  show(): void {
    this.outputChannel.show();
  }

  /**
   * Clear output
   */
  clear(): void {
    this.outputChannel.clear();
  }

  /**
   * Dispose logger
   */
  dispose(): void {
    this.outputChannel.dispose();
  }
}
