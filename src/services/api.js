// API Configuration and Base Setup
const API_BASE_URL =
  process.env.REACT_APP_API_BASE_URL || "http://localhost:8080/api"

// Helper function to get auth token from localStorage
const getAuthToken = () => {
  return localStorage.getItem("access_token")
}

// Helper function to get organization ID from localStorage
const getOrgId = () => {
  return localStorage.getItem("org_id")
}

// Helper function to build headers
const getHeaders = (includeAuth = true, contentType = "application/json") => {
  const headers = {}

  if (contentType) {
    headers["Content-Type"] = contentType
  }

  if (includeAuth) {
    const token = getAuthToken()
    if (token) {
      headers["Authorization"] = `Bearer ${token}`
    }
  }

  return headers
}

// Generic API request handler with error handling
const apiRequest = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      ...options,
      headers: {
        ...getHeaders(options.auth !== false, options.contentType),
        ...options.headers,
      },
    })

    // Handle different response types
    const contentType = response.headers.get("content-type")
    let data

    if (contentType && contentType.includes("application/json")) {
      data = await response.json()
    } else {
      data = await response.text()
    }

    if (!response.ok) {
      throw {
        status: response.status,
        message: data.error || data.message || "Request failed",
        data,
      }
    }

    return data
  } catch (error) {
    console.error("API Request Error:", error)
    throw error
  }
}

// ============================================================================
// AUTHENTICATION API
// ============================================================================

export const authAPI = {
  /**
   * Register a new organization with admin user
   * @param {Object} data - Registration data
   * @param {string} data.org_name - Organization name
   * @param {string} data.org_address - Organization address (optional)
   * @param {string} data.admin_email - Admin email
   * @param {string} data.admin_full_name - Admin full name
   * @param {string} data.admin_password - Admin password (min 6 chars)
   * @returns {Promise<{org_id: string, user_id: string, message: string}>}
   */
  register: async (data) => {
    const response = await apiRequest("/auth/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify(data),
    })

    // Save org_id for future requests
    if (response.org_id) {
      localStorage.setItem("org_id", response.org_id)
    }

    return response
  },

  /**
   * Login user and get JWT token
   * @param {Object} credentials
   * @param {string} credentials.email - User email
   * @param {string} credentials.password - User password
   * @returns {Promise<{access_token: string, refresh_token: string, expires_in: number, token_type: string}>}
   */
  login: async (credentials) => {
    const response = await apiRequest("/auth/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify(credentials),
    })

    // Save tokens
    if (response.access_token) {
      localStorage.setItem("access_token", response.access_token)
    }
    if (response.refresh_token) {
      localStorage.setItem("refresh_token", response.refresh_token)
    }

    return response
  },

  /**
   * Refresh JWT token
   * @returns {Promise<{access_token: string, refresh_token: string, expires_in: number, token_type: string}>}
   */
  refreshToken: async () => {
    const response = await apiRequest("/auth/refresh_token", {
      method: "POST",
    })

    // Update tokens
    if (response.access_token) {
      localStorage.setItem("access_token", response.access_token)
    }
    if (response.refresh_token) {
      localStorage.setItem("refresh_token", response.refresh_token)
    }

    return response
  },

  /**
   * Logout current user
   * @returns {Promise<{message: string}>}
   */
  logout: async () => {
    const response = await apiRequest("/auth/logout", {
      method: "POST",
    })

    // Clear tokens and user data
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("org_id")
    localStorage.removeItem("current_user")

    return response
  },

  /**
   * Get current authenticated user info
   * @returns {Promise<{user: Object, claims: Object}>}
   */
  getCurrentUser: async () => {
    const response = await apiRequest("/auth/me", {
      method: "GET",
    })

    // Cache user info
    if (response.user) {
      localStorage.setItem("current_user", JSON.stringify(response.user))
      if (response.user.organization_id) {
        localStorage.setItem("org_id", response.user.organization_id)
      }
    }

    return response
  },
}

