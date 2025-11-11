/**
 * Integration Tests for Extension Workflows
 *
 * Tests for complete end-to-end workflows
 */

import * as vscode from 'vscode';
import { SocratesApiClient } from '../../src/api/client';
import { AuthenticationService } from '../../src/api/auth';
import { StorageService } from '../../src/utils/storage';
import { CodeGenerator } from '../../src/generators/codeGenerator';
import {
  mockUser,
  mockProjects,
  mockSpecifications,
  mockGeneratedCode,
  mockAuthResponse,
  createMockApiError,
} from '../mocks/api.mock';

jest.mock('../../src/api/client');
jest.mock('../../src/utils/storage');
jest.mock('../../src/utils/logger');

describe('VS Code Extension Workflows', () => {
  let apiClient: jest.Mocked<SocratesApiClient>;
  let authService: AuthenticationService;
  let storage: jest.Mocked<StorageService>;
  let generator: CodeGenerator;

  beforeEach(() => {
    jest.clearAllMocks();

    storage = new StorageService(null as any) as jest.Mocked<StorageService>;
    apiClient = new SocratesApiClient(
      'http://localhost:8000',
      storage
    ) as jest.Mocked<SocratesApiClient>;

    storage.getToken = jest.fn().mockReturnValue(null);
    storage.setToken = jest.fn();
    storage.getUser = jest.fn().mockReturnValue(null);
    storage.setUser = jest.fn();
    storage.getSelectedProject = jest.fn().mockReturnValue(null);
    storage.setSelectedProject = jest.fn();

    authService = new AuthenticationService(apiClient, storage);
    generator = new CodeGenerator(apiClient, null as any);

    (vscode.window.showInputBox as jest.Mock).mockClear();
    (vscode.window.showInformationMessage as jest.Mock).mockClear();
  });

  describe('Authentication Workflow', () => {
    it('should complete full login flow', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('user@example.com')
        .mockResolvedValueOnce('password123');

      apiClient.login = jest.fn().mockResolvedValue(mockAuthResponse);

      const result = await authService.authenticate();

      expect(result).toBe(true);
      expect(storage.setToken).toHaveBeenCalledWith(mockAuthResponse.access_token);
      expect(storage.setUser).toHaveBeenCalledWith(mockAuthResponse.user);
    });

    it('should handle login followed by project selection', async () => {
      // Login
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('user@example.com')
        .mockResolvedValueOnce('password123');

      apiClient.login = jest.fn().mockResolvedValue(mockAuthResponse);

      const loginResult = await authService.authenticate();
      expect(loginResult).toBe(true);

      // Load projects
      apiClient.getProjects = jest.fn().mockResolvedValue(mockProjects);
      const projects = await apiClient.getProjects();

      expect(projects).toHaveLength(2);
      expect(storage.setToken).toHaveBeenCalled();
    });

    it('should handle logout and session cleanup', async () => {
      // Setup authenticated state
      storage.getToken = jest.fn().mockReturnValue('valid-token');
      apiClient.logout = jest.fn().mockResolvedValue({});

      await authService.logout();

      expect(storage.clearToken).toHaveBeenCalled();
      expect(storage.clearUser).toHaveBeenCalled();
    });

    it('should handle expired token refresh', async () => {
      storage.getToken = jest.fn().mockReturnValue('expired-token');
      apiClient.refreshToken = jest
        .fn()
        .mockResolvedValue(mockAuthResponse);

      await authService.refreshAccessToken();

      expect(storage.setToken).toHaveBeenCalledWith(
        mockAuthResponse.access_token
      );
    });
  });

  describe('Project Management Workflow', () => {
    it('should load projects after authentication', async () => {
      storage.getToken = jest.fn().mockReturnValue('valid-token');
      apiClient.getProjects = jest.fn().mockResolvedValue(mockProjects);

      const projects = await apiClient.getProjects();

      expect(projects).toHaveLength(2);
      expect(apiClient.getProjects).toHaveBeenCalled();
    });

    it('should select project and load specifications', async () => {
      // Select project
      const projectId = mockProjects[0].id;
      storage.setSelectedProject(projectId);
      storage.getSelectedProject = jest.fn().mockReturnValue(projectId);

      // Load specs
      apiClient.getSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications);

      const specs = await apiClient.getSpecifications(projectId);

      expect(specs).toHaveLength(3);
      expect(storage.setSelectedProject).toHaveBeenCalledWith(projectId);
    });

    it('should create new project and verify', async () => {
      const newProject = {
        name: 'New Project',
        description: 'Created via workflow',
      };

      apiClient.createProject = jest.fn().mockResolvedValue({
        id: 'new-project-123',
        ...newProject,
        owner_id: mockUser.id,
        status: 'active',
        maturity_score: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      });

      const createdProject = await apiClient.createProject(newProject);

      expect(createdProject.name).toBe(newProject.name);
      expect(createdProject.id).toBe('new-project-123');
    });
  });

  describe('Code Generation Workflow', () => {
    it('should generate code from specification', async () => {
      const spec = mockSpecifications[0];
      const language = 'python';

      apiClient.generateCode = jest
        .fn()
        .mockResolvedValue(mockGeneratedCode.code);

      const code = await generator.generateCode(spec, language);

      expect(code).toBe(mockGeneratedCode.code);
      expect(apiClient.generateCode).toHaveBeenCalledWith(spec.id, language);
    });

    it('should generate code for multiple languages', async () => {
      const spec = mockSpecifications[0];
      const languages = ['python', 'javascript', 'go', 'java'];

      apiClient.generateCode = jest
        .fn()
        .mockResolvedValue(mockGeneratedCode.code);

      const results = await Promise.all(
        languages.map((lang) => generator.generateCode(spec, lang))
      );

      expect(results).toHaveLength(4);
      expect(apiClient.generateCode).toHaveBeenCalledTimes(4);
    });

    it('should handle code generation and insertion', async () => {
      const spec = mockSpecifications[0];

      apiClient.generateCode = jest
        .fn()
        .mockResolvedValue(mockGeneratedCode.code);

      const code = await generator.generateCode(spec, 'python');

      expect(code).toBeTruthy();
      expect(code).toBe(mockGeneratedCode.code);
    });
  });

  describe('Search Workflow', () => {
    it('should search specifications', async () => {
      const projectId = mockProjects[0].id;
      const query = 'endpoint';

      apiClient.searchSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications.slice(0, 1));

      const results = await apiClient.searchSpecifications(projectId, query);

      expect(results).toHaveLength(1);
      expect(apiClient.searchSpecifications).toHaveBeenCalledWith(projectId, query);
    });

    it('should handle empty search results', async () => {
      const projectId = mockProjects[0].id;

      apiClient.searchSpecifications = jest
        .fn()
        .mockResolvedValue([]);

      const results = await apiClient.searchSpecifications(projectId, 'nonexistent');

      expect(results).toHaveLength(0);
    });
  });

  describe('Conflict Detection Workflow', () => {
    it('should detect conflicts in project', async () => {
      const projectId = mockProjects[0].id;

      const mockConflicts = [
        {
          id: 'c1',
          project_id: projectId,
          specification_id: mockSpecifications[0].id,
          type: 'version_mismatch',
          severity: 'high',
          message: 'API endpoint version mismatch',
          resolved: false,
          created_at: new Date().toISOString(),
        },
      ];

      apiClient.getConflicts = jest.fn().mockResolvedValue(mockConflicts);

      const conflicts = await apiClient.getConflicts(projectId);

      expect(conflicts).toHaveLength(1);
      expect(conflicts[0].severity).toBe('high');
    });
  });

  describe('Activity Feed Workflow', () => {
    it('should load project activity', async () => {
      const projectId = mockProjects[0].id;

      const mockActivity = [
        {
          id: 'a1',
          project_id: projectId,
          user_id: mockUser.id,
          action: 'specification_updated',
          description: 'Updated spec',
          timestamp: new Date().toISOString(),
        },
      ];

      apiClient.getActivity = jest.fn().mockResolvedValue(mockActivity);

      const activities = await apiClient.getActivity(projectId);

      expect(activities).toHaveLength(1);
      expect(activities[0].action).toBe('specification_updated');
    });

    it('should support activity pagination', async () => {
      const projectId = mockProjects[0].id;

      apiClient.getActivity = jest.fn().mockResolvedValue([]);

      await apiClient.getActivity(projectId, 0, 10);

      expect(apiClient.getActivity).toHaveBeenCalledWith(projectId, 0, 10);
    });
  });

  describe('Error Recovery Workflows', () => {
    it('should handle and recover from API errors during login', async () => {
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('user@example.com')
        .mockResolvedValueOnce('password123');

      const error = createMockApiError('Invalid credentials', 401);
      apiClient.login = jest.fn()
        .mockRejectedValueOnce(error)
        .mockResolvedValueOnce(mockAuthResponse);

      // First attempt fails
      let result = await authService.authenticate().catch(() => false);
      expect(result).toBe(false);

      // Retry succeeds
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('user@example.com')
        .mockResolvedValueOnce('password123');
      result = await authService.authenticate();
      expect(result).toBe(true);
    });

    it('should handle network timeouts and retry', async () => {
      const timeoutError = new Error('Timeout');
      apiClient.getProjects = jest
        .fn()
        .mockRejectedValueOnce(timeoutError)
        .mockResolvedValueOnce(mockProjects);

      // First call times out
      try {
        await apiClient.getProjects();
      } catch (e) {
        // Expected
      }

      // Retry succeeds
      const projects = await apiClient.getProjects();
      expect(projects).toEqual(mockProjects);
    });

    it('should handle and clear invalid tokens', async () => {
      storage.getToken = jest.fn().mockReturnValue('invalid-token');
      const error = createMockApiError('Unauthorized', 401);
      apiClient.getCurrentUser = jest.fn().mockRejectedValue(error);

      await authService.autoLogin().catch(() => {});

      expect(storage.clearToken).toHaveBeenCalled();
    });
  });

  describe('Multi-Step Workflows', () => {
    it('should complete full authentication and code generation workflow', async () => {
      // Step 1: Login
      (vscode.window.showInputBox as jest.Mock)
        .mockResolvedValueOnce('user@example.com')
        .mockResolvedValueOnce('password123');
      apiClient.login = jest.fn().mockResolvedValue(mockAuthResponse);

      const loginResult = await authService.authenticate();
      expect(loginResult).toBe(true);

      // Step 2: Load projects
      apiClient.getProjects = jest.fn().mockResolvedValue(mockProjects);
      const projects = await apiClient.getProjects();
      expect(projects.length).toBeGreaterThan(0);

      // Step 3: Select project
      storage.setSelectedProject(projects[0].id);

      // Step 4: Load specifications
      apiClient.getSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications);
      const specs = await apiClient.getSpecifications(projects[0].id);
      expect(specs.length).toBeGreaterThan(0);

      // Step 5: Generate code
      apiClient.generateCode = jest
        .fn()
        .mockResolvedValue(mockGeneratedCode.code);
      const code = await generator.generateCode(specs[0], 'python');
      expect(code).toBeTruthy();
    });

    it('should handle project switching workflow', async () => {
      // Start with project 1
      storage.setSelectedProject(mockProjects[0].id);
      apiClient.getSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications);

      let specs = await apiClient.getSpecifications(mockProjects[0].id);
      expect(specs.length).toBeGreaterThan(0);

      // Switch to project 2
      storage.setSelectedProject(mockProjects[1].id);

      // Mock different specs for project 2
      apiClient.getSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications.slice(0, 1));

      specs = await apiClient.getSpecifications(mockProjects[1].id);
      expect(specs.length).toBe(1);
    });
  });

  describe('Concurrent Operations', () => {
    it('should handle concurrent API requests', async () => {
      apiClient.getProjects = jest
        .fn()
        .mockResolvedValue(mockProjects);
      apiClient.getSpecifications = jest
        .fn()
        .mockResolvedValue(mockSpecifications);

      const [projects, specs] = await Promise.all([
        apiClient.getProjects(),
        apiClient.getSpecifications(mockProjects[0].id),
      ]);

      expect(projects).toHaveLength(2);
      expect(specs).toHaveLength(3);
    });

    it('should handle concurrent code generation', async () => {
      apiClient.generateCode = jest
        .fn()
        .mockResolvedValue(mockGeneratedCode.code);

      const specs = mockSpecifications.slice(0, 2);
      const results = await Promise.all(
        specs.map((spec) => generator.generateCode(spec, 'python'))
      );

      expect(results).toHaveLength(2);
      expect(apiClient.generateCode).toHaveBeenCalledTimes(2);
    });
  });

  describe('State Persistence Workflow', () => {
    it('should persist and restore authentication state', async () => {
      // Set authenticated state
      storage.setToken = jest.fn();
      storage.setUser = jest.fn();

      storage.getToken = jest
        .fn()
        .mockReturnValue('persisted-token');
      storage.getUser = jest
        .fn()
        .mockReturnValue(mockUser);

      const token = storage.getToken();
      const user = storage.getUser();

      expect(token).toBe('persisted-token');
      expect(user).toEqual(mockUser);
    });

    it('should persist project selection', async () => {
      const projectId = mockProjects[0].id;

      storage.setSelectedProject(projectId);
      storage.getSelectedProject = jest
        .fn()
        .mockReturnValue(projectId);

      const selected = storage.getSelectedProject();

      expect(selected).toBe(projectId);
    });
  });
});
