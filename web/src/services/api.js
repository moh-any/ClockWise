const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || "http://localhost"

const getAuthToken = () => {
  return localStorage.getItem("access_token")
}

const getOrgId = () => {
  return localStorage.getItem("org_id")
}

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

let isRefreshing = false
let failedQueue = []

const processQueue = (error, token = null) => {
  failedQueue.forEach((prom) => {
    if (error) {
      prom.reject(error)
    } else {
      prom.resolve(token)
    }
  })
  failedQueue = []
}

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

    // Handle 401 Unauthorized (token expired)
    if (response.status === 401 && options.auth !== false && !options._retry) {
      if (isRefreshing) {
        // If already refreshing, queue this request
        return new Promise((resolve, reject) => {
          failedQueue.push({ resolve, reject })
        })
          .then((token) => {
            return apiRequest(endpoint, { ...options, _retry: true })
          })
          .catch((err) => {
            throw err
          })
      }

      isRefreshing = true

      try {
        // Attempt to refresh the token
        const refreshToken = localStorage.getItem("refresh_token")

        if (!refreshToken) {
          throw new Error("No refresh token available")
        }

        const refreshResponse = await fetch(
          `${API_BASE_URL}/api/auth/refresh`,
          {
            method: "POST",
            headers: {
              "Content-Type": "application/json",
              Authorization: `Bearer ${getAuthToken()}`,
            },
            body: JSON.stringify({ refresh_token: refreshToken }),
          },
        )

        if (!refreshResponse.ok) {
          throw new Error("Token refresh failed")
        }

        const refreshData = await refreshResponse.json()

        // Update tokens
        if (refreshData.access_token) {
          localStorage.setItem("access_token", refreshData.access_token)
        }
        if (refreshData.refresh_token) {
          localStorage.setItem("refresh_token", refreshData.refresh_token)
        }

        isRefreshing = false
        processQueue(null, refreshData.access_token)

        // Retry the original request
        return apiRequest(endpoint, { ...options, _retry: true })
      } catch (refreshError) {
        isRefreshing = false
        processQueue(refreshError, null)

        // Clear tokens and redirect to login
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
        localStorage.removeItem("org_id")
        localStorage.removeItem("user_id")
        localStorage.removeItem("current_user")
        localStorage.removeItem("user_info")
        localStorage.removeItem("orgColors")

        // Redirect to login page
        window.location.href = "/"

        throw new Error("Session expired. Please login again.")
      }
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
    const response = await apiRequest("/api/register", {
      method: "POST",
      auth: false,
      body: JSON.stringify(data),
    })

    // Save org_id for future requests (handle both org_id and organization_id)
    const orgId = response.org_id || response.organization_id
    if (orgId) {
      localStorage.setItem("org_id", orgId)
      console.log("Organization ID saved:", orgId)
    }

    // Save user_id if provided
    if (response.user_id) {
      localStorage.setItem("user_id", response.user_id)
      console.log("User ID saved:", response.user_id)
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
    const response = await apiRequest("/api/login", {
      method: "POST",
      auth: false,
      body: JSON.stringify(credentials),
    })

    // Save tokens
    if (response.access_token) {
      localStorage.setItem("access_token", response.access_token)
      console.log("Access token saved to localStorage")
    }
    if (response.refresh_token) {
      localStorage.setItem("refresh_token", response.refresh_token)
      console.log("Refresh token saved to localStorage")
    }

    // Try to get user info immediately after login to obtain org_id
    try {
      const userInfo = await authAPI.getCurrentUser()
      console.log("User info retrieved:", userInfo)
    } catch (err) {
      console.log("Could not fetch user info immediately after login:", err)
    }

    return response
  },

  /**
   * Refresh JWT token
   * @returns {Promise<{access_token: string, refresh_token: string, expires_in: number, token_type: string}>}
   */
  refreshToken: async () => {
    const refreshToken = localStorage.getItem("refresh_token")

    const response = await apiRequest("/api/auth/refresh", {
      method: "POST",
      body: JSON.stringify({ refresh_token: refreshToken }),
    })

    // Update tokens
    if (response.access_token) {
      localStorage.setItem("access_token", response.access_token)
      console.log("Access token refreshed")
    }
    if (response.refresh_token) {
      localStorage.setItem("refresh_token", response.refresh_token)
      console.log("Refresh token updated")
    }

    return response
  },

  /**
   * Logout current user
   * @returns {Promise<{message: string}>}
   */
  logout: async () => {
    const response = await apiRequest("/api/auth/logout", {
      method: "POST",
    })

    // Clear tokens and user data
    localStorage.removeItem("access_token")
    localStorage.removeItem("refresh_token")
    localStorage.removeItem("org_id")
    localStorage.removeItem("user_id")
    localStorage.removeItem("current_user")
    localStorage.removeItem("user_info")
    localStorage.removeItem("orgColors")

    console.log("User logged out, all tokens and data cleared")

    return response
  },

  /**
   * Get current authenticated user info
   * @returns {Promise<{user: Object, claims: Object}>}
   */
  getCurrentUser: async () => {
    const response = await apiRequest("/api/auth/me", {
      method: "GET",
    })

    // Cache user info (response is the user object directly)
    localStorage.setItem("current_user", JSON.stringify(response))

    // Handle nested structure - response may have user/claims nested or be flat
    const userData = response.user || response

    // Save organization_id and user_id
    if (userData.organization_id) {
      localStorage.setItem("org_id", userData.organization_id)
      console.log(
        "Organization ID saved from user info:",
        userData.organization_id,
      )
    }
    if (userData.id) {
      localStorage.setItem("user_id", userData.id)
      console.log("User ID saved:", userData.id)
    }

    return response
  },
}