// ============================================================================
// STAFFING API
// ============================================================================

export const staffingAPI = {
  /**
   * Get staffing summary with employee breakdown by role
   * @returns {Promise<{total_employees: number, by_role: Object, employees: Array}>}
   */
  getStaffingSummary: async () => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing`, {
      method: "GET",
    })
  },

  /**
   * Create a new employee/user
   * @param {Object} data - Employee data
   * @param {string} data.email - Employee email
   * @param {string} data.full_name - Employee full name
   * @param {string} data.role - Employee role (manager, staff)
   * @returns {Promise<{user_id: string, message: string}>}
   */
  createEmployee: async (data) => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  /**
   * Get all employees in the organization
   * @returns {Promise<{employees: Array, total: number}>}
   */
  getAllEmployees: async () => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing/employees`, {
      method: "GET",
    })
  },

  /**
   * Get specific employee details
   * @param {string} employeeId - Employee UUID
   * @returns {Promise<Object>} Employee details
   */
  getEmployee: async (employeeId) => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing/employees/${employeeId}`, {
      method: "GET",
    })
  },

  /**
   * Layoff an employee
   * @param {string} employeeId - Employee UUID
   * @param {string} reason - Layoff reason (optional)
   * @returns {Promise<{employee_id: string, message: string}>}
   */
  layoffEmployee: async (employeeId, reason = "") => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing/employees/${employeeId}/layoff`, {
      method: "DELETE",
      body: JSON.stringify({ reason }),
    })
  },

  /**
   * Bulk upload employees via CSV
   * @param {File} file - CSV file with employee data
   * @returns {Promise<{created_count: number, failed_count: number, created: Array, failed: Array, message: string}>}
   */
  bulkUploadEmployees: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/${orgId}/staffing/upload`, {
      method: "POST",
      contentType: null, // Let browser set it for FormData
      body: formData,
    })
  },
}

// ============================================================================
// EMPLOYEE REQUESTS API
// ============================================================================

export const requestsAPI = {
  /**
   * Get all requests for a specific employee
   * @param {string} employeeId - Employee UUID
   * @returns {Promise<{requests: Array, total: number}>}
   */
  getEmployeeRequests: async (employeeId) => {
    const orgId = getOrgId()
    return apiRequest(`/${orgId}/staffing/employees/${employeeId}/requests`, {
      method: "GET",
    })
  },

  /**
   * Approve an employee request
   * @param {string} employeeId - Employee UUID
   * @param {string} requestId - Request UUID
   * @returns {Promise<{request_id: string, message: string}>}
   */
  approveRequest: async (employeeId, requestId) => {
    const orgId = getOrgId()
    return apiRequest(
      `/${orgId}/staffing/employees/${employeeId}/requests/approve`,
      {
        method: "POST",
        body: JSON.stringify({ request_id: requestId }),
      },
    )
  },

  /**
   * Decline an employee request
   * @param {string} employeeId - Employee UUID
   * @param {string} requestId - Request UUID
   * @returns {Promise<{request_id: string, message: string}>}
   */
  declineRequest: async (employeeId, requestId) => {
    const orgId = getOrgId()
    return apiRequest(
      `/${orgId}/staffing/employees/${employeeId}/requests/decline`,
      {
        method: "POST",
        body: JSON.stringify({ request_id: requestId }),
      },
    )
  },
}

// ============================================================================
// HEALTH API
// ============================================================================

export const healthAPI = {
  /**
   * Check API health status
   * @returns {Promise<{status: string, database: string}>}
   */
  checkHealth: async () => {
    return apiRequest("/health", {
      method: "GET",
      auth: false,
    })
  },
}

// ============================================================================
// EXPORT DEFAULT API OBJECT
// ============================================================================

const api = {
  auth: authAPI,
  staffing: staffingAPI,
  requests: requestsAPI,
  health: healthAPI,
}

export default api
