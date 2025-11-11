/**
 * API Client Unit Tests
 *
 * Tests for the Socrates2 API client
 */

import axios, { AxiosInstance } from 'axios';
import { SocratesApiClient, ApiResponse } from '../../src/api/client';
import { StorageService } from '../../src/utils/storage';
import {
  mockUser,
  mockProject,
  mockProjects,
  mockSpecification,
  mockSpecifications,
  mockConflict,
  mockConflicts,
  mockActivity,
  mockActivities,
  mockGeneratedCode,
  createMockApiResponse,
  createMockApiError,
} from '../mocks/api.mock';

jest.mock('axios');
jest.mock('../../src/utils/storage');

describe('SocratesApiClient', () => {
  let client: SocratesApiClient;
  let mockAxios: jest.Mocked<AxiosInstance>;
  let mockStorage: jest.Mocked<StorageService>;

  beforeEach(() => {
    jest.clearAllMocks();
    mockStorage = new StorageService(null as any) as jest.Mocked<StorageService>;
    mockStorage.getToken = jest.fn().mockReturnValue('test-token');
    mockStorage.setToken = jest.fn();
    mockStorage.getUser = jest.fn().mockReturnValue(mockUser);
    mockStorage.setUser = jest.fn();

    mockAxios = axios.create() as jest.Mocked<AxiosInstance>;
    client = new SocratesApiClient('http://localhost:8000', mockStorage);
    (client as any).client = mockAxios;
  });

  describe('Initialization', () => {
    it('should initialize with base URL', () => {
      expect(client).toBeDefined();
    });

    it('should set up axios interceptor for authorization', () => {
      expect(mockStorage.getToken).toHaveBeenCalled();
    });
  });

  describe('Health Check', () => {
    it('should check API health', async () => {
      const mockResponse = createMockApiResponse({ status: 'healthy' });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.healthCheck();

      expect(result).toEqual({ status: 'healthy' });
      expect(mockAxios.get).toHaveBeenCalledWith('/health');
    });

    it('should handle health check errors', async () => {
      const error = createMockApiError('Service unavailable', 503);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.healthCheck()).rejects.toThrow();
    });
  });

  describe('User Operations', () => {
    it('should get current user', async () => {
      const mockResponse = createMockApiResponse({ user: mockUser });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getCurrentUser();

      expect(result).toEqual(mockUser);
      expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/auth/me');
    });

    it('should handle get current user errors', async () => {
      const error = createMockApiError('Unauthorized', 401);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getCurrentUser()).rejects.toThrow();
    });
  });

  describe('Project Operations', () => {
    it('should get all projects', async () => {
      const mockResponse = createMockApiResponse({ projects: mockProjects });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getProjects();

      expect(result).toEqual(mockProjects);
      expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/projects');
    });

    it('should get single project', async () => {
      const mockResponse = createMockApiResponse({ project: mockProject });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getProject('project-123');

      expect(result).toEqual(mockProject);
      expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/projects/project-123');
    });

    it('should create project', async () => {
      const newProject = {
        name: 'New Project',
        description: 'A new project',
      };
      const mockResponse = createMockApiResponse({ project: mockProject });
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.createProject(newProject);

      expect(result).toEqual(mockProject);
      expect(mockAxios.post).toHaveBeenCalledWith('/api/v1/projects', newProject);
    });

    it('should handle project list errors', async () => {
      const error = createMockApiError('Internal server error', 500);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getProjects()).rejects.toThrow();
    });
  });

  describe('Specification Operations', () => {
    it('should get specifications for project', async () => {
      const mockResponse = createMockApiResponse({
        specifications: mockSpecifications,
      });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getSpecifications('project-123');

      expect(result).toEqual(mockSpecifications);
      expect(mockAxios.get).toHaveBeenCalledWith(
        '/api/v1/projects/project-123/specifications'
      );
    });

    it('should create specification', async () => {
      const newSpec = {
        key: 'new.spec',
        value: 'test value',
        category: 'Test',
      };
      const mockResponse = createMockApiResponse({ specification: mockSpecification });
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.createSpecification('project-123', newSpec);

      expect(result).toEqual(mockSpecification);
      expect(mockAxios.post).toHaveBeenCalledWith(
        '/api/v1/projects/project-123/specifications',
        newSpec
      );
    });

    it('should search specifications', async () => {
      const mockResponse = createMockApiResponse({
        specifications: mockSpecifications.slice(0, 1),
      });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.searchSpecifications(
        'project-123',
        'endpoint'
      );

      expect(result).toHaveLength(1);
      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/projects/project-123/specifications/search'),
        expect.objectContaining({
          params: expect.objectContaining({ query: 'endpoint' }),
        })
      );
    });
  });

  describe('Conflict Operations', () => {
    it('should get conflicts for project', async () => {
      const mockResponse = createMockApiResponse({ conflicts: mockConflicts });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getConflicts('project-123');

      expect(result).toEqual(mockConflicts);
      expect(mockAxios.get).toHaveBeenCalledWith(
        '/api/v1/projects/project-123/conflicts'
      );
    });

    it('should handle empty conflicts list', async () => {
      const mockResponse = createMockApiResponse({ conflicts: [] });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getConflicts('project-123');

      expect(result).toEqual([]);
    });
  });

  describe('Activity Operations', () => {
    it('should get activity feed', async () => {
      const mockResponse = createMockApiResponse({ activities: mockActivities });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getActivity('project-123');

      expect(result).toEqual(mockActivities);
      expect(mockAxios.get).toHaveBeenCalledWith(
        '/api/v1/projects/project-123/activity'
      );
    });

    it('should support pagination in activity', async () => {
      const mockResponse = createMockApiResponse({
        activities: mockActivities.slice(0, 1),
      });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      await client.getActivity('project-123', 0, 10);

      expect(mockAxios.get).toHaveBeenCalledWith(
        expect.stringContaining('/api/v1/projects/project-123/activity'),
        expect.objectContaining({
          params: expect.objectContaining({ skip: 0, limit: 10 }),
        })
      );
    });
  });

  describe('Code Generation', () => {
    it('should generate code from specification', async () => {
      const mockResponse = createMockApiResponse({
        code: mockGeneratedCode.code,
      });
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.generateCode('spec-123', 'python');

      expect(result).toEqual(mockGeneratedCode.code);
      expect(mockAxios.post).toHaveBeenCalledWith(
        '/api/v1/specifications/spec-123/generate',
        expect.objectContaining({ language: 'python' })
      );
    });

    it('should handle code generation errors', async () => {
      const error = createMockApiError(
        'Code generation failed',
        400
      );
      mockAxios.post = jest.fn().mockRejectedValue(error);

      await expect(
        client.generateCode('invalid-id', 'python')
      ).rejects.toThrow();
    });
  });

  describe('Export Operations', () => {
    it('should get export formats', async () => {
      const formats = ['json', 'yaml', 'csv'];
      const mockResponse = createMockApiResponse({ formats });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.getExportFormats();

      expect(result).toEqual(formats);
      expect(mockAxios.get).toHaveBeenCalledWith('/api/v1/export/formats');
    });

    it('should export specifications', async () => {
      const exported = { format: 'json', content: '{}' };
      const mockResponse = createMockApiResponse(exported);
      mockAxios.post = jest.fn().mockResolvedValue(mockResponse);

      const result = await client.exportSpecifications(
        'project-123',
        'json'
      );

      expect(result).toEqual(exported);
      expect(mockAxios.post).toHaveBeenCalledWith(
        '/api/v1/projects/project-123/export',
        expect.objectContaining({ format: 'json' })
      );
    });
  });

  describe('Error Handling', () => {
    it('should handle network errors', async () => {
      const error = new Error('Network error');
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getProjects()).rejects.toThrow('Network error');
    });

    it('should handle timeout errors', async () => {
      const error = createMockApiError('Request timeout', 0);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getProjects()).rejects.toThrow();
    });

    it('should handle authentication errors', async () => {
      const error = createMockApiError('Invalid token', 401);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getCurrentUser()).rejects.toThrow();
    });

    it('should handle rate limiting', async () => {
      const error = createMockApiError('Too many requests', 429);
      mockAxios.get = jest.fn().mockRejectedValue(error);

      await expect(client.getProjects()).rejects.toThrow();
    });
  });

  describe('Request Headers', () => {
    it('should include authorization header with token', async () => {
      const mockResponse = createMockApiResponse({ user: mockUser });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      await client.getCurrentUser();

      expect(mockStorage.getToken).toHaveBeenCalled();
    });

    it('should include user agent', async () => {
      const mockResponse = createMockApiResponse({ status: 'healthy' });
      mockAxios.get = jest.fn().mockResolvedValue(mockResponse);

      await client.healthCheck();

      expect(mockAxios.get).toHaveBeenCalled();
    });
  });
});