// ============================================================================
// PROFILE API
// ============================================================================

export const profileAPI = {
  /**
   * Get current user's profile
   * @returns {Promise<{message: string, data: Object}>}
   */
  getProfile: async () => {
    return apiRequest("/api/auth/profile", {
      method: "GET",
    })
  },

  /**
   * Change user password
   * @param {Object} data
   * @param {string} data.old_password - Current password
   * @param {string} data.new_password - New password
   * @returns {Promise<{message: string}>}
   */
  changePassword: async (data) => {
    return apiRequest("/api/auth/profile/changepassword", {
      method: "POST",
      body: JSON.stringify(data),
    })
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
    return apiRequest(`/api/${orgId}/staffing`, {
      method: "GET",
    })
  },

  /**
   * Create a new employee/user (delegate)
   * @param {Object} data - Employee data
   * @param {string} data.email - Employee email
   * @param {string} data.full_name - Employee full name
   * @param {string} data.role - Employee role
   * @param {number} data.salary_per_hour - Salary per hour
   * @returns {Promise<{user_id: string, message: string}>}
   */
  createEmployee: async (data) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/staffing`, {
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
    return apiRequest(`/api/${orgId}/staffing/employees`, {
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
    return apiRequest(`/api/${orgId}/staffing/employees/${employeeId}`, {
      method: "GET",
    })
  },

  /**
   * Layoff an employee
   * @param {string} employeeId - Employee UUID
   * @returns {Promise<{employee_id: string, message: string}>}
   */
  layoffEmployee: async (employeeId) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/staffing/employees/${employeeId}/layoff`, {
      method: "DELETE",
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

    return apiRequest(`/api/${orgId}/staffing/upload`, {
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
    return apiRequest(
      `/api/${orgId}/staffing/employees/${employeeId}/requests`,
      {
        method: "GET",
      },
    )
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
      `/api/${orgId}/staffing/employees/${employeeId}/requests/approve`,
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
   * @param {string} reason - Optional reason for declining
   * @returns {Promise<{request_id: string, message: string}>}
   */
  declineRequest: async (employeeId, requestId, reason = "") => {
    const orgId = getOrgId()
    return apiRequest(
      `/api/${orgId}/staffing/employees/${employeeId}/requests/decline`,
      {
        method: "POST",
        body: JSON.stringify({ request_id: requestId, reason }),
      },
    )
  },
}

// ============================================================================
// ROLES API
// ============================================================================

export const rolesAPI = {
  /**
   * Get all roles for the organization
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAll: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/roles`, {
      method: "GET",
    })
  },

  /**
   * Get specific role details
   * @param {string} roleName - Role name
   * @returns {Promise<{data: Object, message: string}>}
   */
  getRole: async (roleName) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/roles/${roleName}`, {
      method: "GET",
    })
  },

  /**
   * Create a new role
   * @param {Object} data - Role data
   * @param {string} data.role - Role name
   * @param {number} data.min_needed_per_shift - Minimum needed per shift
   * @param {number} data.items_per_role_per_hour - Items per role per hour (if need_for_demand is true)
   * @param {boolean} data.need_for_demand - Whether role needs demand calculation
   * @param {boolean} data.independent - Whether role is independent
   * @returns {Promise<{data: Object, message: string}>}
   */
  createRole: async (data) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/roles`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  },

  /**
   * Update an existing role
   * @param {string} roleName - Role name
   * @param {Object} data - Updated role data
   * @returns {Promise<{data: Object, message: string}>}
   */
  updateRole: async (roleName, data) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/roles/${roleName}`, {
      method: "PUT",
      body: JSON.stringify(data),
    })
  },

  /**
   * Delete a role
   * @param {string} roleName - Role name
   * @returns {Promise<{message: string}>}
   */
  deleteRole: async (roleName) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/roles/${roleName}`, {
      method: "DELETE",
    })
  },
}

