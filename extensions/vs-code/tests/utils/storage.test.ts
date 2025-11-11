/**
 * Storage Service Unit Tests
 *
 * Tests for VS Code secret storage management
 */

import * as vscode from 'vscode';
import { StorageService } from '../../src/utils/storage';
import { mockUser } from '../mocks/api.mock';

describe('StorageService', () => {
  let storage: StorageService;
  let mockSecrets: jest.Mocked<vscode.SecretStorage>;
  let mockGlobalState: jest.Mocked<vscode.Memento>;
  let mockContext: Partial<vscode.ExtensionContext>;

  beforeEach(() => {
    jest.clearAllMocks();

    mockSecrets = {
      get: jest.fn(),
      store: jest.fn(),
      delete: jest.fn(),
      onDidChange: jest.fn(() => ({ dispose: () => {} })),
    } as any;

    mockGlobalState = {
      get: jest.fn(),
      update: jest.fn(),
      keys: jest.fn(() => []),
    } as any;

    mockContext = {
      secrets: mockSecrets,
      globalState: mockGlobalState,
    };

    storage = new StorageService(mockContext as vscode.ExtensionContext);
  });

  describe('Token Management', () => {
    it('should get token from secret storage', async () => {
      const token = 'test-token-123';
      (mockSecrets.get as jest.Mock).mockResolvedValue(token);

      const result = await storage.getToken();

      expect(result).toBe(token);
      expect(mockSecrets.get).toHaveBeenCalledWith('socrates.token');
    });

    it('should return undefined if token not found', async () => {
      (mockSecrets.get as jest.Mock).mockResolvedValue(undefined);

      const result = await storage.getToken();

      expect(result).toBeUndefined();
    });

    it('should store token securely', async () => {
      const token = 'new-token-456';

      await storage.setToken(token);

      expect(mockSecrets.store).toHaveBeenCalledWith('socrates.token', token);
    });

    it('should delete token from storage', async () => {
      await storage.clearToken();

      expect(mockSecrets.delete).toHaveBeenCalledWith('socrates.token');
    });
  });

  describe('User Information', () => {
    it('should get user from global state', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(mockUser);

      const result = storage.getUser();

      expect(result).toEqual(mockUser);
      expect(mockGlobalState.get).toHaveBeenCalledWith('socrates.user');
    });

    it('should return undefined if user not found', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(undefined);

      const result = storage.getUser();

      expect(result).toBeUndefined();
    });

    it('should store user in global state', async () => {
      await storage.setUser(mockUser);

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.user',
        mockUser
      );
    });

    it('should clear user from storage', async () => {
      await storage.clearUser();

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.user',
        undefined
      );
    });

    it('should parse JSON user data', () => {
      const userJson = JSON.stringify(mockUser);
      (mockGlobalState.get as jest.Mock).mockReturnValue(userJson);

      const result = storage.getUser();

      expect(result).toEqual(mockUser);
    });
  });

  describe('API URL Management', () => {
    it('should get API URL', () => {
      const url = 'http://localhost:8000';
      (mockGlobalState.get as jest.Mock).mockReturnValue(url);

      const result = storage.getApiUrl();

      expect(result).toBe(url);
      expect(mockGlobalState.get).toHaveBeenCalledWith('socrates.apiUrl');
    });

    it('should return default API URL if not set', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(undefined);

      const result = storage.getApiUrl();

      expect(result).toBe('http://localhost:8000');
    });

    it('should store API URL', async () => {
      const url = 'https://api.example.com';

      await storage.setApiUrl(url);

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.apiUrl',
        url
      );
    });
  });

  describe('Project Selection', () => {
    it('should get selected project', () => {
      const projectId = 'project-123';
      (mockGlobalState.get as jest.Mock).mockReturnValue(projectId);

      const result = storage.getSelectedProject();

      expect(result).toBe(projectId);
      expect(mockGlobalState.get).toHaveBeenCalledWith('socrates.selectedProject');
    });

    it('should return null if no project selected', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(null);

      const result = storage.getSelectedProject();

      expect(result).toBeNull();
    });

    it('should store selected project', async () => {
      const projectId = 'project-456';

      await storage.setSelectedProject(projectId);

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.selectedProject',
        projectId
      );
    });

    it('should clear selected project', async () => {
      await storage.clearSelectedProject();

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.selectedProject',
        null
      );
    });
  });

  describe('Workspace Values', () => {
    it('should store workspace value', async () => {
      const value = { key: 'value' };

      await storage.setWorkspaceValue('test.key', value);

      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'ws.test.key',
        value
      );
    });

    it('should get workspace value', () => {
      const value = { key: 'value' };
      (mockGlobalState.get as jest.Mock).mockReturnValue(value);

      const result = storage.getWorkspaceValue('test.key');

      expect(result).toEqual(value);
      expect(mockGlobalState.get).toHaveBeenCalledWith('ws.test.key');
    });

    it('should return default workspace value if not set', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(undefined);

      const result = storage.getWorkspaceValue('test.key', { default: 'value' });

      expect(result).toEqual({ default: 'value' });
    });
  });

  describe('Cache Management', () => {
    it('should clear all cached data', async () => {
      await storage.clearAll();

      expect(mockSecrets.delete).toHaveBeenCalledWith('socrates.token');
      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.user',
        undefined
      );
      expect(mockGlobalState.update).toHaveBeenCalledWith(
        'socrates.selectedProject',
        null
      );
    });

    it('should clear specific cache entries', async () => {
      await storage.clearToken();
      await storage.clearUser();
      await storage.clearSelectedProject();

      expect(mockSecrets.delete).toHaveBeenCalled();
      expect(mockGlobalState.update).toHaveBeenCalledTimes(2);
    });
  });

  describe('Data Persistence', () => {
    it('should persist and retrieve complex objects', async () => {
      const complexData = {
        user: mockUser,
        projects: ['p1', 'p2'],
        settings: { theme: 'dark' },
      };

      (mockGlobalState.get as jest.Mock).mockReturnValue(
        JSON.stringify(complexData)
      );

      const result = storage.getWorkspaceValue('complex');

      expect(typeof result).toBe('string');
    });

    it('should handle missing keys gracefully', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue(undefined);

      const result = storage.getUser();

      expect(result).toBeUndefined();
    });

    it('should overwrite existing values', async () => {
      const oldToken = 'old-token';
      const newToken = 'new-token';

      (mockSecrets.get as jest.Mock).mockResolvedValue(oldToken);

      await storage.setToken(newToken);

      expect(mockSecrets.store).toHaveBeenCalledWith('socrates.token', newToken);
    });
  });

  describe('Error Handling', () => {
    it('should handle storage errors gracefully', async () => {
      (mockSecrets.store as jest.Mock).mockRejectedValue(
        new Error('Storage unavailable')
      );

      await expect(storage.setToken('token')).rejects.toThrow();
    });

    it('should handle corrupted data', () => {
      (mockGlobalState.get as jest.Mock).mockReturnValue('invalid-json');

      const result = storage.getUser();

      expect(result).toBe('invalid-json');
    });
  });

  describe('Synchronization', () => {
    it('should trigger on secret change', () => {
      const onDidChange = jest.fn();
      (mockSecrets.onDidChange as jest.Mock).mockReturnValue({
        dispose: jest.fn(),
      });

      // The constructor should have registered the event
      expect(mockSecrets.onDidChange).toHaveBeenCalled();
    });
  });
});
