/**
 * Socrates2 API Client for VS Code Extension
 *
 * Handles all HTTP communication with the backend API
 */

import axios, { AxiosInstance, AxiosError } from 'axios';
import { StorageService } from '../utils/storage';
import { Logger } from '../utils/logger';

export interface Project {
  id: string;
  name: string;
  description: string;
  user_id: string;
  maturity_score: number;
  status: string;
  created_at: string;
  updated_at: string;
}

export interface Specification {
  id: string;
  project_id: string;
  category: string;
  key: string;
  value: string;
  content: string | null;
  created_at: string;
  updated_at: string;
}

export interface Conflict {
  id: string;
  project_id: string;
  spec1_id: string;
  spec2_id: string;
  description: string;
  severity: 'low' | 'medium' | 'high';
  created_at: string;
}

export interface Activity {
  id: string;
  project_id: string;
  user_id: string;
  action_type: string;
  description: string;
  created_at: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
  message?: string;
}

export class SocratesApiClient {
  private client: AxiosInstance;
  private baseUrl: string;
  private storage: StorageService;
  private logger: Logger;

  constructor(baseUrl: string, storage: StorageService) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.storage = storage;
    this.logger = new Logger('SocratesApiClient');

    // Create axios instance with default config
    this.client = axios.create({
      baseURL: this.baseUrl,
      timeout: 10000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor to attach token
    this.client.interceptors.request.use(
      (config) => {
        const token = this.storage.getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          // Unauthorized - token likely expired
          this.storage.clearToken();
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Health check
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await this.client.get('/');
      return response.status === 200;
    } catch (error) {
      this.logger.error(`Health check failed: ${error}`);
      return false;
    }
  }

  /**
   * Get current user info
   */
  async getCurrentUser(): Promise<any> {
    try {
      const response = await this.client.get('/api/v1/auth/me');
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to get current user: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get all projects for current user
   */
  async getProjects(skip: number = 0, limit: number = 50): Promise<Project[]> {
    try {
      const response = await this.client.get('/api/v1/projects', {
        params: { skip, limit },
      });
      return response.data.projects || [];
    } catch (error) {
      this.logger.error(`Failed to get projects: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get single project
   */
  async getProject(projectId: string): Promise<Project> {
    try {
      const response = await this.client.get(`/api/v1/projects/${projectId}`);
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to get project ${projectId}: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Create new project
   */
  async createProject(name: string, description: string = ''): Promise<Project> {
    try {
      const response = await this.client.post('/api/v1/projects', {
        name,
        description,
      });
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to create project: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get specifications for a project
   */
  async getSpecifications(
    projectId: string,
    category?: string
  ): Promise<Specification[]> {
    try {
      const params: any = {};
      if (category) {
        params.category = category;
      }

      const response = await this.client.get(
        `/api/v1/projects/${projectId}/specifications`,
        { params }
      );
      return response.data.specifications || [];
    } catch (error) {
      this.logger.error(`Failed to get specifications: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Create specification
   */
  async createSpecification(
    projectId: string,
    category: string,
    key: string,
    value: string,
    content?: string
  ): Promise<Specification> {
    try {
      const response = await this.client.post(
        `/api/v1/projects/${projectId}/specifications`,
        {
          category,
          key,
          value,
          content,
        }
      );
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to create specification: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get project conflicts
   */
  async getConflicts(projectId: string): Promise<Conflict[]> {
    try {
      const response = await this.client.get(
        `/api/v1/projects/${projectId}/conflicts`
      );
      return response.data.conflicts || [];
    } catch (error) {
      this.logger.error(`Failed to get conflicts: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Search specifications
   */
  async searchSpecifications(query: string, limit: number = 20): Promise<any[]> {
    try {
      const response = await this.client.get('/api/v1/search', {
        params: { query, resource_type: 'specification', limit },
      });
      return response.data.results || [];
    } catch (error) {
      this.logger.error(`Failed to search specifications: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get project activity
   */
  async getActivity(
    projectId: string,
    limit: number = 50
  ): Promise<Activity[]> {
    try {
      const response = await this.client.get(
        `/api/v1/notifications/projects/${projectId}/activity`,
        { params: { limit } }
      );
      return response.data.activities || [];
    } catch (error) {
      this.logger.error(`Failed to get activity: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Generate code from specification
   */
  async generateCode(
    specificationId: string,
    language: string,
    context: any = {}
  ): Promise<string> {
    try {
      const response = await this.client.post(
        '/api/v1/generate/code',
        {
          specification_id: specificationId,
          language,
          context,
        }
      );
      return response.data.code || '';
    } catch (error) {
      this.logger.error(`Failed to generate code: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Get supported export formats
   */
  async getExportFormats(): Promise<any[]> {
    try {
      const response = await this.client.get('/api/v1/export/formats');
      return response.data.formats || [];
    } catch (error) {
      this.logger.error(`Failed to get export formats: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Export specifications
   */
  async exportSpecifications(
    projectId: string,
    format: string = 'json'
  ): Promise<string> {
    try {
      const response = await this.client.get(
        `/api/v1/export/projects/${projectId}/specs`,
        {
          params: { format },
        }
      );
      return response.data;
    } catch (error) {
      this.logger.error(`Failed to export specifications: ${error}`);
      throw this.handleError(error);
    }
  }

  /**
   * Handle API errors
   */
  private handleError(error: any): Error {
    if (axios.isAxiosError(error)) {
      const axiosError = error as AxiosError;

      if (axiosError.response) {
        const status = axiosError.response.status;
        const data = axiosError.response.data as any;

        if (status === 404) {
          return new Error(`Not found: ${data.detail || 'Resource not found'}`);
        }

        if (status === 401) {
          return new Error('Unauthorized: Please sign in again');
        }

        if (status === 403) {
          return new Error('Forbidden: You do not have permission');
        }

        if (status === 422 || status === 400) {
          return new Error(`Validation error: ${data.detail || 'Invalid input'}`);
        }

        return new Error(
          data.detail || data.message || `API error (${status})`
        );
      }

      if (axiosError.request) {
        return new Error('Network error: No response from server');
      }

      return new Error(`Request error: ${axiosError.message}`);
    }

    return error instanceof Error ? error : new Error(String(error));
  }

  /**
   * Check if API is reachable
   */
  async isReachable(): Promise<boolean> {
    try {
      const response = await axios.get(`${this.baseUrl}/`);
      return response.status === 200;
    } catch {
      return false;
    }
  }

  /**
   * Get API base URL
   */
  getBaseUrl(): string {
    return this.baseUrl;
  }

  /**
   * Set new API base URL
   */
  setBaseUrl(url: string): void {
    this.baseUrl = url.replace(/\/$/, '');
    this.client.defaults.baseURL = this.baseUrl;
  }
}