// ============================================================================
// RULES API
// ============================================================================

export const rulesAPI = {
  /**
   * Get organization's scheduling rules and operating hours
   * @returns {Promise<{data: Object, message: string}>}
   */
  getRules: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/rules`, {
      method: "GET",
    })
  },

  /**
   * Create or update organization's scheduling rules
   * @param {Object} data - Rules data
   * @returns {Promise<{data: Object, message: string}>}
   */
  saveRules: async (data) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/rules`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  },
}

// ============================================================================
// ORDERS API
// ============================================================================

export const ordersAPI = {
  /**
   * Get order insights and analytics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getOrderInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/orders`, {
      method: "GET",
    })
  },

  /**
   * Get all orders for the organization
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAllOrders: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/orders/all`, {
      method: "GET",
    })
  },

  /**
   * Get orders from the last 7 days
   * @returns {Promise<{data: Array, message: string}>}
   */
  getOrdersWeek: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/orders/week`, {
      method: "GET",
    })
  },

  /**
   * Get orders from today
   * @returns {Promise<{data: Array, message: string}>}
   */
  getOrdersToday: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/orders/today`, {
      method: "GET",
    })
  },

  /**
   * Upload orders CSV file
   * @param {File} file - CSV file with orders data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadOrdersCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/orders/upload/orders`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },

  /**
   * Upload order items CSV file
   * @param {File} file - CSV file with order items data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadOrderItemsCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/orders/upload/items`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },
}

// ============================================================================
// PREFERENCES API
// ============================================================================

export const preferencesAPI = {
  /**
   * Get current user's preferences
   * @returns {Promise<{data: Object, message: string}>}
   */
  getPreferences: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/preferences`, {
      method: "GET",
    })
  },

  /**
   * Update current user's preferences
   * @param {Object} data - Preferences data
   * @param {Array} data.preferences - Array of day preferences
   * @param {Array} data.user_roles - Array of role names
   * @param {number} data.max_hours_per_week - Maximum hours per week
   * @param {number} data.preferred_hours_per_week - Preferred hours per week
   * @param {number} data.max_consec_slots - Maximum consecutive slots
   * @returns {Promise<{message: string}>}
   */
  savePreferences: async (data) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/preferences`, {
      method: "POST",
      body: JSON.stringify(data),
    })
  },
}

// ============================================================================
// INSIGHTS API
// ============================================================================

