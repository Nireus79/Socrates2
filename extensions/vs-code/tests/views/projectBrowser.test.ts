/**
 * Project Browser View Provider Unit Tests
 *
 * Tests for the project browser tree view provider
 */

import * as vscode from 'vscode';
import { ProjectBrowserProvider, ProjectItem } from '../../src/views/projectBrowser';
import { SocratesApiClient } from '../../src/api/client';
import { StorageService } from '../../src/utils/storage';
import { Logger } from '../../src/utils/logger';
import { mockProjects, mockProject, createMockApiError } from '../mocks/api.mock';

jest.mock('../../src/api/client');
jest.mock('../../src/utils/storage');
jest.mock('../../src/utils/logger');

describe('ProjectBrowserProvider', () => {
  let provider: ProjectBrowserProvider;
  let mockApiClient: jest.Mocked<SocratesApiClient>;
  let mockStorage: jest.Mocked<StorageService>;
  let mockLogger: jest.Mocked<Logger>;

  beforeEach(() => {
    jest.clearAllMocks();
    jest.useFakeTimers();

    mockApiClient = new SocratesApiClient(
      'http://localhost:8000',
      null as any
    ) as jest.Mocked<SocratesApiClient>;
    mockStorage = new StorageService(null as any) as jest.Mocked<StorageService>;
    mockLogger = new Logger('test') as jest.Mocked<Logger>;

    mockStorage.getSelectedProject = jest.fn().mockReturnValue(null);
    mockStorage.setSelectedProject = jest.fn();
    mockApiClient.getProjects = jest.fn().mockResolvedValue(mockProjects);

    provider = new ProjectBrowserProvider(mockApiClient, mockStorage, mockLogger);
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  describe('Tree Data Provider Interface', () => {
    it('should implement tree data provider', () => {
      expect(provider).toHaveProperty('getTreeItem');
      expect(provider).toHaveProperty('getChildren');
      expect(provider).toHaveProperty('onDidChangeTreeData');
    });

    it('should have onDidChangeTreeData event', () => {
      expect(provider.onDidChangeTreeData).toBeDefined();
      expect(typeof provider.onDidChangeTreeData).toBe('function');
    });
  });

  describe('getTreeItem', () => {
    it('should return tree item', () => {
      const item = new ProjectItem('Test', vscode.TreeItemCollapsibleState.None, 'project', {
        projectId: 'test-123',
      });

      const result = provider.getTreeItem(item);

      expect(result).toEqual(item);
    });
  });

  describe('getChildren', () => {
    it('should return loading state initially', async () => {
      const items = await provider.getChildren();
      expect(items.length).toBeGreaterThan(0);
    });

    it('should load projects on initialization', async () => {
      jest.runAllTimers();

      await new Promise((resolve) => setTimeout(resolve, 100));

      expect(mockApiClient.getProjects).toHaveBeenCalled();
    });

    it('should return empty array for leaf nodes', async () => {
      const item = new ProjectItem('Test', vscode.TreeItemCollapsibleState.None, 'project', {
        projectId: 'test-123',
      });

      const result = await provider.getChildren(item);

      expect(result).toEqual([]);
    });
  });

  describe('Project Loading', () => {
    it('should load projects from API', async () => {
      const items = await provider['getProjectItems']();

      expect(mockApiClient.getProjects).toHaveBeenCalled();
      expect(items.length).toBe(mockProjects.length);
    });

    it('should map projects to tree items', async () => {
      provider['projects'] = mockProjects;
      provider['loading'] = false;

      const items = await provider['getProjectItems']();

      expect(items).toHaveLength(mockProjects.length);
      items.forEach((item, index) => {
        expect(item.label).toBe(mockProjects[index].name);
        expect(item.contextValue).toBe('project');
      });
    });

    it('should handle loading state', async () => {
      provider['loading'] = true;

      const items = await provider['getProjectItems']();

      expect(items).toHaveLength(1);
      expect(items[0].label).toBe('Loading...');
    });

    it('should handle error state', async () => {
      const error = new Error('Failed to load');
      provider['error'] = error;
      provider['loading'] = false;

      const items = await provider['getProjectItems']();

      expect(items).toHaveLength(1);
      expect(items[0].label).toContain('Error');
    });

    it('should handle empty projects list', async () => {
      provider['projects'] = [];
      provider['loading'] = false;

      const items = await provider['getProjectItems']();

      expect(items).toHaveLength(1);
      expect(items[0].label).toContain('No projects');
    });

    it('should handle API errors', async () => {
      const error = createMockApiError('Internal server error', 500);
      mockApiClient.getProjects = jest.fn().mockRejectedValue(error);

      provider['loading'] = true;
      await (provider as any).loadProjects();

      expect(provider['error']).toBeDefined();
      expect(mockLogger.error).toHaveBeenCalled();
    });
  });

  describe('Refresh', () => {
    it('should refresh projects', async () => {
      mockApiClient.getProjects = jest
        .fn()
        .mockResolvedValue(mockProjects);

      await (provider as any).loadProjects();

      expect(mockApiClient.getProjects).toHaveBeenCalled();
    });

    it('should fire tree data change event on refresh', () => {
      const fireSpy = jest.spyOn(
        (provider as any)._onDidChangeTreeData,
        'fire'
      );

      provider.refresh();

      expect(fireSpy).toHaveBeenCalled();
    });
  });

  describe('Project Selection', () => {
    it('should get selected project', () => {
      mockStorage.getSelectedProject = jest
        .fn()
        .mockReturnValue('project-123');

      const result = provider.getSelectedProject();

      expect(result).toBe('project-123');
    });

    it('should return null when no project selected', () => {
      mockStorage.getSelectedProject = jest.fn().mockReturnValue(null);

      const result = provider.getSelectedProject();

      expect(result).toBeNull();
    });

    it('should set selected project', () => {
      provider.setSelectedProject('project-456');

      expect(mockStorage.setSelectedProject).toHaveBeenCalledWith(
        'project-456'
      );
    });

    it('should fire tree data change event on project selection', () => {
      const fireSpy = jest.spyOn(
        (provider as any)._onDidChangeTreeData,
        'fire'
      );

      provider.setSelectedProject('project-456');

      expect(fireSpy).toHaveBeenCalled();
    });
  });

  describe('ProjectItem Class', () => {
    it('should create project item', () => {
      const item = new ProjectItem('Test Project', vscode.TreeItemCollapsibleState.None, 'project', {
        projectId: 'test-123',
        description: 'Test description',
        maturityScore: 75,
        status: 'active',
      });

      expect(item.label).toBe('Test Project');
      expect(item.projectId).toBe('test-123');
      expect(item.description).toBe('Test description');
      expect(item.maturityScore).toBe(75);
      expect(item.status).toBe('active');
    });

    it('should set context value based on type', () => {
      const item = new ProjectItem(
        'Test',
        vscode.TreeItemCollapsibleState.None,
        'project'
      );

      expect(item.contextValue).toBe('project');
    });

    it('should set icon based on type', () => {
      const projectItem = new ProjectItem(
        'Project',
        vscode.TreeItemCollapsibleState.None,
        'project'
      );
      expect(projectItem.iconPath).toBeDefined();

      const loadingItem = new ProjectItem(
        'Loading',
        vscode.TreeItemCollapsibleState.None,
        'loading'
      );
      expect(loadingItem.iconPath).toBeDefined();

      const errorItem = new ProjectItem(
        'Error',
        vscode.TreeItemCollapsibleState.None,
        'error'
      );
      expect(errorItem.iconPath).toBeDefined();
    });

    it('should create tooltip with markdown', () => {
      const item = new ProjectItem(
        'Test Project',
        vscode.TreeItemCollapsibleState.None,
        'project',
        {
          projectId: 'test-123',
          description: 'Test description',
          maturityScore: 75,
        }
      );

      expect(item.tooltip).toBeDefined();
      expect(item.tooltip?.value).toContain('Test Project');
      expect(item.tooltip?.value).toContain('Test description');
      expect(item.tooltip?.value).toContain('75');
    });

    it('should set command for project items', () => {
      const item = new ProjectItem(
        'Test',
        vscode.TreeItemCollapsibleState.None,
        'project',
        { projectId: 'test-123' }
      );

      expect(item.command).toBeDefined();
      expect(item.command?.command).toBe('socrates.openProject');
      expect(item.command?.arguments).toContain(item);
    });
  });

  describe('Tree Item Rendering', () => {
    it('should render project items with icons', async () => {
      provider['projects'] = mockProjects;
      provider['loading'] = false;

      const items = await provider['getProjectItems']();

      items.forEach((item) => {
        expect(item.iconPath).toBeDefined();
      });
    });

    it('should show correct descriptions', async () => {
      provider['projects'] = [mockProject];
      provider['loading'] = false;

      const items = await provider['getProjectItems']();

      expect(items[0].description).toBe(mockProject.description);
    });
  });

  describe('Error Recovery', () => {
    it('should allow refresh after error', async () => {
      mockApiClient.getProjects = jest
        .fn()
        .mockRejectedValueOnce(new Error('Network error'))
        .mockResolvedValueOnce(mockProjects);

      await (provider as any).loadProjects();
      expect(provider['error']).toBeDefined();

      mockApiClient.getProjects = jest
        .fn()
        .mockResolvedValueOnce(mockProjects);
      await (provider as any).loadProjects();

      expect(provider['error']).toBeNull();
    });
  });
});
