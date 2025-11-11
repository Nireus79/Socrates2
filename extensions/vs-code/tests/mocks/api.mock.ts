/**
 * API Mock Utilities and Test Data
 *
 * Mock data and helper functions for API testing
 */

export const mockUser = {
  id: 'user-123',
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  created_at: '2025-01-01T00:00:00Z',
};

export const mockProject = {
  id: 'project-123',
  name: 'Test Project',
  description: 'A test project',
  owner_id: 'user-123',
  status: 'active',
  maturity_score: 75,
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

export const mockProjects = [
  mockProject,
  {
    id: 'project-456',
    name: 'Another Project',
    description: 'Another test project',
    owner_id: 'user-123',
    status: 'active',
    maturity_score: 50,
    created_at: '2025-01-02T00:00:00Z',
    updated_at: '2025-01-02T00:00:00Z',
  },
];

export const mockSpecification = {
  id: 'spec-123',
  project_id: 'project-123',
  key: 'api.endpoint',
  value: 'GET /api/users',
  category: 'API Endpoints',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
};

export const mockSpecifications = [
  mockSpecification,
  {
    id: 'spec-456',
    project_id: 'project-123',
    key: 'database.schema',
    value: 'PostgreSQL 12+',
    category: 'Database',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
  {
    id: 'spec-789',
    project_id: 'project-123',
    key: 'auth.method',
    value: 'JWT',
    category: 'Authentication',
    created_at: '2025-01-01T00:00:00Z',
    updated_at: '2025-01-01T00:00:00Z',
  },
];

export const mockConflict = {
  id: 'conflict-123',
  project_id: 'project-123',
  specification_id: 'spec-123',
  type: 'version_mismatch',
  severity: 'high',
  message: 'API endpoint version mismatch detected',
  resolved: false,
  created_at: '2025-01-01T00:00:00Z',
};

export const mockConflicts = [
  mockConflict,
  {
    id: 'conflict-456',
    project_id: 'project-123',
    specification_id: 'spec-456',
    type: 'deprecated_usage',
    severity: 'medium',
    message: 'Database schema change detected',
    resolved: false,
    created_at: '2025-01-01T00:00:00Z',
  },
];

export const mockActivity = {
  id: 'activity-123',
  project_id: 'project-123',
  user_id: 'user-123',
  action: 'specification_updated',
  description: 'Updated specification: api.endpoint',
  timestamp: '2025-01-01T12:00:00Z',
};

export const mockActivities = [
  mockActivity,
  {
    id: 'activity-456',
    project_id: 'project-123',
    user_id: 'user-456',
    action: 'project_created',
    description: 'Created project: Test Project',
    timestamp: '2025-01-01T10:00:00Z',
  },
];

export const mockGeneratedCode = {
  language: 'python',
  code: `def get_users():
    """Get all users from the API"""
    endpoint = "GET /api/users"
    return requests.get(endpoint)`,
  filename: 'api_client.py',
};

export const mockApiError = {
  status: 400,
  error_code: 'VALIDATION_ERROR',
  message: 'Invalid request parameters',
  details: {
    field: 'email',
    reason: 'Invalid email format',
  },
};

export const mockAuthResponse = {
  access_token: 'eyJhbGciOiJIUzI1NiIs...',
  refresh_token: 'eyJhbGciOiJIUzI1NiIs...',
  user: mockUser,
};

/**
 * Create a mock API client response
 */
export const createMockApiResponse = <T>(
  data: T,
  status: number = 200
) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {} as any,
});

/**
 * Create a mock API error response
 */
export const createMockApiError = (
  message: string = 'Request failed',
  status: number = 500,
  response?: any
) => ({
  message,
  code: 'ERR_REQUEST_FAILED',
  request: {},
  response: response || {
    status,
    data: mockApiError,
    headers: {},
    config: {} as any,
  },
  config: {} as any,
  isAxiosError: true,
  toJSON: () => ({}),
});
