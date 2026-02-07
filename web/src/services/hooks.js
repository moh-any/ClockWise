import { useState, useEffect } from "react"
import api from "./api"

/**
 * Custom hook for managing API calls with loading and error states
 * @param {Function} apiFunction - The API function to call
 * @param {Array} dependencies - Dependencies array for useEffect (optional)
 * @param {boolean} immediate - Whether to call API immediately on mount (default: true)
 * @returns {Object} - {data, loading, error, refetch, execute}
 */
export const useAPI = (apiFunction, dependencies = [], immediate = true) => {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(immediate)
  const [error, setError] = useState(null)

  const execute = async (...args) => {
    try {
      setLoading(true)
      setError(null)
      const result = await apiFunction(...args)
      setData(result)
      return result
    } catch (err) {
      setError(err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const refetch = () => execute()

  useEffect(() => {
    if (immediate) {
      execute()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies)

  return { data, loading, error, refetch, execute }
}

/**
 * Hook for authentication operations
 */
export const useAuth = () => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)
  const [authenticated, setAuthenticated] = useState(false)

  useEffect(() => {
    // Check if user is already logged in
    const checkAuth = async () => {
      try {
        const token = localStorage.getItem("access_token")
        if (token) {
          const userData = await api.auth.getCurrentUser()
          setUser(userData.user)
          setAuthenticated(true)
        }
      } catch (error) {
        console.error("Auth check failed:", error)
        localStorage.removeItem("access_token")
        localStorage.removeItem("refresh_token")
      } finally {
        setLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email, password) => {
    try {
      setLoading(true)
      await api.auth.login({ email, password })
      const userData = await api.auth.getCurrentUser()
      setUser(userData.user)
      setAuthenticated(true)
      return userData
    } catch (error) {
      setAuthenticated(false)
      throw error
    } finally {
      setLoading(false)
    }
  }

  const logout = async () => {
    try {
      await api.auth.logout()
    } catch (error) {
      console.error("Logout error:", error)
    } finally {
      setUser(null)
      setAuthenticated(false)
    }
  }

  const register = async (orgData) => {
    try {
      setLoading(true)
      const response = await api.auth.register(orgData)
      return response
    } catch (error) {
      throw error
    } finally {
      setLoading(false)
    }
  }

  return {
    user,
    loading,
    authenticated,
    login,
    logout,
    register,
  }
}

/**
 * Hook for staffing operations
 */
export const useStaffing = () => {
  const {
    data: summary,
    loading: summaryLoading,
    error: summaryError,
    refetch: refetchSummary,
  } = useAPI(api.staffing.getStaffingSummary, [], true)

  const {
    data: employees,
    loading: employeesLoading,
    error: employeesError,
    refetch: refetchEmployees,
  } = useAPI(api.staffing.getAllEmployees, [], true)

  const createEmployee = async (employeeData) => {
    try {
      const result = await api.staffing.createEmployee(employeeData)
      refetchSummary()
      refetchEmployees()
      return result
    } catch (error) {
      throw error
    }
  }

  const layoffEmployee = async (employeeId, reason) => {
    try {
      const result = await api.staffing.layoffEmployee(employeeId, reason)
      refetchSummary()
      refetchEmployees()
      return result
    } catch (error) {
      throw error
    }
  }

  const bulkUpload = async (file) => {
    try {
      const result = await api.staffing.bulkUploadEmployees(file)
      refetchSummary()
      refetchEmployees()
      return result
    } catch (error) {
      throw error
    }
  }

  return {
    summary,
    summaryLoading,
    summaryError,
    employees,
    employeesLoading,
    employeesError,
    createEmployee,
    layoffEmployee,
    bulkUpload,
    refetchSummary,
    refetchEmployees,
  }
}

/**
 * Hook for employee requests operations
 */
export const useRequests = (employeeId) => {
  const {
    data: requests,
    loading,
    error,
    refetch,
  } = useAPI(
    () => api.requests.getEmployeeRequests(employeeId),
    [employeeId],
    !!employeeId,
  )

  const approveRequest = async (requestId) => {
    try {
      const result = await api.requests.approveRequest(employeeId, requestId)
      refetch()
      return result
    } catch (error) {
      throw error
    }
  }

  const declineRequest = async (requestId) => {
    try {
      const result = await api.requests.declineRequest(employeeId, requestId)
      refetch()
      return result
    } catch (error) {
      throw error
    }
  }

  return {
    requests,
    loading,
    error,
    approveRequest,
    declineRequest,
    refetch,
  }
}

export default {
  useAPI,
  useAuth,
  useStaffing,
  useRequests,
}
