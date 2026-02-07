import { useState, useEffect, useRef } from "react"
import "./AdminDashboard.css"
import api from "./services/api"

// Import SVG icons
import HomeIcon from "./Icons/Home_Icon.svg"
import ScheduleIcon from "./Icons/Schedule_Icon.svg"
import AnalyticsIcon from "./Icons/Analytics_Icon.svg"
import PlanningIcon from "./Icons/Planning_Icon.svg"
import OrdersIcon from "./Icons/Orders-Icon.svg"
import InfoIcon from "./Icons/Info_Icon.svg"
import ChartUpIcon from "./Icons/Chart-Up-Icon.svg"
import ChartDownIcon from "./Icons/Chart-down-Icon.svg"
import TargetHitIcon from "./Icons/Target-Hit-Icon.svg"
import MissedTargetIcon from "./Icons/Missed-Target-Icon.svg"
import LocationIcon from "./Icons/location-Icon.svg"
import CloudUploadIcon from "./Icons/Cloud-Upload-Icon.svg"
import ItemsIcon from "./Icons/Items-Icon.svg"
import ConfigurationIcon from "./Icons/Configuration-Icon.svg"
import EmployeeIcon from "./Icons/Employee-Icon.svg"
import LightModeIcon from "./Icons/Light-Mode-Icon.svg"
import DarkModeIcon from "./Icons/Dark-Mode-Icon.svg"

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("home")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [showAdminProfile, setShowAdminProfile] = useState(false)
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem("darkMode")
    return saved === "true"
  })
  const [primaryColor, setPrimaryColor] = useState("#4A90E2")
  const [secondaryColor, setSecondaryColor] = useState("#7B68EE")
  const [accentColor, setAccentColor] = useState("#FF6B6B")

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  // User profile state
  const [currentUser, setCurrentUser] = useState(null)
  const [passwordForm, setPasswordForm] = useState({
    old_password: "",
    new_password: "",
    confirm_password: "",
  })
  const [passwordLoading, setPasswordLoading] = useState(false)
  const [passwordError, setPasswordError] = useState("")
  const [passwordSuccess, setPasswordSuccess] = useState("")

  // Insights state
  const [insights, setInsights] = useState([])
  const [staffingSummary, setStaffingSummary] = useState(null)
  const [totalHeadcount, setTotalHeadcount] = useState(0)
  const [laborCost, setLaborCost] = useState(0)
  const [revenue, setRevenue] = useState(0)
  const [currentlyClocked, setCurrentlyClocked] = useState(0)
  const [expectedClocked, setExpectedClocked] = useState(0)
  const configFileInput = useRef(null)
  const rosterFileInput = useRef(null)

  // Orders state
  const [ordersData, setOrdersData] = useState([])
  const [orderItemsData, setOrderItemsData] = useState([])
  const [ordersLoading, setOrdersLoading] = useState(false)
  const [ordersFilter, setOrdersFilter] = useState("all")
  const [ordersDataType, setOrdersDataType] = useState("orders") // orders, items, deliveries
  const [ordersInsights, setOrdersInsights] = useState([])
  const [showUploadOrders, setShowUploadOrders] = useState(false)
  const [showUploadItems, setShowUploadItems] = useState(false)
  const [showUploadOrderItems, setShowUploadOrderItems] = useState(false)
  const [showUploadDeliveries, setShowUploadDeliveries] = useState(false)
  const ordersFileInput = useRef(null)
  const itemsFileInput = useRef(null)
  const orderItemsFileInput = useRef(null)
  const deliveriesFileInput = useRef(null)

  // Campaigns state
  const [campaignsData, setCampaignsData] = useState([])
  const [campaignsLoading, setCampaignsLoading] = useState(false)
  const [campaignsFilter, setCampaignsFilter] = useState("all") // all, week
  const [campaignsInsights, setCampaignsInsights] = useState([])
  const [showUploadCampaigns, setShowUploadCampaigns] = useState(false)
  const [showUploadCampaignItems, setShowUploadCampaignItems] = useState(false)
  const campaignsFileInput = useRef(null)
  const campaignItemsFileInput = useRef(null)

  // Staffing state
  const [employees, setEmployees] = useState([])
  const [showDelegateModal, setShowDelegateModal] = useState(false)
  const [showDetailModal, setShowDetailModal] = useState(false)
  const [showCsvUploadModal, setShowCsvUploadModal] = useState(false)
  const [selectedEmployee, setSelectedEmployee] = useState(null)
  const [employeeRequests, setEmployeeRequests] = useState([])
  const [requestsLoading, setRequestsLoading] = useState(false)
  const [searchTerm, setSearchTerm] = useState("")
  const [roles, setRoles] = useState([])
  const [confirmLayoff, setConfirmLayoff] = useState(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [actionMessage, setActionMessage] = useState(null)
  const [delegateForm, setDelegateForm] = useState({
    full_name: "",
    email: "",
    role: "",
    salary_per_hour: "",
  })
  const [delegateLoading, setDelegateLoading] = useState(false)
  const [delegateError, setDelegateError] = useState("")
  const csvFileInput = useRef(null)

  // Role management state
  const [showAddRoleModal, setShowAddRoleModal] = useState(false)
  const [showEditRoleModal, setShowEditRoleModal] = useState(false)
  const [confirmDeleteRole, setConfirmDeleteRole] = useState(null)
  const [selectedRole, setSelectedRole] = useState(null)
  const [roleForm, setRoleForm] = useState({
    role: "",
    min_needed_per_shift: 1,
    items_per_role_per_hour: "",
    need_for_demand: false,
    independent: true,
  })
  const [roleLoading, setRoleLoading] = useState(false)
  const [roleError, setRoleError] = useState("")

  // Remove hardcoded alerts - will be replaced with real data in future
  const [aiAlerts, setAiAlerts] = useState([])

  // Initialize heatmap with base data (24 hours x 7 days, all zeros)
  const [heatMapData, setHeatMapData] = useState(() => {
    const data = []
    for (let hour = 0; hour < 24; hour++) {
      const row = []
      for (let day = 0; day < 7; day++) {
        row.push(0)
      }
      data.push(row)
    }
    return data
  })

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

  const navigationItems = [
    { id: "home", label: "Dashboard", icon: HomeIcon },
    { id: "schedule", label: "Schedule", icon: ScheduleIcon },
    { id: "insights", label: "Insights", icon: AnalyticsIcon },
    { id: "campaigns", label: "Campaigns", icon: PlanningIcon }, // Changed from "planning" to "campaigns"
    { id: "staffing", label: "Staffing", icon: EmployeeIcon },
    { id: "orders", label: "Orders", icon: OrdersIcon },
    { id: "info", label: "Setup", icon: InfoIcon },
  ]

  const getContrastColor = (hexColor) => {
    const hex = hexColor.replace("#", "")
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5 ? "#000000" : "#FFFFFF"
  }

  const hexToRgb = (hex) => {
    const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex)
    return result
      ? {
          r: parseInt(result[1], 16),
          g: parseInt(result[2], 16),
          b: parseInt(result[3], 16),
        }
      : null
  }

  const getHeatColor = (intensity) => {
    const rgb = hexToRgb(secondaryColor)
    const accentRgb = hexToRgb(accentColor)
    if (!rgb || !accentRgb) return `rgba(123, 104, 238, ${intensity / 100})`

    const factor = intensity / 100

    if (intensity > 80) {
      const accentMix = ((intensity - 80) / 20) * 0.3
      return `rgba(${Math.round(rgb.r * (1 - accentMix) + accentRgb.r * accentMix)}, ${Math.round(rgb.g * (1 - accentMix) + accentRgb.g * accentMix)}, ${Math.round(rgb.b * (1 - accentMix) + accentRgb.b * accentMix)}, ${0.3 + factor * 0.7})`
    }

    return `rgba(${rgb.r}, ${rgb.g}, ${rgb.b}, ${0.2 + factor * 0.8})`
  }

  const getHeatTextColor = (intensity) => {
    const bgColor = getHeatColor(intensity)
    const rgba = bgColor.match(/\d+/g)
    if (!rgba) return "#000000"

    const r = parseInt(rgba[0])
    const g = parseInt(rgba[1])
    const b = parseInt(rgba[2])
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    return luminance > 0.5 ? "#000000" : "#FFFFFF"
  }

  useEffect(() => {
    const savedColors = localStorage.getItem("orgColors")
    if (savedColors) {
      const colors = JSON.parse(savedColors)
      const primary = colors[0] || primaryColor
      const secondary = colors[1] || secondaryColor
      const accent = colors[2] || accentColor

      setPrimaryColor(primary)
      setSecondaryColor(secondary)
      setAccentColor(accent)

      // Set scoped CSS variables for Admin Dashboard
      const adminDashboard = document.querySelector(".dashboard-wrapper")
      if (adminDashboard) {
        adminDashboard.style.setProperty("--color-primary", primary)
        adminDashboard.style.setProperty("--color-secondary", secondary)
        adminDashboard.style.setProperty("--color-accent", accent)
        adminDashboard.style.setProperty(
          "--primary-contrast",
          getContrastColor(primary),
        )
        adminDashboard.style.setProperty(
          "--secondary-contrast",
          getContrastColor(secondary),
        )
        adminDashboard.style.setProperty(
          "--accent-contrast",
          getContrastColor(accent),
        )
      }
    }
  }, [])

  useEffect(() => {
    // Apply dark mode class to admin dashboard only
    const adminDashboard = document.querySelector(".dashboard-wrapper")
    if (adminDashboard) {
      if (darkMode) {
        adminDashboard.classList.add("dark-mode")
      } else {
        adminDashboard.classList.remove("dark-mode")
      }
    }
  }, [darkMode])

  useEffect(() => {
    fetchDashboardData()
    fetchCurrentUser()

    if (!document.getElementById("mapbox-gl-js")) {
      const script = document.createElement("script")
      script.id = "mapbox-gl-js"
      script.src = "https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.js"
      document.head.appendChild(script)

      const link = document.createElement("link")
      link.id = "mapbox-gl-css"
      link.href = "https://api.mapbox.com/mapbox-gl-js/v2.15.0/mapbox-gl.css"
      link.rel = "stylesheet"
      document.head.appendChild(link)
    }
  }, [])

  const fetchCurrentUser = async () => {
    try {
      // Try to get from cache first
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        console.log("Loaded user from cache:", parsedUser)
        setCurrentUser(parsedUser)
      }

      // Fetch fresh data from API - use profile endpoint for more detailed info
      const profileData = await api.profile.getProfile()
      console.log("Fetched profile data from API:", profileData)

      // The profile data comes with a nested structure
      const userData = profileData.data || profileData

      // Also get basic user info to ensure we have all fields
      const authData = await api.auth.getCurrentUser()

      // Merge both sources for complete user info
      const completeUser = {
        ...authData,
        ...userData,
        organization_name: userData.organization,
      }

      console.log("Complete user data:", completeUser)
      setCurrentUser(completeUser)

      // Update cache
      localStorage.setItem("current_user", JSON.stringify(completeUser))
    } catch (err) {
      console.error("Error fetching user data:", err)
      // Still try to use cached data
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        console.log("Using cached user data after error:", parsedUser)
        setCurrentUser(parsedUser)
      }
    }
  }

  const handleChangePassword = async (e) => {
    e.preventDefault()
    setPasswordError("")
    setPasswordSuccess("")

    // Validate passwords match
    if (passwordForm.new_password !== passwordForm.confirm_password) {
      setPasswordError("New passwords do not match")
      return
    }

    // Validate password length
    if (passwordForm.new_password.length < 6) {
      setPasswordError("New password must be at least 6 characters")
      return
    }

    setPasswordLoading(true)

    try {
      await api.profile.changePassword({
        old_password: passwordForm.old_password,
        new_password: passwordForm.new_password,
      })

      setPasswordSuccess("Password changed successfully!")
      setPasswordForm({
        old_password: "",
        new_password: "",
        confirm_password: "",
      })

      // Close modal after 2 seconds
      setTimeout(() => {
        setPasswordSuccess("")
      }, 3000)
    } catch (err) {
      setPasswordError(err.message || "Failed to change password")
    } finally {
      setPasswordLoading(false)
    }
  }

  const toggleDarkMode = () => {
    const newMode = !darkMode
    setDarkMode(newMode)
    localStorage.setItem("darkMode", newMode.toString())
  }

  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError("")

      // Fetch insights data
      try {
        const insightsResponse = await api.insights.getInsights()
        if (insightsResponse && insightsResponse.data) {
          setInsights(insightsResponse.data)

          // Extract key metrics from insights
          const employeesInsight = insightsResponse.data.find((i) =>
            i.title.toLowerCase().includes("number of employees"),
          )
          if (employeesInsight) {
            setTotalHeadcount(parseInt(employeesInsight.statistic) || 0)
          }

          const salaryInsight = insightsResponse.data.find((i) =>
            i.title.toLowerCase().includes("average employee salary"),
          )
          if (salaryInsight) {
            const salary =
              parseFloat(salaryInsight.statistic.replace(/[$,]/g, "")) || 0
            setLaborCost(salary)
          }

          const revenueInsight = insightsResponse.data.find((i) =>
            i.title.toLowerCase().includes("total revenue"),
          )
          if (revenueInsight) {
            const rev =
              parseFloat(revenueInsight.statistic.replace(/[$,]/g, "")) || 0
            setRevenue(rev)
          }
        }
      } catch (err) {
        console.error("Error fetching insights:", err)
      }

      // Fetch staffing summary
      try {
        const summary = await api.staffing.getStaffingSummary()
        if (summary && summary.data) {
          setStaffingSummary(summary.data)
        }
      } catch (err) {
        console.error("Error fetching staffing summary:", err)
      }

      // Fetch roles
      try {
        const rolesResponse = await api.roles.getAll()
        if (rolesResponse && rolesResponse.data) {
          setRoles(rolesResponse.data)
        }
      } catch (err) {
        console.error("Error fetching roles:", err)
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err)
      setError(err.message || "Failed to load dashboard data")
    } finally {
      setLoading(false)
    }
  }



  // Load roles when info tab is active
  useEffect(() => {
    if (activeTab === "info") {
      fetchRoles()
    }
  }, [activeTab])

  // Consolidated fetch function for orders/items/deliveries
  const fetchOrders = async (filter = "all", dataType = "orders") => {
    try {
      setOrdersLoading(true)
      let data
      let insights
      if (dataType === "items") {
        // Items don't have time filters
        data = await api.items.getAllItems()
        insights = await api.items.getItemInsights()
      } else if (dataType === "deliveries") {
        insights = await api.deliveries.getDeliveryInsights()
        switch (filter) {
          case "today":
            data = await api.deliveries.getDeliveriesToday()
            break
          case "week":
            data = await api.deliveries.getDeliveriesWeek()
            break
          default:
            data = await api.deliveries.getAllDeliveries()
        }
      } else {
        insights = await api.orders.getOrderInsights()
        switch (filter) {
          case "today":
            data = await api.orders.getOrdersToday()
            break
          case "week":
            data = await api.orders.getOrdersWeek()
            break
          default:
            data = await api.orders.getAllOrders()
        }
      }
      setOrdersData(data.data || [])
      setOrdersInsights(insights.data || [])

      // Extract order items from orders data
      if (dataType === "orders" && data.data) {
        const allOrderItems = []
        data.data.forEach((order) => {
          const items = order.order_items || order.items || []
          items.forEach((item) => {
            allOrderItems.push({
              order_id: order.order_id,
              item_id: item.item_id,
              quantity: item.quantity,
              total_price: item.total_price,
            })
          })
        })
        setOrderItemsData(allOrderItems)
      } else {
        setOrderItemsData([])
      }
    } catch (err) {
      console.error("Failed to fetch data:", err)
      setActionMessage({
        type: "error",
        text: err.message || "Failed to load data",
      })
      setTimeout(() => setActionMessage(null), 4000)
    } finally {
      setOrdersLoading(false)
    }
  }

  // Fetch orders when orders tab is active or filter/type changes
  useEffect(() => {
    if (activeTab === "orders") {
      fetchOrders(ordersFilter, ordersDataType)
    }
  }, [activeTab, ordersFilter, ordersDataType])
  // Fetch campaigns when campaigns tab is active or filter changes
  useEffect(() => {
    if (activeTab === "campaigns") {
      const fetchCampaignsData = async () => {
        try {
          setCampaignsLoading(true)
          let data
          let insights
          insights = await api.campaigns.getCampaignInsights()
          switch (campaignsFilter) {
            case "week":
              data = await api.campaigns.getCampaignsWeek()
              break
            default:
              data = await api.campaigns.getAllCampaigns()
          }
          setCampaignsData(data.data || [])
          setCampaignsInsights(insights.data || [])
        } catch (err) {
          console.error("Failed to fetch campaigns:", err)
        } finally {
          setCampaignsLoading(false)
        }
      }
      fetchCampaignsData()
    }
  }, [activeTab, campaignsFilter])

  const handleConfigUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      console.log("Configuration file selected:", file.name)
    }
  }

  const handleRosterUpload = (event) => {
    const file = event.target.files[0]
    if (file) {
      console.log("Roster file selected:", file.name)
    }
  }

  const dismissAlert = (id) => {
    setAiAlerts((prev) =>
      prev.map((alert) =>
        alert.id === id ? { ...alert, dismissed: true } : alert,
      ),
    )
  }

  const renderSkeletonLoader = () => (
    <div className="skeleton-container">
      <div className="skeleton-header"></div>
      <div className="skeleton-grid">
        {[1, 2, 3].map((i) => (
          <div key={i} className="skeleton-card">
            <div className="skeleton-line skeleton-title"></div>
            <div className="skeleton-line skeleton-value"></div>
            <div className="skeleton-line skeleton-subtitle"></div>
          </div>
        ))}
      </div>
    </div>
  )

  const renderHomeDashboard = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Organization Pulse</h1>
          <p className="page-subtitle">
            Real-time insights into your workforce
          </p>
        </div>
        <button className="btn-primary">
          <span>Export Report</span>
        </button>
      </div>

      {/* Premium KPI Cards */}
      <div className="kpi-grid">
        <div className="kpi-card kpi-card-primary" data-animation="slide-up">
          <div className="kpi-icon-wrapper">
            <svg
              className="kpi-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z"
              />
            </svg>
          </div>
          <div className="kpi-content">
            <h3 className="kpi-label">Total Headcount</h3>
            <div className="kpi-value-wrapper">
              <div className="kpi-value">{totalHeadcount}</div>
              <div className="kpi-trend trend-up">
                <span className="trend-icon">↑</span>
                <span className="trend-value">12%</span>
              </div>
            </div>
            <p className="kpi-subtitle">Active employees this week</p>
          </div>
          <div className="kpi-sparkline"></div>
        </div>

        <div
          className="kpi-card kpi-card-secondary"
          data-animation="slide-up"
          style={{ animationDelay: "0.1s" }}
        >
          <div className="kpi-icon-wrapper">
            <svg
              className="kpi-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="kpi-content">
            <h3 className="kpi-label">Labor Cost</h3>
            <div className="kpi-value-wrapper">
              <div className="kpi-value">${(laborCost / 1000).toFixed(1)}K</div>
              <div className="kpi-trend trend-down">
                <span className="trend-icon">↓</span>
                <span className="trend-value">3%</span>
              </div>
            </div>
            <p className="kpi-subtitle">Weekly expenditure</p>
          </div>
          <div className="kpi-sparkline"></div>
        </div>

        <div
          className="kpi-card kpi-card-accent"
          data-animation="slide-up"
          style={{ animationDelay: "0.2s" }}
        >
          <div className="kpi-icon-wrapper">
            <svg
              className="kpi-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
              />
            </svg>
          </div>
          <div className="kpi-content">
            <h3 className="kpi-label">Revenue Impact</h3>
            <div className="kpi-value-wrapper">
              <div className="kpi-value">${(revenue / 1000).toFixed(1)}K</div>
              <div className="kpi-trend trend-up">
                <span className="trend-icon">↑</span>
                <span className="trend-value">8%</span>
              </div>
            </div>
            <p className="kpi-subtitle">Generated this week</p>
          </div>
          <div className="kpi-sparkline"></div>
        </div>
      </div>

      {/* AI Alerts Section */}
      {aiAlerts && aiAlerts.filter((a) => !a.dismissed).length > 0 && (
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">
              <img src={InfoIcon} alt="Alerts" className="title-icon-svg" />
              Intelligent Alerts
            </h2>
            <span className="badge badge-primary">
              {aiAlerts.filter((a) => !a.dismissed).length} Active
            </span>
          </div>
          <div className="alerts-grid">
            {aiAlerts
              .filter((a) => !a.dismissed)
              .map((alert) => (
                <div
                  key={alert.id}
                  className={`alert-card alert-${alert.priority}`}
                  data-animation="fade-in"
                >
                  <div className="alert-header">
                    <div className={`alert-badge priority-${alert.priority}`}>
                      {alert.priority.toUpperCase()}
                    </div>
                    <span className="alert-timestamp">{alert.timestamp}</span>
                  </div>
                  <p className="alert-message">{alert.message}</p>
                  <div className="alert-actions">
                    <button className="btn-link">View Details</button>
                    <button
                      className="btn-link"
                      onClick={() => dismissAlert(alert.id)}
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* Heat Map Section */}
      {heatMapData && heatMapData.length > 0 && (
        <div className="section-wrapper">
          <div className="section-header">
            <div>
              <h2 className="section-title">Weekly Demand Heat Map</h2>
              <p className="section-description">
                Peak hours analysis - hover for detailed metrics
              </p>
            </div>
            <div className="section-actions">
              <button className="btn-secondary">Export Data</button>
            </div>
          </div>
          <div className="heatmap-wrapper">
            <div className="heatmap-table">
              <div className="heatmap-header-row">
                <div className="heatmap-corner-cell">Hour</div>
                {days.map((day) => (
                  <div key={day} className="heatmap-day-header">
                    {day}
                  </div>
                ))}
              </div>
              {heatMapData.map((row, hourIndex) => (
                <div key={hourIndex} className="heatmap-data-row">
                  <div className="heatmap-hour-label">
                    {String(hourIndex).padStart(2, "0")}:00
                  </div>
                  {row.map((intensity, dayIndex) => (
                    <div
                      key={dayIndex}
                      className="heatmap-data-cell"
                      style={{
                        backgroundColor: getHeatColor(intensity),
                        color: getHeatTextColor(intensity),
                      }}
                      title={`${days[dayIndex]} ${String(hourIndex).padStart(2, "0")}:00 - ${intensity}% capacity`}
                    >
                      {intensity}%
                    </div>
                  ))}
                </div>
              ))}
            </div>
            <div className="heatmap-legend">
              <span className="legend-label">Low</span>
              <div className="legend-gradient"></div>
              <span className="legend-label">High</span>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderMasterSchedule = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Master Schedule</h1>
          <p className="page-subtitle">Comprehensive workforce calendar</p>
        </div>
        <button className="btn-primary">Add Shift</button>
      </div>

      <div className="filter-bar">
        <select className="filter-select">
          <option>All Departments</option>
          <option>Sales</option>
          <option>Operations</option>
          <option>Customer Service</option>
          <option>IT</option>
        </select>
        <select className="filter-select">
          <option>All Segments</option>
          <option>Morning Shift</option>
          <option>Evening Shift</option>
          <option>Night Shift</option>
        </select>
        <button className="btn-secondary">Export Schedule</button>
      </div>

      <div className="empty-state">
        <img src={ScheduleIcon} alt="Schedule" className="empty-icon-svg" />
        <h3>Schedule View Coming Soon</h3>
        <p>Full organization calendar with drag-and-drop scheduling</p>
      </div>
    </div>
  )

  const renderInsights = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Organization Insights</h1>
          <p className="page-subtitle">Real-time metrics and analytics</p>
        </div>
        <button className="btn-primary" onClick={() => fetchDashboardData()}>
          <svg
            style={{ width: "20px", height: "20px", marginRight: "8px" }}
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
            />
          </svg>
          Refresh Data
        </button>
      </div>

      {insights && insights.length > 0 ? (
        <div
          className="insights-grid"
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
            gap: "var(--space-6)",
          }}
        >
          {insights.map((insight, index) => (
            <div
              key={index}
              className="kpi-card kpi-card-primary"
              data-animation="slide-up"
              style={{
                animationDelay: `${index * 0.05}s`,
              }}
            >
              <div className="kpi-icon-wrapper">
                <svg
                  className="kpi-icon"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                  />
                </svg>
              </div>
              <div className="kpi-content">
                <h3 className="kpi-label">{insight.title}</h3>
                <div className="kpi-value-wrapper">
                  <div className="kpi-value">{insight.statistic}</div>
                </div>
              </div>
            </div>
          ))}
        </div>
      ) : (
        <div className="empty-state">
          <img src={AnalyticsIcon} alt="Insights" className="empty-icon-svg" />
          <h3>No Insights Available</h3>
          <p>
            Insights data will appear here once you have sufficient activity
          </p>
        </div>
      )}
    </div>
  )

  const renderCampaigns = () => {
    const fetchCampaigns = async (filter = "all") => {
      try {
        setCampaignsLoading(true)
        let data
        let insights
        insights = await api.campaigns.getCampaignInsights()
        switch (filter) {
          case "week":
            data = await api.campaigns.getCampaignsWeek()
            break
          default:
            data = await api.campaigns.getAllCampaigns()
        }
        setCampaignsData(data.data || [])
        setCampaignsInsights(insights.data || [])
      } catch (err) {
        console.error("Failed to fetch campaigns:", err)
        setActionMessage({
          type: "error",
          text: err.message || "Failed to load campaigns",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setCampaignsLoading(false)
      }
    }

    const handleCampaignsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setCampaignsLoading(true)
        const response = await api.campaigns.uploadCampaignsCSV(file)
        setActionMessage({
          type: "success",
          text: `Campaigns uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchCampaigns(campaignsFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload campaigns",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setCampaignsLoading(false)
        setShowUploadCampaigns(false)
        if (campaignsFileInput.current) campaignsFileInput.current.value = ""
      }
    }

    const handleCampaignItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setCampaignsLoading(true)
        const response = await api.campaigns.uploadCampaignItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Campaign items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchCampaigns(campaignsFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload campaign items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setCampaignsLoading(false)
        setShowUploadCampaignItems(false)
        if (campaignItemsFileInput.current)
          campaignItemsFileInput.current.value = ""
      }
    }

    const handleGetRecommendations = () => {
      setActionMessage({
        type: "success",
        text: "Campaign recommendations feature coming soon! Our AI will analyze your data to suggest optimal campaigns.",
      })
      setTimeout(() => setActionMessage(null), 5000)
    }

    const downloadCSV = () => {
      if (!campaignsData || campaignsData.length === 0) {
        setActionMessage({ type: "error", text: "No campaigns to download" })
        setTimeout(() => setActionMessage(null), 3000)
        return
      }

      let csvContent =
        "Campaign ID,Name,Status,Start Time,End Time,Discount (%),Items Count\n"
      campaignsData.forEach((campaign) => {
        const itemsCount = campaign.items_included
          ? campaign.items_included.length
          : 0
        csvContent += `${campaign.id},${campaign.name},${campaign.status},${campaign.start_time},${campaign.end_time},${campaign.discount || ""},${itemsCount}\n`
      })

      const filename = `campaigns_${campaignsFilter}_${new Date().toISOString().split("T")[0]}.csv`

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const link = document.createElement("a")
      const url = URL.createObjectURL(blob)
      link.setAttribute("href", url)
      link.setAttribute("download", filename)
      link.style.visibility = "hidden"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      setActionMessage({ type: "success", text: "CSV downloaded successfully" })
      setTimeout(() => setActionMessage(null), 3000)
    }

    const getStatusColor = (status) => {
      switch (status) {
        case "active":
          return "var(--color-primary)"
        case "inactive":
          return "var(--gray-500)"
        default:
          return "var(--gray-500)"
      }
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Campaign Management</h1>
            <p className="page-subtitle">
              Manage and analyze marketing campaigns
            </p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <button
              className="btn-secondary"
              onClick={() => setShowUploadCampaigns(true)}
            >
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              Upload Campaigns
            </button>
            <button
              className="btn-secondary"
              onClick={handleGetRecommendations}
            >
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"
                />
              </svg>
              Get Recommendations
            </button>
            <button
              className="btn-primary"
              onClick={() => fetchCampaigns(campaignsFilter)}
            >
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
            <button className="btn-secondary" onClick={downloadCSV}>
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download CSV
            </button>
          </div>
        </div>

        <div
          className="filter-bar"
          style={{
            display: "flex",
            gap: "var(--space-3)",
            alignItems: "center",
          }}
        >
          <button
            className={
              campaignsFilter === "all" ? "btn-primary" : "btn-secondary"
            }
            onClick={() => setCampaignsFilter("all")}
          >
            All Campaigns
          </button>
          <button
            className={
              campaignsFilter === "week" ? "btn-primary" : "btn-secondary"
            }
            onClick={() => setCampaignsFilter("week")}
          >
            This Week
          </button>
        </div>

        {/* Insights Boxes */}
        {campaignsInsights.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--space-4)",
              marginTop: "var(--space-4)",
            }}
          >
            {campaignsInsights.map((insight, index) => (
              <div
                key={index}
                className="stat-card"
                style={{
                  background: "var(--gray-50)",
                  border: "1px solid var(--gray-200)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-4)",
                }}
              >
                <p
                  style={{
                    fontSize: "var(--text-sm)",
                    color: "var(--gray-600)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {insight.title}
                </p>
                <h3
                  style={{
                    fontSize: "var(--text-2xl)",
                    fontWeight: 700,
                    color: "var(--primary-600)",
                  }}
                >
                  {insight.statistic}
                </h3>
              </div>
            ))}
          </div>
        )}

        {campaignsLoading ? (
          <div className="empty-state">
            <h3>Loading campaigns...</h3>
          </div>
        ) : campaignsData && campaignsData.length > 0 ? (
          <div className="section-wrapper">
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Campaign ID
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Name
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Status
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Start Date
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      End Date
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Discount
                    </th>
                    <th
                      style={{
                        textAlign: "left",
                        padding: "var(--space-4)",
                        fontSize: "var(--text-sm)",
                        fontWeight: 600,
                        color: "var(--gray-600)",
                        textTransform: "uppercase",
                      }}
                    >
                      Items
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {campaignsData.map((campaign, index) => (
                    <tr
                      key={campaign.id || `campaign-${index}`}
                      style={{ borderBottom: "1px solid var(--gray-200)" }}
                    >
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-sm)",
                          color: "var(--gray-700)",
                        }}
                      >
                        {campaign.id ? campaign.id.slice(0, 8) + "..." : "—"}
                      </td>
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-base)",
                          color: "var(--gray-700)",
                          fontWeight: 600,
                        }}
                      >
                        {campaign.name}
                      </td>
                      <td style={{ padding: "var(--space-4)" }}>
                        <span
                          style={{
                            padding: "4px 12px",
                            borderRadius: "var(--radius-full)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            backgroundColor:
                              getStatusColor(campaign.status) + "20",
                            color: getStatusColor(campaign.status),
                          }}
                        >
                          {campaign.status}
                        </span>
                      </td>
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-sm)",
                          color: "var(--gray-500)",
                        }}
                      >
                        {new Date(campaign.start_time).toLocaleDateString()}
                      </td>
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-sm)",
                          color: "var(--gray-500)",
                        }}
                      >
                        {new Date(campaign.end_time).toLocaleDateString()}
                      </td>
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-base)",
                          color: "var(--secondary-600)",
                          fontWeight: 600,
                        }}
                      >
                        {campaign.discount ? `${campaign.discount}%` : "—"}
                      </td>
                      <td
                        style={{
                          padding: "var(--space-4)",
                          fontSize: "var(--text-base)",
                          color: "var(--gray-700)",
                        }}
                      >
                        {campaign.items_included &&
                        campaign.items_included.length > 0 ? (
                          <span
                            title={campaign.items_included
                              .map((item) => item.name)
                              .join(", ")}
                          >
                            {campaign.items_included.length} item
                            {campaign.items_included.length !== 1 ? "s" : ""}
                          </span>
                        ) : (
                          <span style={{ color: "var(--gray-400)" }}>
                            No items
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ) : (
          <div className="empty-state">
            <img
              src={PlanningIcon}
              alt="Campaigns"
              className="empty-icon-svg"
            />
            <h3>No Campaigns Found</h3>
            <p>Upload campaigns data to get started</p>
          </div>
        )}

        {/* Upload Campaigns Modal */}
        {showUploadCampaigns && (
          <div
            className="modal-overlay"
            onClick={() => setShowUploadCampaigns(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Campaigns CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowUploadCampaigns(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                onClick={() => campaignsFileInput.current?.click()}
              >
                <img
                  src={CloudUploadIcon}
                  alt="Upload"
                  className="upload-icon-svg"
                />
                <h3 className="upload-title">Campaigns Data</h3>
                <p className="upload-description">
                  Upload marketing campaigns history
                </p>
                <ul className="upload-specs">
                  <li>
                    <strong>Required:</strong> id (UUID), name, status,
                    start_time, end_time
                  </li>
                  <li>
                    <strong>Optional:</strong> discount_percent
                  </li>
                  <li>
                    <strong>Status values:</strong> active, inactive
                  </li>
                  <li>
                    <strong>Timestamp formats:</strong> RFC3339
                    (2024-06-01T00:00:00Z) or DateTime (2024-06-01 00:00:00)
                  </li>
                  <li>Discount percentage is optional (e.g., 15.50)</li>
                </ul>
                <input
                  ref={campaignsFileInput}
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={handleCampaignsUpload}
                />
              </div>
              <div style={{ marginTop: "var(--space-4)" }}>
                <div
                  className="upload-card"
                  onClick={() => campaignItemsFileInput.current?.click()}
                >
                  <img
                    src={CloudUploadIcon}
                    alt="Upload"
                    className="upload-icon-svg"
                  />
                  <h3 className="upload-title">Campaign Items Data</h3>
                  <p className="upload-description">Link items to campaigns</p>
                  <ul className="upload-specs">
                    <li>
                      <strong>Required:</strong> campaign_id (UUID), item_id
                      (UUID)
                    </li>
                    <li>
                      <strong>Prerequisites:</strong> Campaigns and Items must
                      already exist
                    </li>
                    <li>
                      Multiple items can be associated with the same campaign
                    </li>
                    <li>Duplicate campaign-item pairs are ignored</li>
                  </ul>
                  <input
                    ref={campaignItemsFileInput}
                    type="file"
                    accept=".csv"
                    style={{ display: "none" }}
                    onChange={handleCampaignItemsUpload}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  const renderOrders = () => {
    const handleOrdersUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setOrdersLoading(true)
        const response = await api.orders.uploadOrdersCSV(file)
        setActionMessage({
          type: "success",
          text: `Orders uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchOrders(ordersFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload orders",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        setShowUploadOrders(false)
        if (ordersFileInput.current) ordersFileInput.current.value = ""
      }
    }

    const handleItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setOrdersLoading(true)
        const response = await api.items.uploadItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        setShowUploadItems(false)
        if (itemsFileInput.current) itemsFileInput.current.value = ""
      }
    }

    const handleOrderItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setOrdersLoading(true)
        const response = await api.orders.uploadOrderItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Order items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload order items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        setShowUploadOrderItems(false)
        if (orderItemsFileInput.current) orderItemsFileInput.current.value = ""
      }
    }

    const handleDeliveriesUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      try {
        setOrdersLoading(true)
        const response = await api.deliveries.uploadDeliveriesCSV(file)
        setActionMessage({
          type: "success",
          text: `Deliveries uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload deliveries",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        setShowUploadDeliveries(false)
        if (deliveriesFileInput.current) deliveriesFileInput.current.value = ""
      }
    }

    const getOrderTypeColor = (type) => {
      switch (type) {
        case "dine_in":
          return "var(--color-primary)"
        case "delivery":
          return "var(--color-secondary)"
        case "takeaway":
          return "var(--color-accent)"
        default:
          return "var(--gray-500)"
      }
    }

    const getStatusBadge = (status) => {
      const colors = {
        completed: "var(--color-primary)",
        in_progress: "var(--secondary-500)",
        cancelled: "var(--accent-500)",
        pending: "var(--gray-500)",
      }
      return colors[status] || "var(--gray-500)"
    }

    const downloadCSV = () => {
      if (!ordersData || ordersData.length === 0) {
        setActionMessage({ type: "error", text: "No data to download" })
        setTimeout(() => setActionMessage(null), 3000)
        return
      }

      let csvContent = ""
      let filename = ""

      if (ordersDataType === "orders") {
        csvContent =
          "Order ID,Type,Status,Amount,Discount,Item Count,Rating,Date\n"
        ordersData.forEach((order) => {
          csvContent += `${order.order_id},${order.order_type},${order.order_status},${order.total_amount || 0},${order.discount_amount || 0},${order.item_count || 0},${order.rating || ""},${new Date(order.create_time).toISOString()}\n`
        })
        filename = `orders_${ordersFilter}_${new Date().toISOString().split("T")[0]}.csv`
      } else if (ordersDataType === "items") {
        csvContent = "Item ID,Name,Needed Employees,Price\n"
        ordersData.forEach((item) => {
          csvContent += `${item.item_id},${item.name},${item.needed_employees},${item.price}\n`
        })
        filename = `items_${new Date().toISOString().split("T")[0]}.csv`
      } else {
        csvContent =
          "Order ID,Driver ID,Status,Latitude,Longitude,Out for Delivery,Delivered\n"
        ordersData.forEach((delivery) => {
          const lat = delivery.location?.latitude || ""
          const lon = delivery.location?.longitude || ""
          csvContent += `${delivery.order_id},${delivery.driver_id || ""},${delivery.status},${lat},${lon},${delivery.out_for_delivery_time || ""},${delivery.delivered_time || ""}\n`
        })
        filename = `deliveries_${ordersFilter}_${new Date().toISOString().split("T")[0]}.csv`
      }

      const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" })
      const link = document.createElement("a")
      const url = URL.createObjectURL(blob)
      link.setAttribute("href", url)
      link.setAttribute("download", filename)
      link.style.visibility = "hidden"
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)

      setActionMessage({ type: "success", text: "CSV downloaded successfully" })
      setTimeout(() => setActionMessage(null), 3000)
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Orders Management</h1>
            <p className="page-subtitle">View and manage organization orders</p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            {ordersDataType === "orders" ? (
              <>
                <button
                  className="btn-secondary"
                  onClick={() => setShowUploadOrders(true)}
                >
                  <svg
                    style={{
                      width: "18px",
                      height: "18px",
                      marginRight: "8px",
                    }}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  Upload Orders
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setShowUploadOrderItems(true)}
                >
                  <svg
                    style={{
                      width: "18px",
                      height: "18px",
                      marginRight: "8px",
                    }}
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                    />
                  </svg>
                  Upload Order Items
                </button>
              </>
            ) : ordersDataType === "items" ? (
              <button
                className="btn-secondary"
                onClick={() => setShowUploadItems(true)}
              >
                <svg
                  style={{ width: "18px", height: "18px", marginRight: "8px" }}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                Upload Items Catalog
              </button>
            ) : (
              <button
                className="btn-secondary"
                onClick={() => setShowUploadDeliveries(true)}
              >
                <svg
                  style={{ width: "18px", height: "18px", marginRight: "8px" }}
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                  />
                </svg>
                Upload Deliveries
              </button>
            )}
            <button
              className="btn-primary"
              onClick={() => fetchOrders(ordersFilter, ordersDataType)}
            >
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                />
              </svg>
              Refresh
            </button>
            <button className="btn-secondary" onClick={downloadCSV}>
              <svg
                style={{ width: "18px", height: "18px", marginRight: "8px" }}
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                />
              </svg>
              Download CSV
            </button>
          </div>
        </div>

        <div
          className="filter-bar"
          style={{
            display: "flex",
            gap: "var(--space-3)",
            alignItems: "center",
          }}
        >
          <select
            className="filter-select"
            value={ordersDataType}
            onChange={(e) => setOrdersDataType(e.target.value)}
            style={{ padding: "8px 12px", minWidth: "150px" }}
          >
            <option value="orders">Orders</option>
            <option value="items">Items</option>
            <option value="deliveries">Deliveries</option>
          </select>
          {ordersDataType !== "items" && (
            <>
              <button
                className={
                  ordersFilter === "all" ? "btn-primary" : "btn-secondary"
                }
                onClick={() => setOrdersFilter("all")}
              >
                All Time
              </button>
              <button
                className={
                  ordersFilter === "today" ? "btn-primary" : "btn-secondary"
                }
                onClick={() => setOrdersFilter("today")}
              >
                Today
              </button>
              <button
                className={
                  ordersFilter === "week" ? "btn-primary" : "btn-secondary"
                }
                onClick={() => setOrdersFilter("week")}
              >
                This Week
              </button>
            </>
          )}
        </div>

        {/* Insights Boxes */}
        {ordersInsights.length > 0 && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
              gap: "var(--space-4)",
              marginTop: "var(--space-4)",
            }}
          >
            {ordersInsights.map((insight, index) => (
              <div
                key={index}
                className="stat-card"
                style={{
                  background: "var(--gray-50)",
                  border: "1px solid var(--gray-200)",
                  borderRadius: "var(--radius-lg)",
                  padding: "var(--space-4)",
                }}
              >
                <p
                  style={{
                    fontSize: "var(--text-sm)",
                    color: "var(--gray-600)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {insight.title}
                </p>
                <h3
                  style={{
                    fontSize: "var(--text-2xl)",
                    fontWeight: 700,
                    color: "var(--primary-600)",
                  }}
                >
                  {insight.statistic}
                </h3>
              </div>
            ))}
          </div>
        )}

        {ordersLoading ? (
          <div className="empty-state">
            <h3>Loading {ordersDataType}...</h3>
          </div>
        ) : ordersData && ordersData.length > 0 ? (
          <div className="section-wrapper">
            {ordersDataType === "orders" ? (
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "1fr 1fr",
                  gap: "var(--space-4)",
                }}
              >
                {/* Orders Table */}
                <div style={{ overflowX: "auto" }}>
                  <h3
                    style={{
                      fontSize: "var(--text-lg)",
                      fontWeight: 600,
                      marginBottom: "var(--space-3)",
                      color: "var(--gray-700)",
                    }}
                  >
                    Orders
                  </h3>
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-3)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Order ID
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-3)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Type
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-3)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Status
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-3)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Amount
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-3)",
                            fontSize: "var(--text-xs)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Items
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {ordersData.map((order, index) => (
                        <tr
                          key={order.order_id || `order-${index}`}
                          style={{ borderBottom: "1px solid var(--gray-200)" }}
                        >
                          <td
                            style={{
                              padding: "var(--space-3)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                            }}
                          >
                            {order.order_id
                              ? order.order_id.slice(0, 8) + "..."
                              : "—"}
                          </td>
                          <td style={{ padding: "var(--space-3)" }}>
                            <span
                              style={{
                                padding: "2px 8px",
                                borderRadius: "var(--radius-full)",
                                fontSize: "var(--text-xs)",
                                fontWeight: 600,
                                backgroundColor:
                                  getOrderTypeColor(order.order_type) + "20",
                                color: getOrderTypeColor(order.order_type),
                              }}
                            >
                              {order.order_type}
                            </span>
                          </td>
                          <td style={{ padding: "var(--space-3)" }}>
                            <span
                              style={{
                                padding: "2px 8px",
                                borderRadius: "var(--radius-full)",
                                fontSize: "var(--text-xs)",
                                fontWeight: 600,
                                backgroundColor:
                                  getStatusBadge(order.order_status) + "20",
                                color: getStatusBadge(order.order_status),
                              }}
                            >
                              {order.order_status}
                            </span>
                          </td>
                          <td
                            style={{
                              padding: "var(--space-3)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                              fontWeight: 600,
                            }}
                          >
                            ${order.total_amount?.toFixed(2) || "0.00"}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-3)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                              textAlign: "center",
                            }}
                          >
                            {order.item_count || 0}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {/* Order Items Table */}
                <div style={{ overflowX: "auto" }}>
                  <h3
                    style={{
                      fontSize: "var(--text-lg)",
                      fontWeight: 600,
                      marginBottom: "var(--space-3)",
                      color: "var(--gray-700)",
                    }}
                  >
                    Order Items
                  </h3>
                  {orderItemsData.length > 0 ? (
                    <table
                      style={{ width: "100%", borderCollapse: "collapse" }}
                    >
                      <thead>
                        <tr
                          style={{ borderBottom: "2px solid var(--gray-200)" }}
                        >
                          <th
                            style={{
                              textAlign: "left",
                              padding: "var(--space-3)",
                              fontSize: "var(--text-xs)",
                              fontWeight: 600,
                              color: "var(--gray-600)",
                              textTransform: "uppercase",
                            }}
                          >
                            Order ID
                          </th>
                          <th
                            style={{
                              textAlign: "left",
                              padding: "var(--space-3)",
                              fontSize: "var(--text-xs)",
                              fontWeight: 600,
                              color: "var(--gray-600)",
                              textTransform: "uppercase",
                            }}
                          >
                            Item ID
                          </th>
                          <th
                            style={{
                              textAlign: "left",
                              padding: "var(--space-3)",
                              fontSize: "var(--text-xs)",
                              fontWeight: 600,
                              color: "var(--gray-600)",
                              textTransform: "uppercase",
                            }}
                          >
                            Qty
                          </th>
                          <th
                            style={{
                              textAlign: "left",
                              padding: "var(--space-3)",
                              fontSize: "var(--text-xs)",
                              fontWeight: 600,
                              color: "var(--gray-600)",
                              textTransform: "uppercase",
                            }}
                          >
                            Price
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {orderItemsData.map((orderItem, index) => (
                          <tr
                            key={`${orderItem.order_id}-${orderItem.item_id}-${index}`}
                            style={{
                              borderBottom: "1px solid var(--gray-200)",
                            }}
                          >
                            <td
                              style={{
                                padding: "var(--space-3)",
                                fontSize: "var(--text-sm)",
                                color: "var(--gray-700)",
                              }}
                            >
                              {orderItem.order_id
                                ? orderItem.order_id.slice(0, 8) + "..."
                                : "—"}
                            </td>
                            <td
                              style={{
                                padding: "var(--space-3)",
                                fontSize: "var(--text-sm)",
                                color: "var(--gray-700)",
                              }}
                            >
                              {orderItem.item_id
                                ? orderItem.item_id.slice(0, 8) + "..."
                                : "—"}
                            </td>
                            <td
                              style={{
                                padding: "var(--space-3)",
                                fontSize: "var(--text-sm)",
                                color: "var(--gray-700)",
                                textAlign: "center",
                              }}
                            >
                              {orderItem.quantity}
                            </td>
                            <td
                              style={{
                                padding: "var(--space-3)",
                                fontSize: "var(--text-sm)",
                                color: "var(--primary-600)",
                                fontWeight: 600,
                              }}
                            >
                              ${orderItem.total_price?.toFixed(2) || "0.00"}
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  ) : (
                    <div
                      style={{
                        padding: "var(--space-8)",
                        textAlign: "center",
                        color: "var(--gray-500)",
                      }}
                    >
                      <p>
                        No order items found. Upload order items CSV to link
                        items to orders.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                {ordersDataType === "items" ? (
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Item ID
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Name
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Needed Employees
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Price
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {ordersData.map((item, index) => (
                        <tr
                          key={item.item_id || `item-${index}`}
                          style={{ borderBottom: "1px solid var(--gray-200)" }}
                        >
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                            }}
                          >
                            {item.item_id
                              ? item.item_id.slice(0, 8) + "..."
                              : "—"}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-base)",
                              color: "var(--gray-700)",
                              fontWeight: 600,
                            }}
                          >
                            {item.name}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-base)",
                              color: "var(--gray-700)",
                              textAlign: "center",
                            }}
                          >
                            {item.needed_employees}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-base)",
                              color: "var(--primary-600)",
                              fontWeight: 600,
                            }}
                          >
                            ${item.price?.toFixed(2) || "0.00"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                ) : (
                  <table style={{ width: "100%", borderCollapse: "collapse" }}>
                    <thead>
                      <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Order ID
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Driver ID
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Status
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Location
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Out for Delivery
                        </th>
                        <th
                          style={{
                            textAlign: "left",
                            padding: "var(--space-4)",
                            fontSize: "var(--text-sm)",
                            fontWeight: 600,
                            color: "var(--gray-600)",
                            textTransform: "uppercase",
                          }}
                        >
                          Delivered
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {ordersData.map((delivery, index) => (
                        <tr
                          key={delivery.order_id || `delivery-${index}`}
                          style={{ borderBottom: "1px solid var(--gray-200)" }}
                        >
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                            }}
                          >
                            {delivery.order_id
                              ? delivery.order_id.slice(0, 8) + "..."
                              : "—"}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                            }}
                          >
                            {delivery.driver_id
                              ? delivery.driver_id.slice(0, 8) + "..."
                              : "—"}
                          </td>
                          <td style={{ padding: "var(--space-4)" }}>
                            <span
                              style={{
                                padding: "4px 12px",
                                borderRadius: "var(--radius-full)",
                                fontSize: "var(--text-xs)",
                                fontWeight: 600,
                                backgroundColor:
                                  getStatusBadge(delivery.status) + "20",
                                color: getStatusBadge(delivery.status),
                              }}
                            >
                              {delivery.status}
                            </span>
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-700)",
                            }}
                          >
                            {delivery.location
                              ? `${delivery.location.latitude.toFixed(4)}, ${delivery.location.longitude.toFixed(4)}`
                              : "—"}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-500)",
                            }}
                          >
                            {delivery.out_for_delivery_time
                              ? new Date(
                                  delivery.out_for_delivery_time,
                                ).toLocaleString()
                              : "—"}
                          </td>
                          <td
                            style={{
                              padding: "var(--space-4)",
                              fontSize: "var(--text-sm)",
                              color: "var(--gray-500)",
                            }}
                          >
                            {delivery.delivered_time
                              ? new Date(
                                  delivery.delivered_time,
                                ).toLocaleString()
                              : "—"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="empty-state">
            <img src={OrdersIcon} alt="Orders" className="empty-icon-svg" />
            <h3>
              No{" "}
              {ordersDataType === "orders"
                ? "Orders"
                : ordersDataType === "items"
                  ? "Items"
                  : "Deliveries"}{" "}
              Found
            </h3>
            <p>Upload {ordersDataType} data to get started</p>
          </div>
        )}

        {/* Upload Orders Modal */}
        {showUploadOrders && (
          <div
            className="modal-overlay"
            onClick={() => setShowUploadOrders(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Orders CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowUploadOrders(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                onClick={() => ordersFileInput.current?.click()}
              >
                <img
                  src={CloudUploadIcon}
                  alt="Upload"
                  className="upload-icon-svg"
                />
                <h3 className="upload-title">Orders Data</h3>
                <p className="upload-description">Upload past orders history</p>
                <ul className="upload-specs">
                  <li>
                    Required: user_id, create_time, order_type, order_status,
                    total_amount, discount_amount
                  </li>
                  <li>Optional: rating</li>
                </ul>
                <input
                  ref={ordersFileInput}
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={handleOrdersUpload}
                />
              </div>
            </div>
          </div>
        )}

        {/* Upload Items Catalog Modal */}
        {showUploadItems && (
          <div
            className="modal-overlay"
            onClick={() => setShowUploadItems(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Items Catalog CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowUploadItems(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                onClick={() => itemsFileInput.current?.click()}
              >
                <img src={ItemsIcon} alt="Items" className="upload-icon-svg" />
                <h3 className="upload-title">Items Catalog Data</h3>
                <p className="upload-description">
                  Upload menu items for your organization
                </p>
                <ul className="upload-specs">
                  <li>Required: name, needed_employees, price</li>
                  <li>Each item name must be unique within the organization</li>
                </ul>
                <input
                  ref={itemsFileInput}
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={handleItemsUpload}
                />
              </div>
            </div>
          </div>
        )}

        {/* Upload Order Items Modal */}
        {showUploadOrderItems && (
          <div
            className="modal-overlay"
            onClick={() => setShowUploadOrderItems(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Order Items CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowUploadOrderItems(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                onClick={() => orderItemsFileInput.current?.click()}
              >
                <img
                  src={CloudUploadIcon}
                  alt="Upload"
                  className="upload-icon-svg"
                />
                <h3 className="upload-title">Order Items Relationship</h3>
                <p className="upload-description">
                  Link items to specific orders
                </p>
                <ul className="upload-specs">
                  <li>Required: order_id, item_id, quantity, total_price</li>
                  <li>
                    Prerequisites: Both Orders and Items must already exist
                  </li>
                </ul>
                <input
                  ref={orderItemsFileInput}
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={handleOrderItemsUpload}
                />
              </div>
            </div>
          </div>
        )}

        {/* Upload Deliveries Modal */}
        {showUploadDeliveries && (
          <div
            className="modal-overlay"
            onClick={() => setShowUploadDeliveries(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Deliveries CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowUploadDeliveries(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                onClick={() => deliveriesFileInput.current?.click()}
              >
                <img
                  src={CloudUploadIcon}
                  alt="Upload"
                  className="upload-icon-svg"
                />
                <h3 className="upload-title">Deliveries Data</h3>
                <p className="upload-description">
                  Upload delivery information
                </p>
                <ul className="upload-specs">
                  <li>
                    Required: order_id, driver_id, out_for_delivery_time, status
                  </li>
                  <li>
                    Optional: delivered_time, delivery_latitude,
                    delivery_longitude
                  </li>
                  <li>Prerequisites: Orders must exist</li>
                </ul>
                <input
                  ref={deliveriesFileInput}
                  type="file"
                  accept=".csv"
                  style={{ display: "none" }}
                  onChange={handleDeliveriesUpload}
                />
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ============================================================================
  // STAFFING PANEL - Employee Management
  // ============================================================================

  // Fetch employees
  const fetchEmployees = async () => {
    try {
      setLoading(true)
      const data = await api.staffing.getAllEmployees()
      setEmployees(data.employees || [])
    } catch (err) {
      setError(err.message || "Failed to load employees")
    } finally {
      setLoading(false)
    }
  }

  // Fetch roles
  const fetchRoles = async () => {
    try {
      const rolesResponse = await api.roles.getAll()
      console.log("Roles response:", rolesResponse)
      if (rolesResponse && rolesResponse.data) {
        setRoles(rolesResponse.data)
        console.log("Roles set to:", rolesResponse.data)
      }
    } catch (err) {
      console.error("Failed to load roles:", err)
    }
  }

  // Handle CSV upload
  const handleCsvUpload = async (event) => {
    const file = event.target.files[0]
    if (!file) return

    setDelegateLoading(true)
    setShowCsvUploadModal(false)

    try {
      const text = await file.text()
      const lines = text.split("\n").filter((line) => line.trim())

      if (lines.length < 2) {
        setActionMessage({
          type: "error",
          text: "CSV file is empty or invalid",
        })
        setTimeout(() => setActionMessage(null), 4000)
        return
      }

      // Parse header
      const headers = lines[0].split(",").map((h) => h.trim())
      const requiredHeaders = ["full_name", "email", "role", "salary_per_hour"]
      const missingHeaders = requiredHeaders.filter((h) => !headers.includes(h))

      if (missingHeaders.length > 0) {
        setActionMessage({
          type: "error",
          text: `Missing required columns: ${missingHeaders.join(", ")}`,
        })
        setTimeout(() => setActionMessage(null), 4000)
        return
      }

      // Parse and upload employees
      let successCount = 0
      let errorCount = 0
      const failedEmployees = []

      for (let i = 1; i < lines.length; i++) {
        const values = lines[i].split(",").map((v) => v.trim())
        if (values.length !== headers.length) continue

        const employee = {}
        headers.forEach((header, index) => {
          employee[header] = values[index]
        })

        try {
          console.log(
            `Attempting to create employee: ${employee.full_name} with role: ${employee.role}`,
          )
          await api.staffing.createEmployee({
            full_name: employee.full_name,
            email: employee.email,
            role: employee.role,
            salary_per_hour: parseFloat(employee.salary_per_hour),
            max_hours_per_week: employee.max_hours_per_week
              ? parseInt(employee.max_hours_per_week)
              : undefined,
            preferred_hours_per_week: employee.preferred_hours_per_week
              ? parseInt(employee.preferred_hours_per_week)
              : undefined,
          })
          console.log(`✓ Successfully created: ${employee.full_name}`)
          successCount++
        } catch (err) {
          console.error(
            `✗ Failed to create employee ${employee.full_name}:`,
            err,
          )
          failedEmployees.push({
            name: employee.full_name,
            role: employee.role,
            error: err.response?.data?.error || err.message || "Unknown error",
          })
          errorCount++
        }
      }

      // Refresh employee list
      await fetchEmployees()

      // Build detailed message
      let message = `Uploaded ${successCount} employee(s).`
      if (errorCount > 0) {
        message += ` ${errorCount} failed:\n`
        failedEmployees.forEach((emp) => {
          message += `\n• ${emp.name} (${emp.role}): ${emp.error}`
        })
      }

      setActionMessage({
        type: successCount > 0 ? "success" : "error",
        text: message,
      })
      setTimeout(() => setActionMessage(null), 8000)
    } catch (err) {
      console.error("CSV upload error:", err)
      setActionMessage({
        type: "error",
        text: err.message || "Failed to process CSV file",
      })
      setTimeout(() => setActionMessage(null), 4000)
    } finally {
      setDelegateLoading(false)
      event.target.value = "" // Reset file input
    }
  }

  // Fetch employee requests
  const fetchEmployeeRequests = async (employeeId) => {
    try {
      setRequestsLoading(true)
      const data = await api.requests.getEmployeeRequests(employeeId)
      setEmployeeRequests(data.requests || [])
    } catch (err) {
      console.error("Failed to load requests:", err)
      setEmployeeRequests([])
    } finally {
      setRequestsLoading(false)
    }
  }

  // Handle delegate submit
  const handleDelegateSubmit = async (e) => {
    e.preventDefault()
    setDelegateLoading(true)
    setDelegateError("")

    try {
      await api.staffing.createEmployee({
        ...delegateForm,
        salary_per_hour: parseFloat(delegateForm.salary_per_hour),
      })
      setShowDelegateModal(false)
      setDelegateForm({
        full_name: "",
        email: "",
        role: "",
        salary_per_hour: "",
      })
      setActionMessage({
        type: "success",
        text: "Employee delegated successfully. Email sent!",
      })
      fetchEmployees()
      setTimeout(() => setActionMessage(null), 4000)
    } catch (err) {
      setDelegateError(err.message || "Failed to delegate employee")
    } finally {
      setDelegateLoading(false)
    }
  }

  // Handle layoff
  const handleLayoff = async (employeeId) => {
    setActionLoading(true)
    try {
      await api.staffing.layoffEmployee(employeeId)
      setConfirmLayoff(null)
      setShowDetailModal(false)
      setActionMessage({
        type: "success",
        text: "Employee laid off successfully.",
      })
      fetchEmployees()
      setTimeout(() => setActionMessage(null), 4000)
    } catch (err) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to lay off employee",
      })
      setTimeout(() => setActionMessage(null), 4000)
    } finally {
      setActionLoading(false)
    }
  }

  // Handle approve request
  const handleApproveRequest = async (employeeId, requestId) => {
    try {
      await api.requests.approveRequest(employeeId, requestId)
      fetchEmployeeRequests(employeeId)
      setActionMessage({ type: "success", text: "Request approved." })
      setTimeout(() => setActionMessage(null), 3000)
    } catch (err) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to approve request",
      })
      setTimeout(() => setActionMessage(null), 3000)
    }
  }

  // Handle decline request
  const handleDeclineRequest = async (employeeId, requestId) => {
    try {
      await api.requests.declineRequest(employeeId, requestId)
      fetchEmployeeRequests(employeeId)
      setActionMessage({ type: "success", text: "Request declined." })
      setTimeout(() => setActionMessage(null), 3000)
    } catch (err) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to decline request",
      })
      setTimeout(() => setActionMessage(null), 3000)
    }
  }

  // Open employee detail
  const openEmployeeDetail = (emp) => {
    setSelectedEmployee(emp)
    setShowDetailModal(true)
    fetchEmployeeRequests(emp.id)
  }

  // Load employees and roles when staffing tab is active
  useEffect(() => {
    if (activeTab === "staffing") {
      fetchEmployees()
      fetchRoles()
    }
  }, [activeTab])

  const renderStaffing = () => {
    const filteredEmployees = employees.filter(
      (emp) =>
        emp.full_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.email?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        emp.user_role?.toLowerCase().includes(searchTerm.toLowerCase()),
    )

    const availableRoles = roles.filter((r) => r.role !== "admin")
    console.log("All roles:", roles)
    console.log("Available roles (filtered):", availableRoles)

    const thStyle = {
      textAlign: "left",
      padding: "var(--space-4)",
      fontSize: "var(--text-sm)",
      fontWeight: 600,
      color: "var(--gray-600)",
      textTransform: "uppercase",
      letterSpacing: "0.05em",
    }

    const tdStyle = {
      padding: "var(--space-4)",
      fontSize: "var(--text-base)",
      color: "var(--gray-700)",
      verticalAlign: "middle",
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Staffing Management</h1>
            <p className="page-subtitle">Manage your workforce</p>
          </div>
          <div style={{ display: "flex", gap: "var(--space-3)" }}>
            <button
              className="btn-secondary"
              onClick={() => setShowCsvUploadModal(true)}
            >
              📄 Upload CSV
            </button>
            <button
              className="btn-primary"
              onClick={() => setShowDelegateModal(true)}
            >
              + Delegate Employee
            </button>
          </div>
        </div>

        {/* Action Message Toast */}
        {actionMessage && (
          <div
            className={`alert-card ${actionMessage.type === "success" ? "alert-low" : "alert-high"}`}
            style={{ marginBottom: "var(--space-6)" }}
          >
            <p className="alert-message" style={{ whiteSpace: "pre-wrap" }}>
              {actionMessage.text}
            </p>
          </div>
        )}

        {/* Search Bar */}
        <div className="filter-bar">
          <input
            type="text"
            className="filter-select"
            placeholder="Search employees by name, email, or role..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            style={{ flex: 1, minWidth: 300 }}
          />
        </div>

        {/* Employees Table */}
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">
              Employees ({filteredEmployees.length})
            </h2>
          </div>

          {loading ? (
            <div className="skeleton-grid">
              {[1, 2, 3].map((i) => (
                <div key={i} className="skeleton-card">
                  <div className="skeleton-line skeleton-title"></div>
                  <div className="skeleton-line skeleton-value"></div>
                </div>
              ))}
            </div>
          ) : error ? (
            <div className="empty-state">
              <h3>Error Loading Employees</h3>
              <p>{error}</p>
              <button className="btn-primary" onClick={fetchEmployees}>
                Retry
              </button>
            </div>
          ) : filteredEmployees.length === 0 ? (
            <div className="empty-state">
              <h3>No Employees Found</h3>
              <p>
                {searchTerm
                  ? "Try a different search term"
                  : "Delegate your first employee to get started"}
              </p>
            </div>
          ) : (
            <div style={{ overflowX: "auto" }}>
              <table style={{ width: "100%", borderCollapse: "collapse" }}>
                <thead>
                  <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                    <th style={thStyle}>Name</th>
                    <th style={thStyle}>Email</th>
                    <th style={thStyle}>Role</th>
                    <th style={thStyle}>Salary/hr</th>
                    <th style={thStyle}>Joined</th>
                    <th style={thStyle}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredEmployees.map((emp) => (
                    <tr
                      key={emp.id}
                      style={{
                        borderBottom: "1px solid var(--gray-200)",
                        cursor: "pointer",
                        transition: "background var(--transition-fast)",
                      }}
                      onClick={() => openEmployeeDetail(emp)}
                      onMouseEnter={(e) =>
                        (e.currentTarget.style.background = "var(--primary-50)")
                      }
                      onMouseLeave={(e) =>
                        (e.currentTarget.style.background = "transparent")
                      }
                    >
                      <td style={tdStyle}>
                        <div
                          style={{
                            display: "flex",
                            alignItems: "center",
                            gap: "var(--space-3)",
                          }}
                        >
                          <div
                            className="user-avatar"
                            style={{
                              width: 32,
                              height: 32,
                              fontSize: "var(--text-xs)",
                            }}
                          >
                            {emp.full_name
                              ?.split(" ")
                              .map((n) => n[0])
                              .join("")
                              .toUpperCase()
                              .slice(0, 2)}
                          </div>
                          {emp.full_name}
                        </div>
                      </td>
                      <td style={tdStyle}>{emp.email}</td>
                      <td style={tdStyle}>
                        <span className="badge badge-primary">
                          {emp.user_role}
                        </span>
                      </td>
                      <td style={tdStyle}>
                        {emp.salary_per_hour != null
                          ? `$${emp.salary_per_hour}`
                          : "—"}
                      </td>
                      <td style={tdStyle}>
                        {emp.created_at
                          ? new Date(emp.created_at).toLocaleDateString()
                          : "—"}
                      </td>
                      <td style={tdStyle}>
                        {emp.user_role !== "admin" && (
                          <button
                            className="btn-link"
                            style={{ color: "var(--color-accent)" }}
                            onClick={(e) => {
                              e.stopPropagation()
                              setConfirmLayoff(emp)
                            }}
                          >
                            Lay Off
                          </button>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>

        {/* Delegate Employee Modal */}
        {showDelegateModal && (
          <div
            className="modal-overlay"
            onClick={() => setShowDelegateModal(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Delegate New Employee</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowDelegateModal(false)}
                >
                  ×
                </button>
              </div>
              {delegateError && (
                <div
                  className="login-error-message"
                  style={{ marginBottom: "var(--space-4)" }}
                >
                  {delegateError}
                </div>
              )}
              <form onSubmit={handleDelegateSubmit}>
                <div
                  style={{
                    display: "flex",
                    flexDirection: "column",
                    gap: "var(--space-4)",
                  }}
                >
                  <div className="setting-item">
                    <label className="setting-label">Full Name</label>
                    <input
                      className="setting-input"
                      type="text"
                      value={delegateForm.full_name}
                      onChange={(e) =>
                        setDelegateForm({
                          ...delegateForm,
                          full_name: e.target.value,
                        })
                      }
                      placeholder="Employee full name"
                      required
                    />
                  </div>
                  <div className="setting-item">
                    <label className="setting-label">Email</label>
                    <input
                      className="setting-input"
                      type="email"
                      value={delegateForm.email}
                      onChange={(e) =>
                        setDelegateForm({
                          ...delegateForm,
                          email: e.target.value,
                        })
                      }
                      placeholder="Employee email"
                      required
                    />
                  </div>
                  <div className="setting-item">
                    <label className="setting-label">Role</label>
                    <select
                      className="setting-input"
                      value={delegateForm.role}
                      onChange={(e) =>
                        setDelegateForm({
                          ...delegateForm,
                          role: e.target.value,
                        })
                      }
                      required
                    >
                      <option value="">Select a role...</option>
                      <option value="manager">manager</option>
                      <option value="employee">employee</option>
                    </select>
                  </div>
                  <div className="setting-item">
                    <label className="setting-label">Salary per Hour ($)</label>
                    <input
                      className="setting-input"
                      type="number"
                      step="0.01"
                      min="0"
                      value={delegateForm.salary_per_hour}
                      onChange={(e) =>
                        setDelegateForm({
                          ...delegateForm,
                          salary_per_hour: e.target.value,
                        })
                      }
                      placeholder="15.50"
                      required
                    />
                  </div>
                </div>
                <div
                  className="settings-footer"
                  style={{ marginTop: "var(--space-6)" }}
                >
                  <button
                    type="button"
                    className="btn-secondary"
                    onClick={() => setShowDelegateModal(false)}
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="btn-primary"
                    disabled={delegateLoading}
                  >
                    {delegateLoading ? "Sending..." : "Delegate Employee"}
                  </button>
                </div>
              </form>
            </div>
          </div>
        )}

        {/* Employee Detail Modal */}
        {showDetailModal && selectedEmployee && (
          <div
            className="modal-overlay"
            onClick={() => setShowDetailModal(false)}
          >
            <div
              className="modal-content modal-wide"
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2 className="section-title">{selectedEmployee.full_name}</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowDetailModal(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="kpi-grid"
                style={{ marginBottom: "var(--space-6)" }}
              >
                <div className="kpi-card">
                  <div className="kpi-content">
                    <h3 className="kpi-label">Role</h3>
                    <div
                      className="kpi-value"
                      style={{ fontSize: "var(--text-xl)" }}
                    >
                      {selectedEmployee.user_role}
                    </div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-content">
                    <h3 className="kpi-label">Email</h3>
                    <div
                      className="kpi-value"
                      style={{
                        fontSize: "var(--text-sm)",
                        wordBreak: "break-all",
                      }}
                    >
                      {selectedEmployee.email}
                    </div>
                  </div>
                </div>
                <div className="kpi-card">
                  <div className="kpi-content">
                    <h3 className="kpi-label">Salary/hr</h3>
                    <div
                      className="kpi-value"
                      style={{ fontSize: "var(--text-xl)" }}
                    >
                      {selectedEmployee.salary_per_hour != null
                        ? `$${selectedEmployee.salary_per_hour}`
                        : "—"}
                    </div>
                  </div>
                </div>
              </div>

              {/* Requests Section */}
              <div
                className="section-wrapper"
                style={{
                  boxShadow: "none",
                  border: "1px solid var(--gray-200)",
                }}
              >
                <div className="section-header">
                  <h2
                    className="section-title"
                    style={{ fontSize: "var(--text-lg)" }}
                  >
                    Requests
                  </h2>
                </div>
                {requestsLoading ? (
                  <div className="skeleton-grid">
                    <div className="skeleton-card">
                      <div className="skeleton-line skeleton-title"></div>
                    </div>
                  </div>
                ) : employeeRequests.length === 0 ? (
                  <p
                    style={{
                      color: "var(--gray-500)",
                      textAlign: "center",
                      padding: "var(--space-4)",
                    }}
                  >
                    No requests from this employee
                  </p>
                ) : (
                  <div className="alerts-grid">
                    {employeeRequests.map((req) => (
                      <div
                        key={req.id}
                        className={`alert-card ${req.status === "pending" ? "alert-medium" : req.status === "approved" ? "alert-low" : "alert-high"}`}
                      >
                        <div className="alert-header">
                          <div
                            className={`alert-badge ${req.status === "pending" ? "priority-medium" : req.status === "approved" ? "priority-low" : "priority-high"}`}
                          >
                            {req.status?.toUpperCase()}
                          </div>
                          <span className="alert-timestamp">
                            {req.request_type}
                          </span>
                        </div>
                        <p className="alert-message">
                          {req.reason || "No reason provided"} —{" "}
                          {req.start_date} to {req.end_date}
                        </p>
                        {req.status === "pending" && (
                          <div className="alert-actions">
                            <button
                              className="btn-primary btn-sm"
                              onClick={() =>
                                handleApproveRequest(
                                  selectedEmployee.id,
                                  req.id,
                                )
                              }
                            >
                              Approve
                            </button>
                            <button
                              className="btn-link"
                              style={{ color: "var(--color-accent)" }}
                              onClick={() =>
                                handleDeclineRequest(
                                  selectedEmployee.id,
                                  req.id,
                                )
                              }
                            >
                              Decline
                            </button>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {selectedEmployee.user_role !== "admin" && (
                <div className="settings-footer">
                  <button
                    className="btn-secondary"
                    style={{
                      borderColor: "var(--color-accent)",
                      color: "var(--color-accent)",
                    }}
                    onClick={() => setConfirmLayoff(selectedEmployee)}
                  >
                    Lay Off Employee
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Confirm Layoff Modal */}
        {confirmLayoff && (
          <div className="modal-overlay" onClick={() => setConfirmLayoff(null)}>
            <div
              className="modal-content"
              onClick={(e) => e.stopPropagation()}
              style={{ maxWidth: 440 }}
            >
              <div className="modal-header">
                <h2
                  className="section-title"
                  style={{ color: "var(--color-accent)" }}
                >
                  Confirm Layoff
                </h2>
              </div>
              <p
                style={{
                  color: "var(--text-primary)",
                  marginBottom: "var(--space-6)",
                  lineHeight: 1.6,
                }}
              >
                Are you sure you want to lay off{" "}
                <strong>{confirmLayoff.full_name}</strong>? This action cannot
                be undone.
              </p>
              <div className="settings-footer">
                <button
                  className="btn-secondary"
                  onClick={() => setConfirmLayoff(null)}
                >
                  Cancel
                </button>
                <button
                  className="btn-primary"
                  style={{ background: "var(--color-accent)" }}
                  onClick={() => handleLayoff(confirmLayoff.id)}
                  disabled={actionLoading}
                >
                  {actionLoading ? "Processing..." : "Confirm Layoff"}
                </button>
              </div>
            </div>
          </div>
        )}

        {/* CSV Upload Modal */}
        {showCsvUploadModal && (
          <div
            className="modal-overlay"
            onClick={() => setShowCsvUploadModal(false)}
          >
            <div className="modal-content" onClick={(e) => e.stopPropagation()}>
              <div className="modal-header">
                <h2 className="section-title">Upload Employee CSV</h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowCsvUploadModal(false)}
                >
                  ×
                </button>
              </div>
              <div
                className="upload-card"
                style={{
                  border: "2px dashed var(--gray-300)",
                  marginBottom: "var(--space-4)",
                }}
              >
                <input
                  type="file"
                  ref={csvFileInput}
                  onChange={handleCsvUpload}
                  style={{ display: "none" }}
                  accept=".csv,.xlsx"
                />
                <img
                  src={EmployeeIcon}
                  alt="Employees"
                  className="upload-icon-svg"
                />
                <h3 className="upload-title">Employee Roster CSV</h3>
                <p className="upload-description">
                  Import your complete employee list with contact details
                </p>
                <ul className="upload-specs">
                  <li>Supported formats: CSV, XLSX</li>
                  <li>Maximum size: 25MB</li>
                  <li>
                    Required columns: full_name, email, role, salary_per_hour
                  </li>
                  <li>
                    Optional: max_hours_per_week, preferred_hours_per_week
                  </li>
                </ul>
                <button
                  className="btn-primary"
                  onClick={() => csvFileInput.current?.click()}
                >
                  Choose File
                </button>
              </div>
              <div className="settings-footer">
                <button
                  className="btn-secondary"
                  onClick={() => setShowCsvUploadModal(false)}
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    )
  }

  // ============================================================================
  // ROLE MANAGEMENT FUNCTIONS
  // ============================================================================

  // Handle add role submit
  const handleAddRole = async (e) => {
    e.preventDefault()
    setRoleLoading(true)
    setRoleError("")

    try {
      const payload = {
        role: roleForm.role,
        min_needed_per_shift: parseInt(roleForm.min_needed_per_shift),
        need_for_demand: roleForm.need_for_demand,
        independent: roleForm.independent,
      }

      if (roleForm.need_for_demand && roleForm.items_per_role_per_hour) {
        payload.items_per_role_per_hour = parseInt(
          roleForm.items_per_role_per_hour,
        )
      }

      await api.roles.createRole(payload)
      setShowAddRoleModal(false)
      setRoleForm({
        role: "",
        min_needed_per_shift: 1,
        items_per_role_per_hour: "",
        need_for_demand: false,
        independent: true,
      })
      setActionMessage({
        type: "success",
        text: "Role created successfully!",
      })
      fetchRoles()
      setTimeout(() => setActionMessage(null), 4000)
    } catch (err) {
      setRoleError(err.message || "Failed to create role")
    } finally {
      setRoleLoading(false)
    }
  }

  // Handle edit role submit
  const handleEditRole = async (e) => {
    e.preventDefault()
    setRoleLoading(true)
    setRoleError("")

    try {
      const payload = {
        min_needed_per_shift: parseInt(roleForm.min_needed_per_shift),
        need_for_demand: roleForm.need_for_demand,
        independent: roleForm.independent,
      }

      if (roleForm.need_for_demand && roleForm.items_per_role_per_hour) {
        payload.items_per_role_per_hour = parseInt(
          roleForm.items_per_role_per_hour,
        )
      } else {
        payload.items_per_role_per_hour = null
      }

      await api.roles.updateRole(selectedRole.role, payload)
      setShowEditRoleModal(false)
      setSelectedRole(null)
      setActionMessage({
        type: "success",
        text: "Role updated successfully!",
      })
      fetchRoles()
      setTimeout(() => setActionMessage(null), 4000)
    } catch (err) {
      setRoleError(err.message || "Failed to update role")
    } finally {
      setRoleLoading(false)
    }
  }

  // Handle delete role
  const handleDeleteRole = async (roleName) => {
    setActionLoading(true)
    try {
      await api.roles.deleteRole(roleName)
      setConfirmDeleteRole(null)
      setActionMessage({
        type: "success",
        text: "Role deleted successfully.",
      })
      fetchRoles()
      setTimeout(() => setActionMessage(null), 4000)
    } catch (err) {
      setActionMessage({
        type: "error",
        text: err.message || "Failed to delete role",
      })
      setTimeout(() => setActionMessage(null), 4000)
    } finally {
      setActionLoading(false)
    }
  }

  // Open edit role modal
  const openEditRole = (role) => {
    setSelectedRole(role)
    setRoleForm({
      role: role.role,
      min_needed_per_shift: role.min_needed_per_shift || 1,
      items_per_role_per_hour: role.items_per_role_per_hour || "",
      need_for_demand: role.need_for_demand || false,
      independent: role.independent !== undefined ? role.independent : true,
    })
    setShowEditRoleModal(true)
  }

  const renderInfo = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Organization Setup</h1>
          <p className="page-subtitle">
            Configure your organization location and roles
          </p>
        </div>
      </div>

      {/* Action Message Toast */}
      {actionMessage && (
        <div
          className={`alert-card ${actionMessage.type === "success" ? "alert-low" : "alert-high"}`}
          style={{ marginBottom: "var(--space-6)" }}
        >
          <p className="alert-message" style={{ whiteSpace: "pre-wrap" }}>
            {actionMessage.text}
          </p>
        </div>
      )}



      {/* Shift Rules Section */}
      <div className="section-wrapper">
        <div className="section-header">
          <h2 className="section-title">
            <img
              src={ScheduleIcon}
              alt="Shift Rules"
              className="title-icon-svg"
            />
            Shift Rules
          </h2>
        </div>
        <p className="section-description">
          Configure shift scheduling parameters for your organization
        </p>
        <div className="settings-grid" style={{ marginTop: "var(--space-4)" }}>
          <div className="setting-item">
            <label className="setting-label">Minimum Shift Length</label>
            <select className="setting-input">
              <option>4 hours</option>
              <option>6 hours</option>
              <option>8 hours</option>
            </select>
          </div>
          <div className="setting-item">
            <label className="setting-label">Maximum Shift Length</label>
            <select className="setting-input">
              <option>8 hours</option>
              <option>10 hours</option>
              <option>12 hours</option>
            </select>
          </div>
          <div className="setting-item">
            <label className="setting-label">Break Duration</label>
            <select className="setting-input">
              <option>15 minutes</option>
              <option>30 minutes</option>
              <option>60 minutes</option>
            </select>
          </div>
          <div className="setting-item">
            <label className="setting-label">Grace Period</label>
            <select className="setting-input">
              <option>5 minutes</option>
              <option>10 minutes</option>
              <option>15 minutes</option>
            </select>
          </div>
        </div>
        <div
          className="settings-footer"
          style={{ marginTop: "var(--space-6)" }}
        >
          <button className="btn-secondary">Reset to Defaults</button>
          <button className="btn-primary">Save Shift Rules</button>
        </div>
      </div>

      {/* Roles Management Section */}
      <div className="section-wrapper">
        <div className="section-header">
          <div>
            <h2 className="section-title">
              <img src={EmployeeIcon} alt="Roles" className="title-icon-svg" />
              Organization Roles
            </h2>
            <p className="section-description">
              Define roles for your organization and their requirements
            </p>
          </div>
          <button
            className="btn-primary"
            onClick={() => {
              setRoleForm({
                role: "",
                min_needed_per_shift: 1,
                items_per_role_per_hour: "",
                need_for_demand: false,
                independent: true,
              })
              setRoleError("")
              setShowAddRoleModal(true)
            }}
          >
            + Add Role
          </button>
        </div>

        {roles && roles.length > 0 ? (
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse" }}>
              <thead>
                <tr style={{ borderBottom: "2px solid var(--gray-200)" }}>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Role Name
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Min per Shift
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Demand Based
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Items/Hour
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Independent
                  </th>
                  <th
                    style={{
                      textAlign: "left",
                      padding: "var(--space-4)",
                      fontSize: "var(--text-sm)",
                      fontWeight: 600,
                      color: "var(--gray-600)",
                      textTransform: "uppercase",
                      letterSpacing: "0.05em",
                    }}
                  >
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody>
                {roles.map((role) => (
                  <tr
                    key={role.role}
                    style={{
                      borderBottom: "1px solid var(--gray-200)",
                    }}
                  >
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      <span className="badge badge-primary">{role.role}</span>
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.min_needed_per_shift}
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.need_for_demand ? (
                        <span style={{ color: "var(--color-primary)" }}>
                          ✓ Yes
                        </span>
                      ) : (
                        <span style={{ color: "var(--gray-400)" }}>✗ No</span>
                      )}
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.items_per_role_per_hour != null
                        ? role.items_per_role_per_hour
                        : "—"}
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.independent ? (
                        <span style={{ color: "var(--color-primary)" }}>
                          ✓ Yes
                        </span>
                      ) : (
                        <span style={{ color: "var(--gray-400)" }}>✗ No</span>
                      )}
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.role !== "admin" && role.role !== "manager" && (
                        <>
                          <button
                            className="btn-link"
                            style={{ marginRight: "var(--space-2)" }}
                            onClick={() => openEditRole(role)}
                          >
                            Edit
                          </button>
                          <button
                            className="btn-link"
                            style={{ color: "var(--color-accent)" }}
                            onClick={() => setConfirmDeleteRole(role)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                      {(role.role === "admin" || role.role === "manager") && (
                        <span
                          style={{
                            color: "var(--gray-400)",
                            fontSize: "var(--text-sm)",
                          }}
                        >
                          Default Role
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="empty-state">
            <h3>No Roles Defined</h3>
            <p>Add your first role to get started</p>
          </div>
        )}
      </div>

      {/* Add Role Modal */}
      {showAddRoleModal && (
        <div
          className="modal-overlay"
          onClick={() => setShowAddRoleModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="section-title">Add New Role</h2>
              <button
                className="collapse-btn"
                onClick={() => setShowAddRoleModal(false)}
              >
                ×
              </button>
            </div>
            {roleError && (
              <div
                className="login-error-message"
                style={{ marginBottom: "var(--space-4)" }}
              >
                {roleError}
              </div>
            )}
            <form onSubmit={handleAddRole}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-4)",
                }}
              >
                <div className="setting-item">
                  <label className="setting-label">Role Name</label>
                  <input
                    className="setting-input"
                    type="text"
                    value={roleForm.role}
                    onChange={(e) =>
                      setRoleForm({ ...roleForm, role: e.target.value })
                    }
                    placeholder="e.g., waiter, cashier, cook"
                    required
                  />
                </div>
                <div className="setting-item">
                  <label className="setting-label">
                    Minimum Needed per Shift
                  </label>
                  <input
                    className="setting-input"
                    type="number"
                    min="0"
                    value={roleForm.min_needed_per_shift}
                    onChange={(e) =>
                      setRoleForm({
                        ...roleForm,
                        min_needed_per_shift: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="toggle-item">
                  <div className="toggle-content">
                    <h4 className="toggle-title">Need for Demand</h4>
                    <p className="toggle-description">
                      Is this role required based on demand/capacity?
                    </p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={roleForm.need_for_demand}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          need_for_demand: e.target.checked,
                        })
                      }
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
                {roleForm.need_for_demand && (
                  <div className="setting-item">
                    <label className="setting-label">
                      Items per Role per Hour
                    </label>
                    <input
                      className="setting-input"
                      type="number"
                      min="0"
                      value={roleForm.items_per_role_per_hour}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          items_per_role_per_hour: e.target.value,
                        })
                      }
                      placeholder="e.g., 10"
                      required={roleForm.need_for_demand}
                    />
                    <p
                      style={{
                        fontSize: "var(--text-sm)",
                        color: "var(--gray-500)",
                        marginTop: "var(--space-2)",
                      }}
                    >
                      How many items/customers this role can handle per hour
                    </p>
                  </div>
                )}
                <div className="toggle-item">
                  <div className="toggle-content">
                    <h4 className="toggle-title">Independent Role</h4>
                    <p className="toggle-description">
                      Can this role work independently?
                    </p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={roleForm.independent}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          independent: e.target.checked,
                        })
                      }
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>
              <div
                className="settings-footer"
                style={{ marginTop: "var(--space-6)" }}
              >
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowAddRoleModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={roleLoading}
                >
                  {roleLoading ? "Creating..." : "Create Role"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Role Modal */}
      {showEditRoleModal && selectedRole && (
        <div
          className="modal-overlay"
          onClick={() => setShowEditRoleModal(false)}
        >
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2 className="section-title">Edit Role: {selectedRole.role}</h2>
              <button
                className="collapse-btn"
                onClick={() => setShowEditRoleModal(false)}
              >
                ×
              </button>
            </div>
            {roleError && (
              <div
                className="login-error-message"
                style={{ marginBottom: "var(--space-4)" }}
              >
                {roleError}
              </div>
            )}
            <form onSubmit={handleEditRole}>
              <div
                style={{
                  display: "flex",
                  flexDirection: "column",
                  gap: "var(--space-4)",
                }}
              >
                <div className="setting-item">
                  <label className="setting-label">
                    Minimum Needed per Shift
                  </label>
                  <input
                    className="setting-input"
                    type="number"
                    min="0"
                    value={roleForm.min_needed_per_shift}
                    onChange={(e) =>
                      setRoleForm({
                        ...roleForm,
                        min_needed_per_shift: e.target.value,
                      })
                    }
                    required
                  />
                </div>
                <div className="toggle-item">
                  <div className="toggle-content">
                    <h4 className="toggle-title">Need for Demand</h4>
                    <p className="toggle-description">
                      Is this role required based on demand/capacity?
                    </p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={roleForm.need_for_demand}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          need_for_demand: e.target.checked,
                        })
                      }
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
                {roleForm.need_for_demand && (
                  <div className="setting-item">
                    <label className="setting-label">
                      Items per Role per Hour
                    </label>
                    <input
                      className="setting-input"
                      type="number"
                      min="0"
                      value={roleForm.items_per_role_per_hour}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          items_per_role_per_hour: e.target.value,
                        })
                      }
                      placeholder="e.g., 10"
                      required={roleForm.need_for_demand}
                    />
                  </div>
                )}
                <div className="toggle-item">
                  <div className="toggle-content">
                    <h4 className="toggle-title">Independent Role</h4>
                    <p className="toggle-description">
                      Can this role work independently?
                    </p>
                  </div>
                  <label className="toggle-switch">
                    <input
                      type="checkbox"
                      checked={roleForm.independent}
                      onChange={(e) =>
                        setRoleForm({
                          ...roleForm,
                          independent: e.target.checked,
                        })
                      }
                    />
                    <span className="toggle-slider"></span>
                  </label>
                </div>
              </div>
              <div
                className="settings-footer"
                style={{ marginTop: "var(--space-6)" }}
              >
                <button
                  type="button"
                  className="btn-secondary"
                  onClick={() => setShowEditRoleModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn-primary"
                  disabled={roleLoading}
                >
                  {roleLoading ? "Updating..." : "Update Role"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Delete Role Confirmation */}
      {confirmDeleteRole && (
        <div
          className="modal-overlay"
          onClick={() => setConfirmDeleteRole(null)}
        >
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: 440 }}
          >
            <div className="modal-header">
              <h2
                className="section-title"
                style={{ color: "var(--color-accent)" }}
              >
                Confirm Delete
              </h2>
            </div>
            <p
              style={{
                color: "var(--text-primary)",
                marginBottom: "var(--space-6)",
                lineHeight: 1.6,
              }}
            >
              Are you sure you want to delete the role{" "}
              <strong>{confirmDeleteRole.role}</strong>? This action cannot be
              undone and may fail if employees are assigned to this role.
            </p>
            <div className="settings-footer">
              <button
                className="btn-secondary"
                onClick={() => setConfirmDeleteRole(null)}
              >
                Cancel
              </button>
              <button
                className="btn-primary"
                style={{ background: "var(--color-accent)" }}
                onClick={() => handleDeleteRole(confirmDeleteRole.role)}
                disabled={actionLoading}
              >
                {actionLoading ? "Deleting..." : "Confirm Delete"}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  const renderAdminProfile = () => {
    console.log("Rendering profile with currentUser:", currentUser)

    const userInitials = currentUser?.full_name
      ? currentUser.full_name
          .split(" ")
          .map((n) => n[0])
          .join("")
          .toUpperCase()
          .slice(0, 2)
      : "AD"

    // Get data from currentUser, no fallback hardcoded values in display
    const displayName = currentUser?.full_name || "Loading..."
    const displayEmail = currentUser?.email || "Loading..."
    const displayRole = currentUser?.user_role || "Loading..."

    return (
      <>
        <div
          className={`admin-profile-overlay ${showAdminProfile ? "show" : ""}`}
        >
          <div className="admin-profile-modal fade-in">
            <button
              className="profile-close-btn"
              onClick={() => setShowAdminProfile(false)}
              aria-label="Close Profile"
            >
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M6 18L18 6M6 6l12 12"
                />
              </svg>
            </button>

            <div className="profile-header-section">
              <div className="profile-avatar-large">
                <div className="avatar-gradient">{userInitials}</div>
              </div>
              <div className="profile-header-info">
                <h1 className="profile-name">{displayName}</h1>
                <p className="profile-role">{displayRole}</p>
              </div>
            </div>

            <div className="profile-content-grid">
              {/* Personal Information Card */}
              <div className="profile-card" data-animation="slide-up">
                <div className="profile-card-header">
                  <h3 className="profile-card-title">
                    <svg
                      className="card-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
                      />
                    </svg>
                    Personal Information
                  </h3>
                </div>
                <div className="profile-info-grid">
                  <div className="info-item">
                    <span className="info-label">Full Name</span>
                    <span className="info-value">{displayName}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Email</span>
                    <span className="info-value">{displayEmail}</span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Role</span>
                    <span
                      className="info-value"
                      style={{ textTransform: "capitalize" }}
                    >
                      {displayRole}
                    </span>
                  </div>
                  <div className="info-item">
                    <span className="info-label">Organization</span>
                    <span className="info-value">
                      {currentUser?.organization_name ||
                        currentUser?.organization ||
                        "N/A"}
                    </span>
                  </div>
                </div>
              </div>

              {/* Account Statistics Card */}
              <div
                className="profile-card"
                data-animation="slide-up"
                style={{ animationDelay: "0.1s" }}
              >
                <div className="profile-card-header">
                  <h3 className="profile-card-title">
                    <svg
                      className="card-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
                      />
                    </svg>
                    Organization Statistics
                  </h3>
                </div>
                <div className="profile-stats-grid">
                  <div className="stat-item">
                    <div className="stat-value">{totalHeadcount}</div>
                    <div className="stat-label">Total Employees</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{roles.length}</div>
                    <div className="stat-label">Active Roles</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{currentlyClocked}</div>
                    <div className="stat-label">Currently Clocked</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">
                      ${(laborCost / 1000).toFixed(1)}K
                    </div>
                    <div className="stat-label">Labor Cost</div>
                  </div>
                </div>
              </div>

              {/* Security Settings Card */}
              <div
                className="profile-card profile-card-full"
                data-animation="slide-up"
                style={{ animationDelay: "0.2s" }}
              >
                <div className="profile-card-header">
                  <h3 className="profile-card-title">
                    <svg
                      className="card-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
                      />
                    </svg>
                    Security & Account
                  </h3>
                </div>

                <div className="password-change-section">
                  <h4 className="section-subtitle">
                    <svg
                      className="subtitle-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"
                      />
                    </svg>
                    Change Password
                  </h4>

                  {passwordError && (
                    <div
                      className="login-error-message"
                      style={{ marginBottom: "var(--space-4)" }}
                    >
                      {passwordError}
                    </div>
                  )}
                  {passwordSuccess && (
                    <div
                      className="login-error-message"
                      style={{
                        marginBottom: "var(--space-4)",
                        background: "var(--secondary-50)",
                        color: "var(--color-secondary)",
                        borderColor: "var(--color-secondary)",
                      }}
                    >
                      {passwordSuccess}
                    </div>
                  )}

                  <form
                    onSubmit={handleChangePassword}
                    className="password-form"
                  >
                    <div className="password-form-grid">
                      <div className="form-group">
                        <label htmlFor="old_password" className="form-label">
                          Current Password
                        </label>
                        <input
                          type="password"
                          id="old_password"
                          className="form-input"
                          value={passwordForm.old_password}
                          onChange={(e) =>
                            setPasswordForm({
                              ...passwordForm,
                              old_password: e.target.value,
                            })
                          }
                          required
                          minLength={6}
                          disabled={passwordLoading}
                          placeholder="Enter current password"
                        />
                      </div>
                      <div className="form-group">
                        <label htmlFor="new_password" className="form-label">
                          New Password
                        </label>
                        <input
                          type="password"
                          id="new_password"
                          className="form-input"
                          value={passwordForm.new_password}
                          onChange={(e) =>
                            setPasswordForm({
                              ...passwordForm,
                              new_password: e.target.value,
                            })
                          }
                          required
                          minLength={6}
                          disabled={passwordLoading}
                          placeholder="Enter new password"
                        />
                      </div>
                      <div className="form-group">
                        <label
                          htmlFor="confirm_password"
                          className="form-label"
                        >
                          Confirm New Password
                        </label>
                        <input
                          type="password"
                          id="confirm_password"
                          className="form-input"
                          value={passwordForm.confirm_password}
                          onChange={(e) =>
                            setPasswordForm({
                              ...passwordForm,
                              confirm_password: e.target.value,
                            })
                          }
                          required
                          minLength={6}
                          disabled={passwordLoading}
                          placeholder="Confirm new password"
                        />
                      </div>
                    </div>
                    <button
                      type="submit"
                      className="btn-primary password-submit-btn"
                      disabled={passwordLoading}
                    >
                      {passwordLoading
                        ? "Changing Password..."
                        : "Update Password"}
                    </button>
                  </form>
                </div>

                <div className="security-info">
                  <div className="info-row">
                    <svg
                      className="info-icon"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                      />
                    </svg>
                    <div>
                      <div className="info-title">Account Status</div>
                      <div className="info-subtitle">Active</div>
                    </div>
                  </div>
                  {currentUser?.created_at && (
                    <div className="info-row">
                      <svg
                        className="info-icon"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
                        />
                      </svg>
                      <div>
                        <div className="info-title">Member Since</div>
                        <div className="info-subtitle">
                          {new Date(currentUser.created_at).toLocaleDateString(
                            "en-US",
                            {
                              year: "numeric",
                              month: "long",
                              day: "numeric",
                            },
                          )}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="profile-footer">
              <button
                className="btn-secondary"
                onClick={() => setShowAdminProfile(false)}
              >
                Close Profile
              </button>
            </div>
          </div>
        </div>
      </>
    )
  }

  return (
    <div className={`dashboard-wrapper ${darkMode ? "dark-mode" : ""}`}>
      {/* Premium Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          <div className="logo-wrapper">
            {sidebarCollapsed ? (
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
                <span className="logo-badge">Admin</span>
              </>
            )}
          </div>
          <button
            className="collapse-btn"
            onClick={() => setSidebarCollapsed(!sidebarCollapsed)}
          >
            {sidebarCollapsed ? "→" : "←"}
          </button>
        </div>

        <nav className="nav-menu">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={`nav-item ${activeTab === item.id ? "active" : ""}`}
              onClick={() => setActiveTab(item.id)}
            >
              <img src={item.icon} alt={item.label} className="nav-icon" />
              {!sidebarCollapsed && (
                <span className="nav-label">{item.label}</span>
              )}
              {activeTab === item.id && (
                <div className="active-indicator"></div>
              )}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <div className="theme-toggle-container">
            <button
              className={`theme-toggle-switch ${darkMode ? "dark" : "light"}`}
              onClick={toggleDarkMode}
              title={darkMode ? "Switch to Light Mode" : "Switch to Dark Mode"}
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
            {!sidebarCollapsed && (
              <span className="theme-label">
                {darkMode ? "Dark Mode" : "Light Mode"}
              </span>
            )}
          </div>
          <div className="user-profile">
            <div
              className="user-avatar user-avatar-clickable"
              onClick={() => setShowAdminProfile(true)}
              title="View Profile"
            >
              {currentUser?.full_name
                ? currentUser.full_name
                    .split(" ")
                    .map((n) => n[0])
                    .join("")
                    .toUpperCase()
                    .slice(0, 2)
                : "..."}
            </div>
            {!sidebarCollapsed && (
              <div className="user-info">
                <div className="user-name">
                  {currentUser?.full_name || "Loading..."}
                </div>
                <div className="user-role">
                  {currentUser?.role || "Loading..."}
                </div>
              </div>
            )}
          </div>
          {!sidebarCollapsed && <button className="logout-btn">Logout</button>}
        </div>
      </aside>

      {/* Main Content */}
      <main className="main-content">
        {loading && renderSkeletonLoader()}
        {error && !loading && (
          <div className="error-state">
            <img
              src={MissedTargetIcon}
              alt="Error"
              className="error-icon-svg"
            />
            <h3>Error Loading Dashboard</h3>
            <p>{error}</p>
            <button className="btn-primary" onClick={fetchDashboardData}>
              Retry
            </button>
          </div>
        )}
        {!loading && (
          <>
            {activeTab === "home" && renderHomeDashboard()}
            {activeTab === "schedule" && renderMasterSchedule()}
            {activeTab === "insights" && renderInsights()}
            {activeTab === "campaigns" && renderCampaigns()}{" "}
            {/* Changed from "planning" */}
            {activeTab === "staffing" && renderStaffing()}
            {activeTab === "orders" && renderOrders()}
            {activeTab === "info" && renderInfo()}
          </>
        )}
        {renderAdminProfile()}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav">
        {navigationItems.slice(0, 5).map((item) => (
          <button
            key={item.id}
            className={`mobile-nav-item ${activeTab === item.id ? "active" : ""}`}
            onClick={() => setActiveTab(item.id)}
          >
            <img src={item.icon} alt={item.label} className="mobile-nav-icon" />
            <span className="mobile-nav-label">{item.label}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}

export default AdminDashboard
