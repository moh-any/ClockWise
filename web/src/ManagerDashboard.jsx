import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import "./ManagerDashboard.css"
import api from "./services/api"

// Import SVG icons
import HomeIcon from "./Icons/Home_Icon.svg"
import ScheduleIcon from "./Icons/Schedule_Icon.svg"
import EmployeeIcon from "./Icons/Employee_Icon.svg"
import SettingsIcon from "./Icons/Settings_Icon.svg"
import InfoIcon from "./Icons/Info_Icon.svg"
import LightModeIcon from "./Icons/Light-Mode-Icon.svg"
import DarkModeIcon from "./Icons/Dark-Mode-Icon.svg"
import MissedTargetIcon from "./Icons/Missed-Target-Icon.svg"

function ManagerDashboard() {
  const navigate = useNavigate()
  const [mgrActiveTab, setMgrActiveTab] = useState("home")
  const [mgrSidebarCollapsed, setMgrSidebarCollapsed] = useState(false)
  const [mgrDarkMode, setMgrDarkMode] = useState(() => {
    const saved = localStorage.getItem("mgrDarkMode")
    return saved === "true"
  })
  const [mgrPrimaryColor, setMgrPrimaryColor] = useState("#4A90E2")
  const [mgrSecondaryColor, setMgrSecondaryColor] = useState("#7B68EE")
  const [mgrAccentColor, setMgrAccentColor] = useState("#FF6B6B")

  const [mgrLoading, setMgrLoading] = useState(true)
  const [mgrError, setMgrError] = useState("")

  // User profile state
  const [mgrCurrentUser, setMgrCurrentUser] = useState(null)
  const [mgrProfileData, setMgrProfileData] = useState(null)
  const [mgrPasswordForm, setMgrPasswordForm] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  })
  const [mgrPasswordLoading, setMgrPasswordLoading] = useState(false)
  const [mgrPasswordError, setMgrPasswordError] = useState("")
  const [mgrPasswordSuccess, setMgrPasswordSuccess] = useState("")

  // Manager-specific state - Insights
  const [mgrInsights, setMgrInsights] = useState([])

  // Manager-specific state - Staffing
  const [mgrEmployees, setMgrEmployees] = useState([])
  const [mgrTotalEmployees, setMgrTotalEmployees] = useState(0)
  const [mgrEmployeesByRole, setMgrEmployeesByRole] = useState({})
  const [mgrStaffingLoading, setMgrStaffingLoading] = useState(false)
  const [mgrStaffingError, setMgrStaffingError] = useState("")
  const [mgrStaffingSuccess, setMgrStaffingSuccess] = useState("")

  // Delegate User Form
  const [mgrDelegateForm, setMgrDelegateForm] = useState({
    full_name: "",
    email: "",
    role: "employee",
    salary_per_hour: "",
  })
  const [mgrDelegateLoading, setMgrDelegateLoading] = useState(false)

  // Orders state
  const [mgrOrders, setMgrOrders] = useState([])
  const [mgrOrdersLoading, setMgrOrdersLoading] = useState(false)
  const [mgrOrdersError, setMgrOrdersError] = useState("")
  const [mgrOrdersFilter, setMgrOrdersFilter] = useState("all") // all, today, week

  // Rules state (for configuration)
  const [mgrRules, setMgrRules] = useState(null)
  const [mgrRulesLoading, setMgrRulesLoading] = useState(false)
  const [mgrRulesError, setMgrRulesError] = useState("")
  const [mgrRulesSuccess, setMgrRulesSuccess] = useState("")

  const mgrNavigationItems = [
    { id: "home", label: "Dashboard", icon: HomeIcon },
    { id: "staffing", label: "Staffing", icon: EmployeeIcon },
    { id: "schedule", label: "Schedule", icon: ScheduleIcon },
    { id: "orders", label: "Orders", icon: InfoIcon },
    { id: "rules", label: "Rules", icon: SettingsIcon },
    { id: "profile", label: "Profile", icon: InfoIcon },
  ]

  const mgrGetContrastColor = (hexColor) => {
    const hex = hexColor.replace("#", "")
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5 ? "#000000" : "#FFFFFF"
  }

  useEffect(() => {
    const savedColors = localStorage.getItem("orgColors")
    if (savedColors) {
      const colors = JSON.parse(savedColors)
      const primary = colors[0] || mgrPrimaryColor
      const secondary = colors[1] || mgrSecondaryColor
      const accent = colors[2] || mgrAccentColor

      setMgrPrimaryColor(primary)
      setMgrSecondaryColor(secondary)
      setMgrAccentColor(accent)

      // Set scoped CSS variables for Manager Dashboard
      const mgrDashboard = document.querySelector(".manager-dashboard-wrapper")
      if (mgrDashboard) {
        mgrDashboard.style.setProperty("--mgr-color-primary", primary)
        mgrDashboard.style.setProperty("--mgr-color-secondary", secondary)
        mgrDashboard.style.setProperty("--mgr-color-accent", accent)
        mgrDashboard.style.setProperty(
          "--mgr-primary-contrast",
          mgrGetContrastColor(primary),
        )
        mgrDashboard.style.setProperty(
          "--mgr-secondary-contrast",
          mgrGetContrastColor(secondary),
        )
        mgrDashboard.style.setProperty(
          "--mgr-accent-contrast",
          mgrGetContrastColor(accent),
        )
      }
    }
  }, [])

  useEffect(() => {
    // Apply dark mode class to manager dashboard only
    const mgrDashboard = document.querySelector(".manager-dashboard-wrapper")
    if (mgrDashboard) {
      if (mgrDarkMode) {
        mgrDashboard.classList.add("dark-mode")
      } else {
        mgrDashboard.classList.remove("dark-mode")
      }
    }
  }, [mgrDarkMode])

  useEffect(() => {
    mgrFetchDashboardData()
    mgrFetchCurrentUser()
  }, [])

  const mgrFetchCurrentUser = async () => {
    try {
      // Try to get from cache first
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        setMgrCurrentUser(parsedUser)
      }

      // Fetch fresh data from API
      const userData = await api.auth.getCurrentUser()
      setMgrCurrentUser(userData)
    } catch (err) {
      console.error("Error fetching user data:", err)
      // Still try to use cached data
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        setMgrCurrentUser(parsedUser)
      }
    }
  }

  const mgrFetchDashboardData = async () => {
    try {
      setMgrLoading(true)
      setMgrError("")

      // Fetch insights data
      try {
        const insightsResponse = await api.insights.getInsights()
        if (insightsResponse && insightsResponse.data) {
          setMgrInsights(insightsResponse.data)
        }
      } catch (err) {
        console.error("Error fetching insights:", err)
      }

      // Fetch profile data
      try {
        const profile = await api.profile.getProfile()
        if (profile && profile.data) {
          setMgrProfileData(profile.data)
        }
      } catch (err) {
        console.error("Error fetching profile:", err)
      }

      // Fetch staffing data
      try {
        const staffingResponse = await api.staffing.getStaffingSummary()
        if (staffingResponse && staffingResponse.data) {
          setMgrEmployees(staffingResponse.data.employees || [])
          setMgrTotalEmployees(staffingResponse.data.total_employees || 0)
          setMgrEmployeesByRole(staffingResponse.data.by_role || {})
        }
      } catch (err) {
        console.error("Error fetching staffing:", err)
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err)
      setMgrError(err.message || "Failed to load dashboard data")
    } finally {
      setMgrLoading(false)
    }
  }

  const mgrHandleChangePassword = async (e) => {
    e.preventDefault()
    setMgrPasswordError("")
    setMgrPasswordSuccess("")

    // Validate passwords match
    if (mgrPasswordForm.new_password !== mgrPasswordForm.confirm_password) {
      setMgrPasswordError("New passwords do not match")
      return
    }

    // Validate password length
    if (mgrPasswordForm.new_password.length < 8) {
      setMgrPasswordError("New password must be at least 8 characters")
      return
    }

    setMgrPasswordLoading(true)

    try {
      await api.profile.changePassword({
        old_password: mgrPasswordForm.old_password,
        new_password: mgrPasswordForm.new_password,
      })

      setMgrPasswordSuccess("Password changed successfully!")
      setMgrPasswordForm({
        old_password: "",
        new_password: "",
        confirm_password: "",
      })

      setTimeout(() => {
        setMgrPasswordSuccess("")
      }, 3000)
    } catch (err) {
      setMgrPasswordError(err.message || "Failed to change password")
    } finally {
      setMgrPasswordLoading(false)
    }
  }

  const mgrToggleDarkMode = () => {
    const newMode = !mgrDarkMode
    setMgrDarkMode(newMode)
    localStorage.setItem("mgrDarkMode", newMode.toString())
  }

  const mgrHandleLogout = async () => {
    try {
      await api.auth.logout()
      navigate("/")
    } catch (err) {
      console.error("Logout error:", err)
      // Still navigate to home even if API call fails
      navigate("/")
    }
  }

  const mgrFetchStaffing = async () => {
    setMgrStaffingLoading(true)
    setMgrStaffingError("")

    try {
      const staffingResponse = await api.staffing.getStaffingSummary()
      if (staffingResponse && staffingResponse.data) {
        setMgrEmployees(staffingResponse.data.employees || [])
        setMgrTotalEmployees(staffingResponse.data.total_employees || 0)
        setMgrEmployeesByRole(staffingResponse.data.by_role || {})
      }
    } catch (err) {
      setMgrStaffingError(err.message || "Failed to load staffing data")
    } finally {
      setMgrStaffingLoading(false)
    }
  }

  const mgrHandleDelegateUser = async (e) => {
    e.preventDefault()
    setMgrDelegateLoading(true)
    setMgrStaffingError("")
    setMgrStaffingSuccess("")

    try {
      await api.staffing.createEmployee({
        full_name: mgrDelegateForm.full_name,
        email: mgrDelegateForm.email,
        role: mgrDelegateForm.role,
        salary_per_hour: parseFloat(mgrDelegateForm.salary_per_hour),
      })

      setMgrStaffingSuccess("User delegated successfully! Email sent.")
      setMgrDelegateForm({
        full_name: "",
        email: "",
        role: "employee",
        salary_per_hour: "",
      })

      // Refresh staffing data
      mgrFetchStaffing()

      setTimeout(() => {
        setMgrStaffingSuccess("")
      }, 3000)
    } catch (err) {
      setMgrStaffingError(err.message || "Failed to delegate user")
    } finally {
      setMgrDelegateLoading(false)
    }
  }

  const mgrFetchOrders = async (filter = "all") => {
    setMgrOrdersLoading(true)
    setMgrOrdersError("")

    try {
      let ordersResponse
      if (filter === "today") {
        ordersResponse = await api.orders.getOrdersToday()
      } else if (filter === "week") {
        ordersResponse = await api.orders.getOrdersWeek()
      } else {
        ordersResponse = await api.orders.getAllOrders()
      }

      if (ordersResponse && ordersResponse.data) {
        setMgrOrders(ordersResponse.data)
      }
    } catch (err) {
      setMgrOrdersError(err.message || "Failed to load orders")
    } finally {
      setMgrOrdersLoading(false)
    }
  }

  const mgrFetchRules = async () => {
    setMgrRulesLoading(true)
    setMgrRulesError("")

    try {
      const rulesResponse = await api.rules.getRules()
      if (rulesResponse && rulesResponse.data) {
        setMgrRules(rulesResponse.data)
      }
    } catch (err) {
      setMgrRulesError(err.message || "Failed to load rules")
    } finally {
      setMgrRulesLoading(false)
    }
  }

  const mgrHandleSaveRules = async () => {
    setMgrRulesLoading(true)
    setMgrRulesError("")
    setMgrRulesSuccess("")

    try {
      await api.rules.saveRules(mgrRules)
      setMgrRulesSuccess("Rules saved successfully!")
      setTimeout(() => {
        setMgrRulesSuccess("")
      }, 3000)
    } catch (err) {
      setMgrRulesError(err.message || "Failed to save rules")
    } finally {
      setMgrRulesLoading(false)
    }
  }

  useEffect(() => {
    if (mgrActiveTab === "staffing") {
      mgrFetchStaffing()
    } else if (mgrActiveTab === "orders") {
      mgrFetchOrders(mgrOrdersFilter)
    } else if (mgrActiveTab === "rules") {
      mgrFetchRules()
    }
  }, [mgrActiveTab])

  useEffect(() => {
    if (mgrActiveTab === "orders") {
      mgrFetchOrders(mgrOrdersFilter)
    }
  }, [mgrOrdersFilter])

  const mgrRenderSkeletonLoader = () => (
    <div className="skeleton-loader">
      <div className="skeleton-card"></div>
      <div className="skeleton-card"></div>
      <div className="skeleton-card"></div>
    </div>
  )

  const mgrRenderHomeDashboard = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">
            Welcome Back,{" "}
            {mgrCurrentUser?.full_name?.split(" ")[0] || "Manager"}
          </h1>
          <p className="page-subtitle">Your management dashboard</p>
        </div>
      </div>

      {/* Profile Summary Cards */}
      {mgrProfileData && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Total Employees</div>
              <div className="kpi-value">{mgrTotalEmployees || "0"}</div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Hours Worked This Week</div>
              <div className="kpi-value">
                {mgrProfileData.hours_worked_this_week || "0"} hrs
              </div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Your Role</div>
              <div className="kpi-value">
                {mgrProfileData.user_role || "N/A"}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Insights Section */}
      {mgrInsights && mgrInsights.length > 0 && (
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">
              <img src={InfoIcon} alt="Insights" className="title-icon-svg" />
              Organization Insights
            </h2>
          </div>
          <div className="insights-grid">
            {mgrInsights.map((insight, index) => (
              <div key={index} className="insight-card">
                <h4 className="insight-title">{insight.title}</h4>
                <p className="insight-value">{insight.statistic}</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )

  const mgrRenderStaffing = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Staffing Management</h1>
          <p className="page-subtitle">
            Manage your team and delegate new users
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => mgrFetchStaffing()}
          disabled={mgrStaffingLoading}
        >
          {mgrStaffingLoading ? "Refreshing..." : "Refresh"}
        </button>
      </div>

      {mgrStaffingError && (
        <div
          className="alert alert-error"
          style={{ marginBottom: "var(--mgr-space-4)" }}
        >
          {mgrStaffingError}
        </div>
      )}

      {mgrStaffingSuccess && (
        <div
          className="alert alert-success"
          style={{ marginBottom: "var(--mgr-space-4)" }}
        >
          {mgrStaffingSuccess}
        </div>
      )}

      {/* Delegate New User Form */}
      <div className="section-wrapper">
        <div className="section-header">
          <h2 className="section-title">Delegate New User</h2>
        </div>
        <form onSubmit={mgrHandleDelegateUser} className="delegate-form">
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Full Name</label>
              <input
                type="text"
                className="form-input"
                value={mgrDelegateForm.full_name}
                onChange={(e) =>
                  setMgrDelegateForm({
                    ...mgrDelegateForm,
                    full_name: e.target.value,
                  })
                }
                required
              />
            </div>
            <div className="form-group">
              <label className="form-label">Email</label>
              <input
                type="email"
                className="form-input"
                value={mgrDelegateForm.email}
                onChange={(e) =>
                  setMgrDelegateForm({
                    ...mgrDelegateForm,
                    email: e.target.value,
                  })
                }
                required
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Role</label>
              <select
                className="form-input"
                value={mgrDelegateForm.role}
                onChange={(e) =>
                  setMgrDelegateForm({
                    ...mgrDelegateForm,
                    role: e.target.value,
                  })
                }
                required
              >
                <option value="employee">Employee</option>
                <option value="manager">Manager</option>
              </select>
            </div>
            <div className="form-group">
              <label className="form-label">Salary Per Hour</label>
              <input
                type="number"
                step="0.01"
                className="form-input"
                value={mgrDelegateForm.salary_per_hour}
                onChange={(e) =>
                  setMgrDelegateForm({
                    ...mgrDelegateForm,
                    salary_per_hour: e.target.value,
                  })
                }
                required
              />
            </div>
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={mgrDelegateLoading}
          >
            {mgrDelegateLoading ? "Delegating..." : "Delegate User"}
          </button>
        </form>
      </div>

      {/* Employees List */}
      <div
        className="section-wrapper"
        style={{ marginTop: "var(--mgr-space-6)" }}
      >
        <div className="section-header">
          <h2 className="section-title">Team Members ({mgrTotalEmployees})</h2>
        </div>

        {/* Employee Statistics */}
        <div
          className="kpi-grid"
          style={{ marginBottom: "var(--mgr-space-6)" }}
        >
          {Object.entries(mgrEmployeesByRole).map(([role, count]) => (
            <div key={role} className="kpi-card">
              <div className="kpi-content">
                <div className="kpi-label">{role}</div>
                <div className="kpi-value">{count}</div>
              </div>
            </div>
          ))}
        </div>

        {/* Employees Table */}
        {mgrEmployees.length > 0 ? (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Email</th>
                  <th>Role</th>
                  <th>Salary/Hr</th>
                  <th>Max Hrs/Week</th>
                  <th>On Call</th>
                </tr>
              </thead>
              <tbody>
                {mgrEmployees.map((employee) => (
                  <tr key={employee.id}>
                    <td>{employee.full_name}</td>
                    <td>{employee.email}</td>
                    <td>
                      <span className="badge badge-primary">
                        {employee.user_role}
                      </span>
                    </td>
                    <td>${employee.salary_per_hour || "N/A"}</td>
                    <td>{employee.max_hours_per_week || "N/A"}</td>
                    <td>{employee.on_call ? "Yes" : "No"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <img src={InfoIcon} alt="No Employees" className="empty-icon-svg" />
            <h3>No Employees Found</h3>
            <p>Start by delegating new team members</p>
          </div>
        )}
      </div>
    </div>
  )

  const mgrRenderOrders = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Orders Management</h1>
          <p className="page-subtitle">View and analyze orders</p>
        </div>
        <div style={{ display: "flex", gap: "var(--mgr-space-3)" }}>
          <select
            className="form-input"
            value={mgrOrdersFilter}
            onChange={(e) => setMgrOrdersFilter(e.target.value)}
            style={{ width: "150px" }}
          >
            <option value="all">All Orders</option>
            <option value="today">Today</option>
            <option value="week">This Week</option>
          </select>
          <button
            className="btn-primary"
            onClick={() => mgrFetchOrders(mgrOrdersFilter)}
            disabled={mgrOrdersLoading}
          >
            {mgrOrdersLoading ? "Loading..." : "Refresh"}
          </button>
        </div>
      </div>

      {mgrOrdersError && (
        <div
          className="alert alert-error"
          style={{ marginBottom: "var(--mgr-space-4)" }}
        >
          {mgrOrdersError}
        </div>
      )}

      <div className="section-wrapper">
        {mgrOrders.length > 0 ? (
          <div className="table-wrapper">
            <table className="data-table">
              <thead>
                <tr>
                  <th>Order ID</th>
                  <th>Date</th>
                  <th>Type</th>
                  <th>Status</th>
                  <th>Total</th>
                  <th>Discount</th>
                  <th>Rating</th>
                </tr>
              </thead>
              <tbody>
                {mgrOrders.map((order) => (
                  <tr key={order.order_id}>
                    <td>{order.order_id.substring(0, 8)}...</td>
                    <td>{new Date(order.create_time).toLocaleDateString()}</td>
                    <td>
                      <span className="badge badge-primary">
                        {order.order_type}
                      </span>
                    </td>
                    <td>{order.order_status}</td>
                    <td>${order.total_amount.toFixed(2)}</td>
                    <td>${order.discount_amount.toFixed(2)}</td>
                    <td>{order.rating || "N/A"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <img src={InfoIcon} alt="No Orders" className="empty-icon-svg" />
            <h3>No Orders Found</h3>
            <p>No orders available for the selected filter</p>
          </div>
        )}
      </div>
    </div>
  )

  const mgrRenderRules = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Rules Configuration</h1>
          <p className="page-subtitle">
            Manage scheduling and operational rules
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={mgrHandleSaveRules}
          disabled={mgrRulesLoading || !mgrRules}
        >
          {mgrRulesLoading ? "Saving..." : "Save Rules"}
        </button>
      </div>

      {mgrRulesError && (
        <div
          className="alert alert-error"
          style={{ marginBottom: "var(--mgr-space-4)" }}
        >
          {mgrRulesError}
        </div>
      )}

      {mgrRulesSuccess && (
        <div
          className="alert alert-success"
          style={{ marginBottom: "var(--mgr-space-4)" }}
        >
          {mgrRulesSuccess}
        </div>
      )}

      {mgrRules ? (
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">Shift Rules</h2>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Shift Hours</label>
              <input
                type="number"
                className="form-input"
                value={mgrRules.shift_max_hours || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    shift_max_hours: parseInt(e.target.value),
                  })
                }
              />
            </div>
            <div className="form-group">
              <label className="form-label">Min Shift Hours</label>
              <input
                type="number"
                className="form-input"
                value={mgrRules.shift_min_hours || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    shift_min_hours: parseInt(e.target.value),
                  })
                }
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Weekly Hours</label>
              <input
                type="number"
                className="form-input"
                value={mgrRules.max_weekly_hours || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    max_weekly_hours: parseInt(e.target.value),
                  })
                }
              />
            </div>
            <div className="form-group">
              <label className="form-label">Min Weekly Hours</label>
              <input
                type="number"
                className="form-input"
                value={mgrRules.min_weekly_hours || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    min_weekly_hours: parseInt(e.target.value),
                  })
                }
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Slot Length (Hours)</label>
              <input
                type="number"
                step="0.5"
                className="form-input"
                value={mgrRules.slot_len_hour || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    slot_len_hour: parseFloat(e.target.value),
                  })
                }
              />
            </div>
            <div className="form-group">
              <label className="form-label">Min Rest Slots</label>
              <input
                type="number"
                className="form-input"
                value={mgrRules.min_rest_slots || ""}
                onChange={(e) =>
                  setMgrRules({
                    ...mgrRules,
                    min_rest_slots: parseInt(e.target.value),
                  })
                }
              />
            </div>
          </div>
          <div className="form-row">
            <div className="form-group">
              <label className="checkbox-switch">
                <input
                  type="checkbox"
                  checked={mgrRules.fixed_shifts || false}
                  onChange={(e) =>
                    setMgrRules({ ...mgrRules, fixed_shifts: e.target.checked })
                  }
                />
                <span className="checkbox-text">Fixed Shifts</span>
              </label>
            </div>
            <div className="form-group">
              <label className="checkbox-switch">
                <input
                  type="checkbox"
                  checked={mgrRules.meet_all_demand || false}
                  onChange={(e) =>
                    setMgrRules({
                      ...mgrRules,
                      meet_all_demand: e.target.checked,
                    })
                  }
                />
                <span className="checkbox-text">Meet All Demand</span>
              </label>
            </div>
          </div>
        </div>
      ) : (
        <div className="empty-state">
          <img src={SettingsIcon} alt="No Rules" className="empty-icon-svg" />
          <h3>Loading Rules...</h3>
          <p>Please wait while we fetch the rules configuration</p>
        </div>
      )}
    </div>
  )

  const mgrRenderSchedule = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Schedule Management</h1>
          <p className="page-subtitle">View and manage team schedules</p>
        </div>
      </div>

      <div className="empty-state">
        <img src={ScheduleIcon} alt="Schedule" className="empty-icon-svg" />
        <h3>Schedule View Coming Soon</h3>
        <p>Manage team shifts and work calendar</p>
      </div>
    </div>
  )

  const mgrRenderProfile = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">My Profile</h1>
          <p className="page-subtitle">
            View and manage your profile information
          </p>
        </div>
      </div>

      <div className="section-wrapper">
        <div className="section-header">
          <h2 className="section-title">Profile Information</h2>
        </div>
        <div className="profile-info-grid">
          <div className="info-item">
            <div className="info-label">Full Name</div>
            <div className="info-value">
              {mgrCurrentUser?.full_name || mgrProfileData?.full_name || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Email</div>
            <div className="info-value">
              {mgrCurrentUser?.email || mgrProfileData?.email || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Role</div>
            <div className="info-value">
              {mgrCurrentUser?.user_role || mgrProfileData?.user_role || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Organization</div>
            <div className="info-value">
              {mgrProfileData?.organization || "N/A"}
            </div>
          </div>
          {(mgrCurrentUser?.salary_per_hour ||
            mgrProfileData?.salary_per_hour) && (
            <div className="info-item">
              <div className="info-label">Salary Per Hour</div>
              <div className="info-value">
                $
                {mgrCurrentUser?.salary_per_hour ||
                  mgrProfileData?.salary_per_hour}
              </div>
            </div>
          )}
          <div className="info-item">
            <div className="info-label">Member Since</div>
            <div className="info-value">
              {mgrProfileData?.created_at
                ? new Date(mgrProfileData.created_at).toLocaleDateString()
                : "N/A"}
            </div>
          </div>
        </div>
      </div>

      <div
        className="section-wrapper"
        style={{ marginTop: "var(--mgr-space-6)" }}
      >
        <div className="section-header">
          <h2 className="section-title">Change Password</h2>
        </div>
        <form onSubmit={mgrHandleChangePassword} className="password-form">
          {mgrPasswordError && (
            <div className="alert alert-error">{mgrPasswordError}</div>
          )}
          {mgrPasswordSuccess && (
            <div className="alert alert-success">{mgrPasswordSuccess}</div>
          )}
          <div className="form-group">
            <label className="form-label">Current Password</label>
            <input
              type="password"
              className="form-input"
              value={mgrPasswordForm.old_password}
              onChange={(e) =>
                setMgrPasswordForm({
                  ...mgrPasswordForm,
                  old_password: e.target.value,
                })
              }
              required
            />
          </div>
          <div className="form-group">
            <label className="form-label">New Password</label>
            <input
              type="password"
              className="form-input"
              value={mgrPasswordForm.new_password}
              onChange={(e) =>
                setMgrPasswordForm({
                  ...mgrPasswordForm,
                  new_password: e.target.value,
                })
              }
              required
              minLength={8}
            />
          </div>
          <div className="form-group">
            <label className="form-label">Confirm New Password</label>
            <input
              type="password"
              className="form-input"
              value={mgrPasswordForm.confirm_password}
              onChange={(e) =>
                setMgrPasswordForm({
                  ...mgrPasswordForm,
                  confirm_password: e.target.value,
                })
              }
              required
              minLength={8}
            />
          </div>
          <button
            type="submit"
            className="btn-primary"
            disabled={mgrPasswordLoading}
          >
            {mgrPasswordLoading ? "Changing..." : "Change Password"}
          </button>
        </form>
      </div>
    </div>
  )

  return (
    <div
      className={`manager-dashboard-wrapper ${mgrDarkMode ? "dark-mode" : ""}`}
    >
      {/* Premium Sidebar */}
      <aside className={`sidebar ${mgrSidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          <div className="logo-wrapper">
            {mgrSidebarCollapsed ? (
              <svg
                xmlns="http://www.w3.org/2000/svg"
                width="40px"
                height="40px"
                className="logo-svg"
                viewBox="1100 1 1240 1"
              >
                <path d="M1664.5-602.5c-31 1-59.9 5-63.9 8.4-4.5 4-7.3 19.8-7.3 44.7 0 44.6 7.3 55.9 37.3 55.9h19.2v27.7c0 30.5.6 30-42.4 37.3-32.2 5.6-84.7 24.3-127.1 45.2-106.8 53.7-204 162.1-250.3 279.7-25.4 65-33.9 122.6-30.5 208.4 2.8 77.4 10.2 112.5 36.7 178.6 55.4 138.4 186.5 254.8 337.3 299.4 69 21 176.9 25.5 246.4 11.3 175.1-35 330-166 389.2-330 70.7-193.2 26.6-399.4-117-549.1-37.8-39.6-37.2-35.6-15.7-66.1 1.1-.6 7.9 1.7 16.4 5 12.4 5.7 16.3 5.2 26.5-3.9 18-16.4 27.7-37.8 21.5-49.1-6.2-10.2-105.7-83.1-114.1-83.1-8.5 0-43.6 40.7-43.6 50.9 0 5 5.1 14 11.3 19.7 10.8 10.2 10.8 10.2 0 25.5l-11.3 15.8-38.4-18.7a502 502 0 0 0-140.7-45.2l-29.9-4v-27c0-26.6.6-26.6 20.3-30 31.7-5 36.2-11.9 36.2-52.5 0-28.9-2.3-38.5-11.3-47.5-11.9-11.9-9-11.9-154.8-7.3m169 264.4c83 23.1 170 80.8 223.7 148 64.4 81.4 95.4 169 95.4 270 0 72.4-13.5 128.9-48.5 199.5-45.8 93.8-144.1 179.1-243.6 213-55.9 18.7-119.2 27.7-170 23.8C1402.3 493 1214.7 206 1310.2-64.1c22.6-64.4 48-104 102.3-158.2 66.7-66.7 128.8-101.1 217.5-121 49.2-10.6 154.8-8.4 203.4 5.2" />
                <g className="inner1">
                  <path d="M1635.7-295.2a387 387 0 0 0-301.2 356 386.3 386.3 0 0 0 366.1 404.5c70.7 3.4 123.8-7.9 191-40.7 41.8-20.9 61.6-35 96-69.5 68.4-68.3 102.9-137.3 114.2-228.2 14.7-120.4-23.2-226.6-112.4-315.3-80.8-80.2-162.2-113.6-274-112.4-31.7.5-67.3 2.8-79.7 5.6m87 274.6c0 28.8 1.1 52.6 2.2 52.6.6 0 21-6.3 45.2-13.6C1807 7 1813.7 6 1813.7 13.9c0 14.1-91.6 326.5-97.8 332.2-1.1 1.1-4-46.3-6.2-106.2-1.7-59.4-4.5-109.6-6.2-110.8-1.7-1.7-21 2.9-43.5 9-22 6.9-41.3 11.4-43 10.2-1.1-1.7 20.4-78.5 48-171.7l49.8-169 3.4 60c2.2 32.7 4 83.6 4.5 111.8" />
                </g>
              </svg>
            ) : (
              <>
                <h1 className="logo">ClockWise</h1>
                <span className="logo-badge">Manager</span>
              </>
            )}
          </div>
          <button
            className="collapse-btn"
            onClick={() => setMgrSidebarCollapsed(!mgrSidebarCollapsed)}
          >
            {mgrSidebarCollapsed ? "→" : "←"}
          </button>
        </div>

        <nav className="nav-menu">
          {mgrNavigationItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${mgrActiveTab === item.id ? "active" : ""}`}
              onClick={() => setMgrActiveTab(item.id)}
            >
              <img src={item.icon} alt={item.label} className="nav-icon" />
              {!mgrSidebarCollapsed && (
                <span className="nav-label">{item.label}</span>
              )}
              {mgrActiveTab === item.id && (
                <div className="active-indicator"></div>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="theme-toggle-container">
            <button
              className={`theme-toggle-switch ${mgrDarkMode ? "dark" : "light"}`}
              onClick={mgrToggleDarkMode}
              title={
                mgrDarkMode ? "Switch to Light Mode" : "Switch to Dark Mode"
              }
            >
              <div className="toggle-track">
                <img
                  src={LightModeIcon}
                  alt="Light Mode"
                  className="toggle-icon toggle-icon-light"
                />
                <img
                  src={DarkModeIcon}
                  alt="Dark Mode"
                  className="toggle-icon toggle-icon-dark"
                />
              </div>
              <div className="toggle-thumb"></div>
            </button>
            {!mgrSidebarCollapsed && (
              <span className="theme-label">
                {mgrDarkMode ? "Dark Mode" : "Light Mode"}
              </span>
            )}
          </div>
          <div className="user-profile">
            <div className="user-avatar">
              {(() => {
                const fullName =
                  mgrCurrentUser?.full_name || mgrProfileData?.full_name || ""
                if (fullName) {
                  return fullName
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)
                }
                return "?"
              })()}
            </div>
            {!mgrSidebarCollapsed && (
              <div className="user-info">
                <div className="user-name">
                  {mgrCurrentUser?.full_name ||
                    mgrProfileData?.full_name ||
                    "Loading..."}
                </div>
                <div className="user-role">
                  {mgrCurrentUser?.user_role ||
                    mgrProfileData?.user_role ||
                    "Manager"}
                </div>
              </div>
            )}
          </div>
          {!mgrSidebarCollapsed && (
            <button className="logout-btn" onClick={mgrHandleLogout}>
              Logout
            </button>
          )}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {mgrLoading && mgrRenderSkeletonLoader()}
        {mgrError && !mgrLoading && (
          <div className="error-state">
            <img
              src={MissedTargetIcon}
              alt="Error"
              className="error-icon-svg"
            />
            <h3>Error Loading Dashboard</h3>
            <p>{mgrError}</p>
            <button className="btn-primary" onClick={mgrFetchDashboardData}>
              Retry
            </button>
          </div>
        )}
        {!mgrLoading && (
          <>
            {mgrActiveTab === "home" && mgrRenderHomeDashboard()}
            {mgrActiveTab === "staffing" && mgrRenderStaffing()}
            {mgrActiveTab === "schedule" && mgrRenderSchedule()}
            {mgrActiveTab === "orders" && mgrRenderOrders()}
            {mgrActiveTab === "rules" && mgrRenderRules()}
            {mgrActiveTab === "profile" && mgrRenderProfile()}
          </>
        )}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav">
        {mgrNavigationItems.map((item) => (
          <button
            key={item.id}
            className={`mobile-nav-item ${mgrActiveTab === item.id ? "active" : ""}`}
            onClick={() => setMgrActiveTab(item.id)}
          >
            <img src={item.icon} alt={item.label} className="mobile-nav-icon" />
            <span className="mobile-nav-label">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default ManagerDashboard