export const insightsAPI = {
  /**
   * Get dashboard insights and statistics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/insights`, {
      method: "GET",
    })
  },
}

// ============================================================================
// DELIVERIES API
// ============================================================================

export const deliveriesAPI = {
  /**
   * Get delivery insights and analytics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getDeliveryInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/deliveries`, {
      method: "GET",
    })
  },

  /**
   * Get all deliveries for the organization
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAllDeliveries: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/deliveries/all`, {
      method: "GET",
    })
  },

  /**
   * Get deliveries from the last 7 days
   * @returns {Promise<{data: Array, message: string}>}
   */
  getDeliveriesWeek: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/deliveries/week`, {
      method: "GET",
    })
  },

  /**
   * Get deliveries from today
   * @returns {Promise<{data: Array, message: string}>}
   */
  getDeliveriesToday: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/deliveries/today`, {
      method: "GET",
    })
  },

  /**
   * Upload deliveries CSV file
   * @param {File} file - CSV file with deliveries data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadDeliveriesCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/deliveries/upload`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },
}

// ============================================================================
// ITEMS API
// ============================================================================

export const itemsAPI = {
  /**
   * Get item insights and analytics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getItemInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/items`, {
      method: "GET",
    })
  },

  /**
   * Get all items for the organization
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAllItems: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/items/all`, {
      method: "GET",
    })
  },

  /**
   * Upload items CSV file
   * @param {File} file - CSV file with items data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadItemsCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/items/upload`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },
}

// ============================================================================
// CAMPAIGNS API
// ============================================================================

export const campaignsAPI = {
  /**
   * Get campaign insights and analytics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getCampaignInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/campaigns`, {
      method: "GET",
    })
  },

  /**
   * Get all campaigns for the organization
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAllCampaigns: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/campaigns/all`, {
      method: "GET",
    })
  },

  /**
   * Get campaigns from the last 7 days
   * @returns {Promise<{data: Array, message: string}>}
   */
  getCampaignsWeek: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/campaigns/week`, {
      method: "GET",
    })
  },

  /**
   * Upload campaigns CSV file
   * @param {File} file - CSV file with campaigns data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadCampaignsCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/campaigns/upload`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },
    recommendCampaigns: async (params) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/campaigns/recommend`, {
      method: "POST",
      body: JSON.stringify(params),
    })
  },
    submitCampaignFeedback: async (feedback) => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/campaigns/feedback`, {
      method: "POST",
      body: JSON.stringify(feedback),
    })
  },
  /**
   * Upload campaign items CSV file
   * @param {File} file - CSV file with campaign items data
   * @returns {Promise<{total_rows: number, success_count: number, error_count: number, message: string}>}
   */
  uploadCampaignItemsCSV: async (file) => {
    const orgId = getOrgId()
    const formData = new FormData()
    formData.append("file", file)

    return apiRequest(`/api/${orgId}/campaigns/upload/items`, {
      method: "POST",
      contentType: null,
      body: formData,
    })
  },
}

// ============================================================================
// DASHBOARD/SURGE API
// ============================================================================

export const dashboardAPI = {
  /**
   * Get surge pricing insights and analytics
   * @returns {Promise<{data: Array, message: string}>}
   */
  getSurgeInsights: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/dashboard/surge`, {
      method: "GET",
    })
  },

  /**
   * Get all surge pricing data
   * @returns {Promise<{data: Array, message: string}>}
   */
  getAllSurge: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/dashboard/surge/all`, {
      method: "GET",
    })
  },

  /**
   * Get surge pricing data from the last 7 days
   * @returns {Promise<{data: Array, message: string}>}
   */
  getSurgeWeek: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/dashboard/surge/week`, {
      method: "GET",
    })
  },

  /**
   * Get demand heatmap predictions
   * @returns {Promise<{data: Object, message: string}>}
   */
  getDemandHeatmap: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/dashboard/demand`, {
      method: "GET",
    })
  },

  /**
   * Generate demand predictions using ML service
   * @returns {Promise<{message: string}>}
   */
  generateDemandPrediction: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}/dashboard/demand/predict`, {
      method: "POST",
    })
  },
}

// ============================================================================
// ORGANIZATION API
// ============================================================================

export const organizationAPI = {
  /**
   * Get organization profile including colors
   * @returns {Promise<{data: Object, message: string}>}
   */
  getProfile: async () => {
    const orgId = getOrgId()
    return apiRequest(`/api/${orgId}`, {
      method: "GET",
    })
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
  profile: profileAPI,
  organization: organizationAPI,
  staffing: staffingAPI,
  requests: requestsAPI,
  roles: rolesAPI,
  rules: rulesAPI,
  preferences: preferencesAPI,
  insights: insightsAPI,
  orders: ordersAPI,
  deliveries: deliveriesAPI,
  items: itemsAPI,
  campaigns: campaignsAPI,
  dashboard: dashboardAPI,
  health: healthAPI,
}

export default api
