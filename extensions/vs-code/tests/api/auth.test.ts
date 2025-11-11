/**
 * Authentication Service Unit Tests
 *
 * Tests for the Socrates2 authentication service
 */

import * as vscode from 'vscode';
import { AuthenticationService } from '../../src/api/auth';
import { StorageService } from '../../src/utils/storage';
import { SocratesApiClient } from '../../src/api/client';
import {
  mockUser,
  mockAuthResponse,
  createMockApiResponse,
  createMockApiError,
} from '../mocks/api.mock';

jest.mock('../../src/utils/storage');
jest.mock('../../src/api/client');

describe('AuthenticationService', () => {
  let authService: AuthenticationService;
  let mockStorage: jest.Mocked<StorageService>;
  let mockApiClient: jest.Mocked<SocratesApiClient>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockStorage = new StorageService(null as any) as jest.Mocked<StorageService>;
    mockApiClient = new SocratesApiClient(
      'http://localhost:8000',
      mockStorage
    ) as jest.Mocked<SocratesApiClient>;

    mockStorage.getToken = jest.fn().mockReturnValue(null);
    mockStorage.setToken = jest.fn();
    mockStorage.clearToken = jest.fn();
    mockStorage.getUser = jest.fn().mockReturnValue(null);
    mockStorage.setUser = jest.fn();
    mockStorage.clearUser = jest.fn();

    authService = new AuthenticationService(mockApiClient, mockStorage);
  });

  describe('Authentication Status', () => {
    it('should return false when no token is stored', () => {
      mockStorage.getToken = jest.fn().mockReturnValue(null);

      const isAuth = authService.isAuthenticated();

      expect(isAuth).toBe(false);
    });

    it('should return true when token is stored', () => {
      mockStorage.getToken = jest.fn().mockReturnValue('valid-token');

      const isAuth = authService.isAuthenticated();

      expect(isAuth).toBe(true);
    });
  });

  describe('User Login', () => {
    beforeEach(() => {
      (vscode.window.showInputBox as jest.Mock).mockClear();
      (vscode.window.showInformationMessage as jest.Mock).mockClear();
      (vscode.window.showErrorMessage as jest.Mock).mockClear();
    });

    it('should perform login with valid credentials', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('test@example.com')
        .mockResolvedValueOnce('password123');

      mockApiClient.login = jest.fn().mockResolvedValue(mockAuthResponse);

      const result = await authService.authenticate();

      expect(result).toBe(true);
      expect(mockStorage.setToken).toHaveBeenCalledWith(mockAuthResponse.access_token);
      expect(mockStorage.setUser).toHaveBeenCalledWith(mockAuthResponse.user);
      expect(vscode.window.showInformationMessage).toHaveBeenCalledWith(
        expect.stringContaining('successfully')
      );
    });

    it('should handle login cancellation', async () => {
      (vscode.window.showInputBox as jest.Mock).mockResolvedValueOnce(undefined);

      const result = await authService.authenticate();

      expect(result).toBe(false);
      expect(mockStorage.setToken).not.toHaveBeenCalled();
    });

    it('should handle invalid email format', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('invalid-email')
        .mockResolvedValueOnce('password123');

      const result = await authService.authenticate();

      expect(result).toBe(false);
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        expect.stringContaining('email')
      );
    });

    it('should handle weak password', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('test@example.com')
        .mockResolvedValueOnce('weak');

      const result = await authService.authenticate();

      expect(result).toBe(false);
      expect(vscode.window.showErrorMessage).toHaveBeenCalled();
    });

    it('should handle API errors during login', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('test@example.com')
        .mockResolvedValueOnce('password123');

      const error = createMockApiError('Invalid credentials', 401);
      mockApiClient.login = jest.fn().mockRejectedValue(error);

      const result = await authService.authenticate();

      expect(result).toBe(false);
      expect(vscode.window.showErrorMessage).toHaveBeenCalledWith(
        expect.stringContaining('sign in')
      );
    });

    it('should handle network errors', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('test@example.com')
        .mockResolvedValueOnce('password123');

      const error = new Error('Network error');
      mockApiClient.login = jest.fn().mockRejectedValue(error);

      const result = await authService.authenticate();

      expect(result).toBe(false);
      expect(vscode.window.showErrorMessage).toHaveBeenCalled();
    });
  });

  describe('Logout', () => {
    it('should logout and clear credentials', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('valid-token');
      mockApiClient.logout = jest.fn().mockResolvedValue({});

      await authService.logout();

      expect(mockStorage.clearToken).toHaveBeenCalled();
      expect(mockStorage.clearUser).toHaveBeenCalled();
      expect(mockApiClient.logout).toHaveBeenCalled();
    });

    it('should handle logout when not authenticated', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue(null);

      await authService.logout();

      expect(mockStorage.clearToken).toHaveBeenCalled();
      expect(mockStorage.clearUser).toHaveBeenCalled();
    });

    it('should handle logout errors', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('valid-token');
      const error = new Error('Logout failed');
      mockApiClient.logout = jest.fn().mockRejectedValue(error);

      await authService.logout();

      expect(mockStorage.clearToken).toHaveBeenCalled();
    });
  });

  describe('Token Management', () => {
    it('should return stored token', () => {
      const token = 'test-token-123';
      mockStorage.getToken = jest.fn().mockReturnValue(token);

      const result = authService.getToken();

      expect(result).toBe(token);
    });

    it('should check if token is expired', () => {
      const expiredToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJleHAiOjE2MDAwMDAwMDB9.xxx';
      mockStorage.getToken = jest.fn().mockReturnValue(expiredToken);

      const isExpired = authService.isTokenExpired();

      expect(isExpired).toBe(true);
    });

    it('should refresh token if expired', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('old-token');
      mockApiClient.refreshToken = jest.fn().mockResolvedValue({
        access_token: 'new-token',
        refresh_token: 'new-refresh-token',
      });

      await authService.refreshAccessToken();

      expect(mockStorage.setToken).toHaveBeenCalledWith('new-token');
    });

    it('should handle token refresh errors', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('old-token');
      const error = createMockApiError('Token refresh failed', 401);
      mockApiClient.refreshToken = jest.fn().mockRejectedValue(error);

      await authService.refreshAccessToken();

      expect(mockStorage.clearToken).toHaveBeenCalled();
    });
  });

  describe('User Information', () => {
    it('should get stored user', () => {
      mockStorage.getUser = jest.fn().mockReturnValue(mockUser);

      const user = authService.getStoredUser();

      expect(user).toEqual(mockUser);
    });

    it('should return null when user not stored', () => {
      mockStorage.getUser = jest.fn().mockReturnValue(null);

      const user = authService.getStoredUser();

      expect(user).toBeNull();
    });

    it('should get current user from API', async () => {
      mockApiClient.getCurrentUser = jest
        .fn()
        .mockResolvedValue(mockUser);

      const user = await authService.getCurrentUser();

      expect(user).toEqual(mockUser);
      expect(mockStorage.setUser).toHaveBeenCalledWith(mockUser);
    });

    it('should handle get current user errors', async () => {
      const error = createMockApiError('Unauthorized', 401);
      mockApiClient.getCurrentUser = jest.fn().mockRejectedValue(error);

      await expect(authService.getCurrentUser()).rejects.toThrow();
    });
  });

  describe('Email Validation', () => {
    it('should validate correct email format', () => {
      const isValid = (authService as any).isValidEmail('test@example.com');
      expect(isValid).toBe(true);
    });

    it('should reject invalid email format', () => {
      const testEmails = [
        'notanemail',
        'test@',
        '@example.com',
        'test @example.com',
        '',
      ];

      testEmails.forEach((email) => {
        const isValid = (authService as any).isValidEmail(email);
        expect(isValid).toBe(false);
      });
    });
  });

  describe('Password Validation', () => {
    it('should validate strong passwords', () => {
      const strongPasswords = [
        'MyPassword123!',
        'SecurePass456@',
        'LongPassword789#WithSymbols',
      ];

      strongPasswords.forEach((password) => {
        const isValid = (authService as any).isValidPassword(password);
        expect(isValid).toBe(true);
      });
    });

    it('should reject weak passwords', () => {
      const weakPasswords = [
        'short',
        '12345678', // only numbers
        'abcdefgh', // only letters
        'abc123', // too short
      ];

      weakPasswords.forEach((password) => {
        const isValid = (authService as any).isValidPassword(password);
        expect(isValid).toBe(false);
      });
    });
  });

  describe('Auto-Login', () => {
    it('should auto-login if valid token exists', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('valid-token');
      mockApiClient.getCurrentUser = jest
        .fn()
        .mockResolvedValue(mockUser);

      const result = await authService.autoLogin();

      expect(result).toBe(true);
      expect(mockApiClient.getCurrentUser).toHaveBeenCalled();
    });

    it('should fail auto-login if no token', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue(null);

      const result = await authService.autoLogin();

      expect(result).toBe(false);
      expect(mockApiClient.getCurrentUser).not.toHaveBeenCalled();
    });

    it('should clear credentials on auto-login failure', async () => {
      mockStorage.getToken = jest.fn().mockReturnValue('invalid-token');
      const error = createMockApiError('Token invalid', 401);
      mockApiClient.getCurrentUser = jest.fn().mockRejectedValue(error);

      await authService.autoLogin();

      expect(mockStorage.clearToken).toHaveBeenCalled();
      expect(mockStorage.clearUser).toHaveBeenCalled();
    });
  });
});
