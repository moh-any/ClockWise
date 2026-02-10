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
import MagicIcon from "./Icons/Magic-Icon.svg"
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
  const [predictionLoading, setPredictionLoading] = useState(false)
  const [predictionError, setPredictionError] = useState("")
  const [predictionSuccess, setPredictionSuccess] = useState("")

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
  const [selectedCoords, setSelectedCoords] = useState({ lat: null, lng: null })
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

  // Shift Rules state
  const [shiftRules, setShiftRules] = useState(null)
  const [shiftRulesLoading, setShiftRulesLoading] = useState(false)
  const [shiftRulesForm, setShiftRulesForm] = useState({
    shift_max_hours: 8,
    shift_min_hours: 4,
    max_weekly_hours: 40,
    min_weekly_hours: 20,
    fixed_shifts: false,
    number_of_shifts_per_day: 3,
    meet_all_demand: true,
    min_rest_slots: 2,
    slot_len_hour: 0.5,
    min_shift_length_slots: 4,
    receiving_phone: true,
    delivery: true,
    waiting_time: 15,
    accepting_orders: true,
  })
  const [shiftTimes, setShiftTimes] = useState([
    { from: "10:00", to: "14:00" },
    { from: "14:00", to: "18:00" },
    { from: "18:00", to: "22:00" },
  ])
  const [operatingHours, setOperatingHours] = useState([
    { weekday: "Monday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Tuesday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Wednesday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Thursday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Friday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Saturday", opening_time: "09:00", closing_time: "22:00" },
    { weekday: "Sunday", opening_time: "09:00", closing_time: "22:00" },
  ])
  const [customDayShifts, setCustomDayShifts] = useState({})

  // Campaigns state
  const [campaignsData, setCampaignsData] = useState([])
  const [campaignsLoading, setCampaignsLoading] = useState(false)
  const [campaignsFilter, setCampaignsFilter] = useState("all") // all, week
  const [campaignsInsights, setCampaignsInsights] = useState([])
  const [showUploadCampaigns, setShowUploadCampaigns] = useState(false)
  const [showUploadCampaignItems, setShowUploadCampaignItems] = useState(false)
  const campaignsFileInput = useRef(null)
  const campaignItemsFileInput = useRef(null)
  const [profileData, setProfileData] = useState(null)
  const [profileLoading, setProfileLoading] = useState(false)

  // Requests Management state (for main Requests tab)
  const [allRequests, setAllRequests] = useState([])
  const [allRequestsLoading, setAllRequestsLoading] = useState(false)
  const [allRequestsError, setAllRequestsError] = useState("")
  const [requestActionLoading, setRequestActionLoading] = useState(false)
  const [requestActionMessage, setRequestActionMessage] = useState(null)

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
    hourly_salary: "",
  })
  const [delegateLoading, setDelegateLoading] = useState(false)
  const [delegateError, setDelegateError] = useState("")
  const csvFileInput = useRef(null)
  // ADD THESE STATE VARIABLES:
  const [showRecommendationModal, setShowRecommendationModal] = useState(false)
  const [recommendationParams, setRecommendationParams] = useState({
    recommendation_start_date: new Date().toISOString().split("T")[0],
    num_recommendations: 5,
    optimize_for: "roi",
    max_discount: 30,
    min_campaign_duration_days: 3,
    max_campaign_duration_days: 14,
    available_items: [],
  })
  const [recommendations, setRecommendations] = useState(null)
  const [recommendationsLoading, setRecommendationsLoading] = useState(false)
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

  // Schedule state
  const [scheduleData, setScheduleData] = useState([])
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [scheduleError, setScheduleError] = useState("")
  const [scheduleGeneratingWeek, setScheduleGeneratingWeek] = useState(false)
  const [scheduleGeneratingMonth, setScheduleGeneratingMonth] = useState(false)
  const [scheduleGenerateError, setScheduleGenerateError] = useState("")
  const [scheduleGenerateSuccess, setScheduleGenerateSuccess] = useState("")
  const [scheduleView, setScheduleView] = useState("none") // none, week, month
  const [selectedWeek, setSelectedWeek] = useState(null) // 0-3 for month view
  const [selectedSlot, setSelectedSlot] = useState(null) // {hour, day}
  const [showSchedulePopup, setShowSchedulePopup] = useState(false)
  const [cameFromMonth, setCameFromMonth] = useState(false)

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

  // Transform API schedule data for display
  // API returns: { date, day, start_time, end_time }
  // We need to create a simplified schedule grid showing coverage
  const scheduleDataForDisplay = (() => {
    const data = []

    // Group shifts by day and hour to count coverage
    const coverageMap = {}

    scheduleData.forEach((shift) => {
      // Handle new backend format: { schedule_date, day, start_time, end_time, employees }
      if (
        shift.day &&
        shift.start_time &&
        shift.end_time &&
        Array.isArray(shift.employees)
      ) {
        // Parse start and end times (format: "HH:MM:SS")
        const startHour = parseInt(shift.start_time.split(":")[0], 10)
        const endHour = parseInt(shift.end_time.split(":")[0], 10)

        // Map day name to day index (0=Monday, 6=Sunday)
        const dayMap = {
          monday: 0,
          tuesday: 1,
          wednesday: 2,
          thursday: 3,
          friday: 4,
          saturday: 5,
          sunday: 6,
        }
        const dayOfWeek = dayMap[shift.day.toLowerCase()] ?? 0

        // Mark all hours in this shift
        for (let hour = startHour; hour < endHour; hour++) {
          const key = `${dayOfWeek}-${hour}`
          if (!coverageMap[key]) {
            coverageMap[key] = { count: 0, shifts: [] }
          }
          coverageMap[key].count += shift.employees.length
          coverageMap[key].shifts.push(shift)
        }
      }
    })

    // Create data structure for grid display
    for (let hour = 0; hour < 24; hour++) {
      for (let day = 0; day < 7; day++) {
        const key = `${day}-${hour}`
        const coverage = coverageMap[key] || { count: 0, shifts: [] }

        data.push({
          hour,
          day,
          employeeCount: coverage.count,
          shifts: coverage.shifts,
        })
      }
    }

    return data
  })()

  const getScheduleSlot = (hour, day) => {
    return scheduleDataForDisplay.find((s) => s.hour === hour && s.day === day)
  }

  const navigationItems = [
    { id: "home", label: "Dashboard", icon: HomeIcon },
    { id: "schedule", label: "Schedule", icon: ScheduleIcon },
    { id: "insights", label: "Insights", icon: AnalyticsIcon },
    { id: "campaigns", label: "Campaigns", icon: PlanningIcon }, // Changed from "planning" to "campaigns"
    { id: "staffing", label: "Staffing", icon: EmployeeIcon },
    { id: "requests", label: "Requests", icon: InfoIcon },
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
  // Fetch profile data when admin profile modal opens
  useEffect(() => {
    if (showAdminProfile) {
      fetchProfileData()
    }
  }, [showAdminProfile])

  const fetchProfileData = async () => {
    try {
      setProfileLoading(true)
      const data = await api.profile.getProfile()
      setProfileData(data.data)
    } catch (err) {
      console.error("Failed to fetch profile data:", err)
    } finally {
      setProfileLoading(false)
    }
  }
  // Load shift rules when info tab is active
  useEffect(() => {
    if (activeTab === "info") {
      fetchShiftRules()
    }
  }, [activeTab])

  const fetchShiftRules = async () => {
    try {
      setShiftRulesLoading(true)
      const orgId = localStorage.getItem("org_id")
      const response = await api.rules.getRules()

      if (response.data) {
        const rules = response.data
        setShiftRules(rules)

        // Populate form with existing data
        setShiftRulesForm({
          shift_max_hours: rules.shift_max_hours || 8,
          shift_min_hours: rules.shift_min_hours || 4,
          max_weekly_hours: rules.max_weekly_hours || 40,
          min_weekly_hours: rules.min_weekly_hours || 20,
          fixed_shifts: rules.fixed_shifts || false,
          number_of_shifts_per_day: rules.number_of_shifts_per_day || 3,
          meet_all_demand:
            rules.meet_all_demand !== undefined ? rules.meet_all_demand : true,
          min_rest_slots: rules.min_rest_slots || 2,
          slot_len_hour: rules.slot_len_hour || 0.5,
          min_shift_length_slots: rules.min_shift_length_slots || 4,
          receiving_phone:
            rules.receiving_phone !== undefined ? rules.receiving_phone : true,
          delivery: rules.delivery !== undefined ? rules.delivery : true,
          waiting_time: rules.waiting_time || 15,
          accepting_orders:
            rules.accepting_orders !== undefined
              ? rules.accepting_orders
              : true,
        })

        // Populate operating hours if available
        if (rules.operating_hours && rules.operating_hours.length > 0) {
          setOperatingHours(
            rules.operating_hours.map((oh) => ({
              weekday: oh.weekday,
              opening_time: oh.opening_time ? oh.opening_time.slice(0, 5) : "",
              closing_time: oh.closing_time ? oh.closing_time.slice(0, 5) : "",
              closed: oh.closed || false,
            })),
          )
        }
      }
    } catch (err) {
      console.error("Failed to fetch shift rules:", err)
    } finally {
      setShiftRulesLoading(false)
    }
  }

  const handleSaveShiftRules = async () => {
    try {
      setShiftRulesLoading(true)
      setActionMessage(null)

      // Build the payload
      const payload = {
        shift_max_hours: parseInt(shiftRulesForm.shift_max_hours),
        shift_min_hours: parseInt(shiftRulesForm.shift_min_hours),
        max_weekly_hours: parseInt(shiftRulesForm.max_weekly_hours),
        min_weekly_hours: parseInt(shiftRulesForm.min_weekly_hours),
        fixed_shifts: shiftRulesForm.fixed_shifts,
        meet_all_demand: shiftRulesForm.meet_all_demand,
        min_rest_slots: parseInt(shiftRulesForm.min_rest_slots),
        slot_len_hour: parseFloat(shiftRulesForm.slot_len_hour),
        min_shift_length_slots: parseInt(shiftRulesForm.min_shift_length_slots),
        receiving_phone: shiftRulesForm.receiving_phone,
        delivery: shiftRulesForm.delivery,
        waiting_time: parseInt(shiftRulesForm.waiting_time),
        accepting_orders: shiftRulesForm.accepting_orders,
        operating_hours: operatingHours
          .filter((oh) => !oh.closed && oh.opening_time && oh.closing_time)
          .map((oh) => ({
            weekday: oh.weekday,
            opening_time: oh.opening_time,
            closing_time: oh.closing_time,
          })),
      }

      // Only include number_of_shifts_per_day if fixed_shifts is true
      if (shiftRulesForm.fixed_shifts) {
        payload.number_of_shifts_per_day = parseInt(
          shiftRulesForm.number_of_shifts_per_day,
        )
      } else {
        payload.number_of_shifts_per_day = null
      }

      await api.rules.saveRules(payload)

      setActionMessage({
        type: "success",
        text: "Shift rules saved successfully!",
      })
      setTimeout(() => setActionMessage(null), 4000)

      // Refresh data
      fetchShiftRules()
    } catch (err) {
      console.error("Failed to save shift rules:", err)
      setActionMessage({
        type: "error",
        text: err.message || "Failed to save shift rules",
      })
      setTimeout(() => setActionMessage(null), 4000)
    } finally {
      setShiftRulesLoading(false)
    }
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

  useEffect(() => {
    if (activeTab === "schedule") {
      fetchSchedule()
    }
  }, [activeTab])

  // Fetch fresh insights when admin profile is opened
  useEffect(() => {
    const fetchOrgStatsForProfile = async () => {
      if (showAdminProfile && currentUser?.user_role === "admin") {
        try {
          const insightsResponse = await api.dashboard.getInsights()
          if (insightsResponse && insightsResponse.data) {
            setInsights(insightsResponse.data)
          }
        } catch (err) {
          console.error("Error fetching organization stats:", err)
        }
      }
    }

    fetchOrgStatsForProfile()
  }, [showAdminProfile, currentUser?.user_role])

  const fetchSchedule = async () => {
    try {
      setScheduleLoading(true)
      setScheduleError("")
      const response = await api.dashboard.getAllSchedule()
      console.log("fetchSchedule response:", response)
      if (response && response.data) {
        // Handle new backend format with data array
        setScheduleData(response.data)
      } else {
        setScheduleData([])
      }
    } catch (err) {
      console.error("Error fetching schedule:", err)
      setScheduleError(err.message || "Failed to load schedule")
    } finally {
      setScheduleLoading(false)
    }
  }

  const handleGenerateSchedule = async (viewType) => {
    try {
      if (viewType === "week") {
        setScheduleGeneratingWeek(true)
      } else {
        setScheduleGeneratingMonth(true)
      }
      setScheduleGenerateError("")
      setScheduleGenerateSuccess("")

      console.log("Generating schedule...")
      const response = await api.dashboard.generateSchedule()
      console.log("Schedule generation response:", response)

      setScheduleGenerateSuccess(
        response.schedule_message ||
          response.message ||
          "Schedule generated successfully!",
      )

      // Fetch the newly generated schedule from backend
      await fetchSchedule()

      // DON'T auto-navigate - let user click to view
      // setScheduleView(viewType) - REMOVED

      // Clear success message after 5 seconds
      setTimeout(() => setScheduleGenerateSuccess(""), 5000)
    } catch (err) {
      console.error("Error generating schedule:", err)
      setScheduleGenerateError(err.message || "Failed to generate schedule")
      setTimeout(() => setScheduleGenerateError(""), 5000)
    } finally {
      setScheduleGeneratingWeek(false)
      setScheduleGeneratingMonth(false)
    }
  }

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
        // Map salary_per_hour to hourly_salary for consistency
        hourly_salary:
          userData.salary_per_hour ||
          userData.hourly_salary ||
          authData.salary_per_hour ||
          authData.hourly_salary,
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

      // Fetch demand heatmap data
      try {
        const demandResponse = await api.dashboard.getDemandHeatmap()
        console.log("Initial demand heatmap fetch:", demandResponse)
        if (demandResponse && demandResponse.data) {
          // Transform API data to heatmap format (24 hours x 7 days)
          const transformedHeatmap = transformDemandToHeatmap(
            demandResponse.data,
          )
          setHeatMapData(transformedHeatmap)
        } else {
          console.log("No existing demand data, keeping initial zeros")
        }
      } catch (err) {
        console.error("Error fetching demand heatmap:", err)
        // Keep the default zero values if API fails
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err)
      setError(err.message || "Failed to load dashboard data")
    } finally {
      setLoading(false)
    }
  }

  // Transform demand API response to heatmap format
  const transformDemandToHeatmap = (demandData) => {
    console.log("transformDemandToHeatmap called with:", demandData)
    // Initialize 24 hours x 7 days array with zeros
    const heatmap = Array(24)
      .fill(null)
      .map(() => Array(7).fill(0))

    if (!demandData || !demandData.days) {
      console.log("No demand data or days found, returning empty heatmap")
      return heatmap
    }

    // Map day names to indices (Mon=0, Tue=1, ..., Sun=6)
    const dayNameToIndex = {
      monday: 0,
      tuesday: 1,
      wednesday: 2,
      thursday: 3,
      friday: 4,
      saturday: 5,
      sunday: 6,
    }

    // Find max item count for percentage calculation
    let maxItemCount = 0
    demandData.days.forEach((day) => {
      if (day.hours) {
        day.hours.forEach((hourData) => {
          if (hourData.item_count > maxItemCount) {
            maxItemCount = hourData.item_count
          }
        })
      }
    })

    // Avoid division by zero
    if (maxItemCount === 0) {
      maxItemCount = 1
    }

    console.log("Max item count:", maxItemCount)

    // Fill heatmap with percentage values
    demandData.days.forEach((day) => {
      const dayIndex = dayNameToIndex[day.day_name.toLowerCase()]
      if (dayIndex !== undefined && day.hours) {
        day.hours.forEach((hourData) => {
          if (hourData.hour >= 0 && hourData.hour < 24) {
            // Calculate percentage (0-100) based on item count
            const percentage = Math.round(
              (hourData.item_count / maxItemCount) * 100,
            )
            heatmap[hourData.hour][dayIndex] = percentage
          }
        })
      }
    })

    console.log("Transformed heatmap:", heatmap)
    return heatmap
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

  // Handle demand prediction generation
  const handleGeneratePredictions = async () => {
    try {
      setPredictionLoading(true)
      setPredictionError("")
      setPredictionSuccess("")

      // Generate predictions
      const response = await api.dashboard.generateDemandPrediction()
      console.log("Generate prediction response:", response)

      // Use the data directly from the generation response
      if (response && response.data) {
        const transformedHeatmap = transformDemandToHeatmap(response.data)
        setHeatMapData(transformedHeatmap)
        setPredictionSuccess("Demand predictions generated successfully!")

        // Clear success message after 3 seconds
        setTimeout(() => setPredictionSuccess(""), 3000)
      }
    } catch (err) {
      console.error("Error generating predictions:", err)
      setPredictionError(err.message || "Failed to generate predictions")

      // Clear error message after 5 seconds
      setTimeout(() => setPredictionError(""), 5000)
    } finally {
      setPredictionLoading(false)
    }
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
      <div className="section-wrapper">
        <div className="section-header">
          <div>
            <h2 className="section-title">Weekly Demand Heat Map</h2>
            <p className="section-description">
              Peak hours analysis - hover for detailed metrics
            </p>
          </div>
          <div className="section-actions">
            <button
              className="btn-primary"
              onClick={handleGeneratePredictions}
              disabled={predictionLoading}
              style={{ marginRight: "10px" }}
            >
              {predictionLoading ? "Generating..." : "Generate Predictions"}
            </button>
            <button className="btn-secondary">Export Data</button>
          </div>
        </div>
        {predictionError && (
          <div className="login-error-message" style={{ marginBottom: "15px" }}>
            {predictionError}
          </div>
        )}
        {predictionSuccess && (
          <div
            className="login-error-message"
            style={{
              marginBottom: "15px",
              backgroundColor: "var(--success-color)",
              borderColor: "var(--success-color)",
            }}
          >
            {predictionSuccess}
          </div>
        )}
        {heatMapData && heatMapData.length > 0 && (
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
        )}
      </div>
    </div>
  )

  const renderMasterSchedule = () => {
    const handleSlotClick = (hour, day) => {
      setSelectedSlot({ hour, day })
      setShowSchedulePopup(true)
    }

    const renderWeekView = (weekOffset = 0) => {
      const headerGradient = `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`
      const cornerGradient = `linear-gradient(135deg, ${secondaryColor}, ${accentColor})`

      return (
        <div className="schedule-week-view-premium">
          <div className="schedule-week-header-premium">
            <div className="schedule-title-section">
              <h3 className="schedule-main-title">
                Week {weekOffset + 1} Schedule
              </h3>
              <p className="schedule-subtitle">
                Click any time slot to view employee details
              </p>
            </div>
            <div className="schedule-stats-mini">
              <div className="mini-stat">
                <span className="mini-stat-value">{scheduleData.length}</span>
                <span className="mini-stat-label">Shifts</span>
              </div>
              <div className="mini-stat">
                <span className="mini-stat-value">
                  {scheduleData.reduce(
                    (sum, s) => sum + (s.employees?.length || 0),
                    0,
                  )}
                </span>
                <span className="mini-stat-label">Staff</span>
              </div>
            </div>
          </div>
          <div className="schedule-grid-premium">
            {/* Header row with days */}
            <div
              className="schedule-header-cell-premium schedule-corner-cell-premium"
              style={{ background: cornerGradient }}
            >
              <svg
                className="corner-icon"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                />
              </svg>
              <span className="corner-label">Time</span>
            </div>
            {days.map((day, dayIndex) => (
              <div
                key={dayIndex}
                className="schedule-header-cell-premium"
                style={{ background: headerGradient }}
              >
                <span className="day-name-premium">{day}</span>
                <span className="day-subtitle">Day {dayIndex + 1}</span>
              </div>
            ))}

            {/* Hour rows */}
            {Array.from({ length: 24 }).map((_, hour) => (
              <>
                <div
                  key={`hour-${hour}`}
                  className="schedule-hour-label-premium"
                >
                  <span className="hour-time-large">
                    {hour.toString().padStart(2, "0")}
                  </span>
                  <span className="hour-period">{hour < 12 ? "AM" : "PM"}</span>
                </div>
                {days.map((_, day) => {
                  const slotData = getScheduleSlot(hour, day)
                  const totalStaff = slotData ? slotData.employeeCount : 0

                  return (
                    <div
                      key={`${hour}-${day}`}
                      className={`schedule-cell-premium ${totalStaff === 0 ? "empty-slot-premium" : "active-slot-premium"}`}
                      onClick={() =>
                        totalStaff > 0 && handleSlotClick(hour, day)
                      }
                      style={{
                        background:
                          totalStaff > 0
                            ? `linear-gradient(135deg, ${primaryColor}08, ${secondaryColor}05)`
                            : undefined,
                      }}
                    >
                      {totalStaff > 0 ? (
                        <div className="schedule-cell-content-premium">
                          <div
                            className="staff-count-badge"
                            style={{
                              background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`,
                            }}
                          >
                            <svg
                              className="staff-icon"
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
                            <span className="staff-count">{totalStaff}</span>
                          </div>
                          <span className="staff-label">Staff Members</span>
                        </div>
                      ) : (
                        <div className="empty-indicator-premium">
                          <svg
                            className="empty-icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  )
                })}
              </>
            ))}
          </div>
        </div>
      )
    }

    const renderMonthView = () => {
      const weeks = [
        { label: "Week 1", dates: "Feb 1-7" },
        { label: "Week 2", dates: "Feb 8-14" },
        { label: "Week 3", dates: "Feb 15-21" },
        { label: "Week 4", dates: "Feb 22-28" },
      ]

      return (
        <div className="schedule-month-view">
          {scheduleLoading && (
            <div className="schedule-hardcoded-alert">
              <div className="alert-icon">⏳</div>
              <div className="alert-content">Loading schedule data...</div>
            </div>
          )}

          {scheduleError && (
            <div
              className="schedule-hardcoded-alert"
              style={{ borderColor: accentColor }}
            >
              <div className="alert-icon">⚠️</div>
              <div className="alert-content">
                <strong>Error:</strong> {scheduleError}
              </div>
            </div>
          )}

          {!scheduleLoading && !scheduleError && scheduleData.length === 0 && (
            <div className="schedule-hardcoded-alert">
              <div className="alert-icon">ℹ️</div>
              <div className="alert-content">
                <strong>No Schedule:</strong> No shifts scheduled for the next 7
                days. Generate a new schedule to get started.
              </div>
            </div>
          )}

          <div className="month-header">
            <h3>February 2026 - Monthly Overview</h3>
            <p>Click on any week to view detailed schedule</p>
          </div>
          <div className="month-grid">
            {weeks.map((week, weekIndex) => (
              <div
                key={weekIndex}
                className="month-week-card"
                onClick={() => {
                  setSelectedWeek(weekIndex)
                  setCameFromMonth(true)
                  setScheduleView("week")
                }}
              >
                <div className="week-card-header">
                  <h4>{week.label}</h4>
                  <span className="week-dates">{week.dates}</span>
                </div>
                <div className="week-preview">
                  {days.map((day, dayIndex) => {
                    // Show total staff for peak hour (18:00)
                    const peakSlot = getScheduleSlot(18, dayIndex)
                    const peakStaff = peakSlot ? peakSlot.employeeCount : 0

                    return (
                      <div key={dayIndex} className="week-preview-day">
                        <div className="day-label">{day}</div>
                        <div className="day-staff-count">{peakStaff}</div>
                        <div className="day-staff-label">staff</div>
                      </div>
                    )
                  })}
                </div>
                <div className="week-card-footer">
                  <span className="view-details">Click to view details →</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )
    }

    const renderSchedulePopup = () => {
      if (!showSchedulePopup || !selectedSlot) return null

      const slotData = getScheduleSlot(selectedSlot.hour, selectedSlot.day)
      const totalEmployees = slotData ? slotData.employeeCount : 0

      return (
        <div
          className="schedule-popup-overlay-premium"
          onClick={() => setShowSchedulePopup(false)}
        >
          <div
            className="schedule-popup-premium"
            onClick={(e) => e.stopPropagation()}
          >
            {/* Profile-style header card */}
            <div className="popup-header-card">
              <div className="popup-header-content">
                <div
                  className="popup-icon-wrapper"
                  style={{
                    background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`,
                  }}
                >
                  <svg
                    className="popup-main-icon"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                    />
                  </svg>
                </div>
                <div className="popup-title-section">
                  <h3 className="popup-title-premium">
                    {days[selectedSlot.day]},{" "}
                    {selectedSlot.hour.toString().padStart(2, "0")}:00
                  </h3>
                  <p className="popup-subtitle-premium">
                    {totalEmployees}{" "}
                    {totalEmployees === 1 ? "Staff Member" : "Staff Members"}{" "}
                    Scheduled
                  </p>
                </div>
              </div>
              <button
                className="popup-close-premium"
                onClick={() => setShowSchedulePopup(false)}
                aria-label="Close"
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
            </div>

            {/* Profile-style content */}
            <div className="popup-content-premium">
              {slotData && slotData.shifts && slotData.shifts.length > 0 ? (
                <>
                  {/* Shift info cards */}
                  {slotData.shifts.map((shift, idx) => (
                    <div key={idx} className="shift-info-card">
                      <div className="shift-card-header">
                        <div
                          className="shift-time-badge"
                          style={{
                            background: `linear-gradient(135deg, ${primaryColor}15, ${secondaryColor}10)`,
                            borderColor: primaryColor,
                          }}
                        >
                          <svg
                            className="time-icon"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          <span>
                            {shift.start_time} - {shift.end_time}
                          </span>
                        </div>
                      </div>

                      {/* Employee grid - profile style */}
                      <div className="employees-grid-premium">
                        {shift.employees && shift.employees.length > 0 ? (
                          shift.employees.map((emp, empIdx) => (
                            <div key={empIdx} className="employee-card-mini">
                              <div
                                className="employee-avatar"
                                style={{
                                  background: `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`,
                                }}
                              >
                                <svg
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
                              </div>
                              <div className="employee-info-mini">
                                <span className="employee-name-mini">
                                  {emp}
                                </span>
                                <span className="employee-role-mini">
                                  Staff Member
                                </span>
                              </div>
                            </div>
                          ))
                        ) : (
                          <div className="no-employees-card">
                            <svg
                              className="no-emp-icon"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                            >
                              <path
                                strokeLinecap="round"
                                strokeLinejoin="round"
                                strokeWidth={2}
                                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                              />
                            </svg>
                            <span>No employees assigned</span>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </>
              ) : (
                <div className="no-data-card">
                  <div
                    className="no-data-icon"
                    style={{ background: `${accentColor}15` }}
                  >
                    <svg
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      style={{ stroke: accentColor }}
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
                      />
                    </svg>
                  </div>
                  <h4 className="no-data-title">No Staff Scheduled</h4>
                  <p className="no-data-text">
                    There are no staff members assigned to this time slot yet.
                  </p>
                </div>
              )}
            </div>
          </div>
        </div>
      )
    }

    const handleBackClick = () => {
      if (scheduleView === "week" && cameFromMonth) {
        // Return to month view
        setScheduleView("month")
        setCameFromMonth(false)
        setSelectedWeek(null)
      } else {
        // Return to root
        setScheduleView("none")
        setSelectedWeek(null)
        setCameFromMonth(false)
      }
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Master Schedule</h1>
            <p className="page-subtitle">Comprehensive workforce calendar</p>
          </div>
          <div className="schedule-buttons">
            {scheduleView !== "none" && (
              <button className="btn-secondary" onClick={handleBackClick}>
                <span className="btn-icon">←</span> Back to{" "}
                {cameFromMonth && scheduleView === "week"
                  ? "Month"
                  : "Schedule"}
              </button>
            )}
            {scheduleView === "none" && (
              <>
                <button
                  className="btn-primary"
                  onClick={() => handleGenerateSchedule("week")}
                  disabled={scheduleGeneratingWeek || scheduleGeneratingMonth}
                >
                  <img src={ScheduleIcon} alt="" className="btn-icon-svg" />{" "}
                  {scheduleGeneratingWeek
                    ? "Generating..."
                    : "Generate Week Schedule"}
                </button>
                <button
                  className="btn-primary"
                  onClick={() => handleGenerateSchedule("month")}
                  disabled={scheduleGeneratingWeek || scheduleGeneratingMonth}
                >
                  <img src={ScheduleIcon} alt="" className="btn-icon-svg" />{" "}
                  {scheduleGeneratingMonth
                    ? "Generating..."
                    : "Generate Month Schedule"}
                </button>
              </>
            )}
          </div>
        </div>

        {scheduleGenerateError && (
          <div className="login-error-message" style={{ marginBottom: "15px" }}>
            {scheduleGenerateError}
          </div>
        )}
        {scheduleGenerateSuccess && (
          <div
            className="login-error-message"
            style={{
              marginBottom: "15px",
              backgroundColor: "var(--success-color)",
              borderColor: "var(--success-color)",
            }}
          >
            {scheduleGenerateSuccess}
          </div>
        )}

        {scheduleView === "none" && (
          <div className="empty-state">
            <img src={ScheduleIcon} alt="Schedule" className="empty-icon-svg" />
            <h3>View Your Schedule</h3>
            <p>
              {scheduleData.length > 0
                ? "Click on Week or Month view below to see the schedule"
                : "Generate a schedule first, then click Week or Month to view it"}
            </p>
            {scheduleData.length > 0 && (
              <div
                style={{
                  marginTop: "var(--space-4)",
                  display: "flex",
                  gap: "var(--space-3)",
                  justifyContent: "center",
                }}
              >
                <button
                  className="btn-secondary"
                  onClick={() => setScheduleView("week")}
                >
                  View Week Schedule
                </button>
                <button
                  className="btn-secondary"
                  onClick={() => setScheduleView("month")}
                >
                  View Month Schedule
                </button>
              </div>
            )}
          </div>
        )}

        {scheduleView === "week" && renderWeekView(selectedWeek || 0)}
        {scheduleView === "month" && renderMonthView()}
        {renderSchedulePopup()}
      </div>
    )
  }

  const renderInsights = () => {
    // Group insights by category for better organization
    const categorizeInsights = (insights) => {
      const categories = {
        staffing: [],
        financial: [],
        operations: [],
        performance: [],
        tables: [],
        orders: [],
      }

      insights.forEach((insight) => {
        const title = insight.title.toLowerCase()

        if (
          title.includes("employee") ||
          title.includes("staff") ||
          title.includes("salary") ||
          title.includes("manager") ||
          title.includes("waiter") ||
          title.includes("chef") ||
          title.includes("driver") ||
          title.includes("cashier")
        ) {
          categories.staffing.push(insight)
        } else if (
          title.includes("revenue") ||
          title.includes("salary") ||
          title.includes("cost")
        ) {
          categories.financial.push(insight)
        } else if (
          title.includes("table") ||
          title.includes("capacity") ||
          title.includes("people")
        ) {
          categories.tables.push(insight)
        } else if (
          title.includes("order") ||
          title.includes("delivery") ||
          title.includes("dine") ||
          title.includes("takeaway")
        ) {
          categories.orders.push(insight)
        } else if (
          title.includes("selling") ||
          title.includes("item") ||
          title.includes("popular")
        ) {
          categories.performance.push(insight)
        } else {
          categories.operations.push(insight)
        }
      })

      return categories
    }

    const categorizedInsights =
      insights.length > 0 ? categorizeInsights(insights) : null

    const renderInsightCard = (insight, index, variant = "primary") => {
      const variantColors = {
        primary: "var(--color-primary)",
        secondary: "var(--color-secondary)",
        accent: "var(--color-accent)",
        info: "var(--primary-500)",
      }

      const color = variantColors[variant] || variantColors.primary

      return (
        <div
          key={index}
          className="kpi-card"
          data-animation="slide-up"
          style={{
            animationDelay: `${index * 0.05}s`,
            background: `linear-gradient(135deg, ${color}15 0%, ${color}05 100%)`,
            border: `1px solid ${color}30`,
          }}
        >
          <div
            className="kpi-icon-wrapper"
            style={{ background: `${color}20` }}
          >
            <svg
              className="kpi-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke={color}
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
            <h3 className="kpi-label" style={{ color: "var(--gray-600)" }}>
              {insight.title}
            </h3>
            <div className="kpi-value-wrapper">
              <div className="kpi-value" style={{ color }}>
                {insight.statistic}
              </div>
            </div>
          </div>
        </div>
      )
    }

    const renderCategorySection = (
      title,
      insightsList,
      icon,
      variant = "primary",
    ) => {
      if (!insightsList || insightsList.length === 0) return null

      return (
        <div
          className="section-wrapper"
          style={{ marginBottom: "var(--space-6)" }}
        >
          <div className="section-header">
            <h2 className="section-title">
              {icon && (
                <img src={icon} alt={title} className="title-icon-svg" />
              )}
              {title}
            </h2>
            <span className="badge badge-primary">
              {insightsList.length} Metrics
            </span>
          </div>
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))",
              gap: "var(--space-4)",
              marginTop: "var(--space-4)",
            }}
          >
            {insightsList.map((insight, index) =>
              renderInsightCard(insight, index, variant),
            )}
          </div>
        </div>
      )
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Organization Insights</h1>
            <p className="page-subtitle">
              {currentUser?.user_role === "admin"
                ? "Comprehensive analytics and metrics for your organization"
                : currentUser?.user_role === "manager"
                  ? "Management insights and team performance"
                  : "Your personal performance and workplace metrics"}
            </p>
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

        {/* Role Indicator Badge */}
        <div
          style={{
            marginBottom: "var(--space-6)",
            padding: "var(--space-4)",
            background: "var(--primary-50)",
            borderRadius: "var(--radius-lg)",
            border: "1px solid var(--primary-200)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
          }}
        >
          <div
            className="user-avatar"
            style={{ width: 48, height: 48, fontSize: "var(--text-lg)" }}
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
          <div>
            <h3
              style={{
                margin: 0,
                fontSize: "var(--text-lg)",
                fontWeight: 600,
                color: "var(--gray-800)",
              }}
            >
              {currentUser?.full_name || "Loading..."}
            </h3>
            <p
              style={{
                margin: 0,
                fontSize: "var(--text-sm)",
                color: "var(--gray-600)",
              }}
            >
              <span
                className="badge badge-primary"
                style={{ marginRight: "var(--space-2)" }}
              >
                {currentUser?.user_role || "..."}
              </span>
              Viewing{" "}
              {currentUser?.user_role === "admin"
                ? "full organization"
                : currentUser?.user_role === "manager"
                  ? "management"
                  : "personal"}{" "}
              insights
            </p>
          </div>
        </div>

        {insights && insights.length > 0 && categorizedInsights ? (
          <>
            {/* Staffing Insights */}
            {renderCategorySection(
              "Staffing & Team",
              categorizedInsights.staffing,
              EmployeeIcon,
              "primary",
            )}

            {/* Financial Insights */}
            {renderCategorySection(
              "Financial Metrics",
              categorizedInsights.financial,
              null,
              "secondary",
            )}

            {/* Tables & Capacity */}
            {renderCategorySection(
              "Tables & Capacity",
              categorizedInsights.tables,
              LocationIcon,
              "accent",
            )}

            {/* Orders & Sales */}
            {renderCategorySection(
              "Orders & Sales",
              categorizedInsights.orders,
              OrdersIcon,
              "primary",
            )}

            {/* Performance & Items */}
            {renderCategorySection(
              "Performance & Popular Items",
              categorizedInsights.performance,
              ChartUpIcon,
              "secondary",
            )}

            {/* Other Operations */}
            {renderCategorySection(
              "Operations",
              categorizedInsights.operations,
              ConfigurationIcon,
              "info",
            )}

            {/* Summary Statistics */}
            <div
              className="section-wrapper"
              style={{
                background: "var(--gray-50)",
                border: "2px solid var(--gray-200)",
              }}
            >
              <div className="section-header">
                <h2 className="section-title">
                  <img
                    src={AnalyticsIcon}
                    alt="Summary"
                    className="title-icon-svg"
                  />
                  Insights Summary
                </h2>
              </div>
              <div
                style={{
                  display: "grid",
                  gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                  gap: "var(--space-4)",
                  marginTop: "var(--space-4)",
                }}
              >
                <div style={{ textAlign: "center" }}>
                  <h4
                    style={{
                      fontSize: "var(--text-3xl)",
                      fontWeight: 700,
                      color: "var(--color-primary)",
                      margin: 0,
                    }}
                  >
                    {insights.length}
                  </h4>
                  <p
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--gray-600)",
                      margin: 0,
                    }}
                  >
                    Total Metrics
                  </p>
                </div>
                <div style={{ textAlign: "center" }}>
                  <h4
                    style={{
                      fontSize: "var(--text-3xl)",
                      fontWeight: 700,
                      color: "var(--color-secondary)",
                      margin: 0,
                    }}
                  >
                    {categorizedInsights.staffing.length}
                  </h4>
                  <p
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--gray-600)",
                      margin: 0,
                    }}
                  >
                    Staffing Metrics
                  </p>
                </div>
                <div style={{ textAlign: "center" }}>
                  <h4
                    style={{
                      fontSize: "var(--text-3xl)",
                      fontWeight: 700,
                      color: "var(--color-accent)",
                      margin: 0,
                    }}
                  >
                    {categorizedInsights.orders.length}
                  </h4>
                  <p
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--gray-600)",
                      margin: 0,
                    }}
                  >
                    Order Metrics
                  </p>
                </div>
                <div style={{ textAlign: "center" }}>
                  <h4
                    style={{
                      fontSize: "var(--text-3xl)",
                      fontWeight: 700,
                      color: "var(--primary-600)",
                      margin: 0,
                    }}
                  >
                    {categorizedInsights.financial.length}
                  </h4>
                  <p
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--gray-600)",
                      margin: 0,
                    }}
                  >
                    Financial Metrics
                  </p>
                </div>
              </div>
            </div>
          </>
        ) : (
          <div className="empty-state">
            <img
              src={AnalyticsIcon}
              alt="Insights"
              className="empty-icon-svg"
            />
            <h3>No Insights Available</h3>
            <p>
              Insights data will appear here once you have sufficient activity
            </p>
            <button
              className="btn-primary"
              onClick={() => fetchDashboardData()}
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
              Load Insights
            </button>
          </div>
        )}
      </div>
    )
  }
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

      // Close modal immediately
      setShowUploadCampaigns(false)

      try {
        setCampaignsLoading(true)
        const response = await api.campaigns.uploadCampaignsCSV(file)
        setActionMessage({
          type: "success",
          text: `Campaigns uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchCampaigns(campaignsFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload campaigns",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setCampaignsLoading(false)
        if (campaignsFileInput.current) campaignsFileInput.current.value = ""
      }
    }

    const handleCampaignItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Close modal immediately
      setShowUploadCampaigns(false)

      try {
        setCampaignsLoading(true)
        const response = await api.campaigns.uploadCampaignItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Campaign items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchCampaigns(campaignsFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload campaign items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setCampaignsLoading(false)
        if (campaignItemsFileInput.current)
          campaignItemsFileInput.current.value = ""
      }
    }

    const handleGetRecommendations = async () => {
      setShowRecommendationModal(true)
    }

    const handleFetchRecommendations = async () => {
      try {
        setRecommendationsLoading(true)
        const response =
          await api.campaigns.recommendCampaigns(recommendationParams)
        setRecommendations(response)
        setActionMessage({
          type: "success",
          text: `Generated ${response.recommendations?.length || 0} recommendations`,
        })
        setTimeout(() => setActionMessage(null), 4000)
      } catch (err) {
        console.error("Failed to fetch recommendations:", err)
        setActionMessage({
          type: "error",
          text:
            err.message ||
            "Failed to generate recommendations. Ensure sufficient historical data exists.",
        })
        setTimeout(() => setActionMessage(null), 6000)
      } finally {
        setRecommendationsLoading(false)
      }
    }

    const handleSubmitFeedback = async (feedback) => {
      try {
        await api.campaigns.submitCampaignFeedback(feedback)
        setActionMessage({
          type: "success",
          text: "Feedback submitted successfully",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } catch (err) {
        console.error("Failed to submit feedback:", err)
        setActionMessage({
          type: "error",
          text: err.message || "Failed to submit feedback",
        })
        setTimeout(() => setActionMessage(null), 4000)
      }
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
              <img
                src={MagicIcon}
                alt="AI Recommendations"
                style={{
                  width: "18px",
                  height: "18px",
                  marginRight: "8px",
                  filter: "brightness(0) saturate(100%)",
                }}
              />
              Get AI Recommendations
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
                    color: "var(--text-secondary)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {insight.title}
                </p>
                <h3
                  style={{
                    fontSize: "var(--text-2xl)",
                    fontWeight: 700,
                    color: primaryColor,
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
          <div
            className="section-wrapper"
            style={{ marginTop: "var(--space-6)" }}
          >
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
        {/* Campaign Recommendation Modal */}
        {showRecommendationModal && (
          <div
            className="modal-overlay"
            onClick={() =>
              !recommendationsLoading && setShowRecommendationModal(false)
            }
          >
            <div
              className="modal-content"
              style={{
                maxWidth: "900px",
                maxHeight: "90vh",
                overflow: "auto",
              }}
              onClick={(e) => e.stopPropagation()}
            >
              <div className="modal-header">
                <h2 className="section-title">
                  🎯 AI Campaign Recommendations
                </h2>
                <button
                  className="collapse-btn"
                  onClick={() => setShowRecommendationModal(false)}
                  disabled={recommendationsLoading}
                >
                  ×
                </button>
              </div>

              {!recommendations ? (
                // Configuration Form
                <div style={{ padding: "var(--space-4)" }}>
                  <h3
                    style={{
                      marginBottom: "var(--space-4)",
                      fontSize: "var(--text-lg)",
                      color: "var(--text-primary)",
                    }}
                  >
                    Configure Parameters
                  </h3>

                  <div style={{ display: "grid", gap: "var(--space-4)" }}>
                    <div>
                      <label className="form-label">Campaign Start Date</label>
                      <input
                        type="date"
                        className="form-input"
                        value={recommendationParams.recommendation_start_date}
                        onChange={(e) =>
                          setRecommendationParams({
                            ...recommendationParams,
                            recommendation_start_date: e.target.value,
                          })
                        }
                      />
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "var(--space-3)",
                      }}
                    >
                      <div>
                        <label className="form-label">
                          Number of Recommendations
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="10"
                          className="form-input"
                          value={recommendationParams.num_recommendations}
                          onChange={(e) =>
                            setRecommendationParams({
                              ...recommendationParams,
                              num_recommendations: parseInt(e.target.value),
                            })
                          }
                        />
                      </div>

                      <div>
                        <label className="form-label">Optimize For</label>
                        <select
                          className="form-input"
                          value={recommendationParams.optimize_for}
                          onChange={(e) =>
                            setRecommendationParams({
                              ...recommendationParams,
                              optimize_for: e.target.value,
                            })
                          }
                        >
                          <option value="roi">ROI</option>
                          <option value="revenue">Revenue</option>
                          <option value="uplift">Uplift</option>
                        </select>
                      </div>
                    </div>

                    <div>
                      <label className="form-label">Maximum Discount (%)</label>
                      <input
                        type="number"
                        min="0"
                        max="100"
                        step="5"
                        className="form-input"
                        value={recommendationParams.max_discount}
                        onChange={(e) =>
                          setRecommendationParams({
                            ...recommendationParams,
                            max_discount: parseFloat(e.target.value),
                          })
                        }
                      />
                    </div>

                    <div
                      style={{
                        display: "grid",
                        gridTemplateColumns: "1fr 1fr",
                        gap: "var(--space-3)",
                      }}
                    >
                      <div>
                        <label className="form-label">
                          Min Duration (days)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="30"
                          className="form-input"
                          value={
                            recommendationParams.min_campaign_duration_days
                          }
                          onChange={(e) =>
                            setRecommendationParams({
                              ...recommendationParams,
                              min_campaign_duration_days: parseInt(
                                e.target.value,
                              ),
                            })
                          }
                        />
                      </div>
                      <div>
                        <label className="form-label">
                          Max Duration (days)
                        </label>
                        <input
                          type="number"
                          min="1"
                          max="30"
                          className="form-input"
                          value={
                            recommendationParams.max_campaign_duration_days
                          }
                          onChange={(e) =>
                            setRecommendationParams({
                              ...recommendationParams,
                              max_campaign_duration_days: parseInt(
                                e.target.value,
                              ),
                            })
                          }
                        />
                      </div>
                    </div>
                  </div>

                  <button
                    className="btn-primary"
                    onClick={handleFetchRecommendations}
                    disabled={recommendationsLoading}
                    style={{
                      width: "100%",
                      marginTop: "var(--space-4)",
                      padding: "var(--space-3)",
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: "8px",
                    }}
                  >
                    {recommendationsLoading ? (
                      <>
                        <svg
                          width="20"
                          height="20"
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="2"
                          style={{
                            animation: "spin 1s linear infinite",
                          }}
                        >
                          <path d="M21 12a9 9 0 11-6.219-8.56" />
                        </svg>
                        Generating Recommendations...
                      </>
                    ) : (
                      <>
                        <img
                          src={MagicIcon}
                          alt="Magic"
                          style={{
                            width: "20px",
                            height: "20px",
                            filter: "brightness(0) saturate(100%) invert(1)",
                          }}
                        />
                        Generate Recommendations
                      </>
                    )}
                  </button>

                  {recommendationsLoading && (
                    <div
                      style={{
                        textAlign: "center",
                        marginTop: "var(--space-3)",
                      }}
                    >
                      <p
                        style={{
                          color: "var(--text-tertiary)",
                          fontSize: "var(--text-sm)",
                          marginBottom: "8px",
                        }}
                      >
                        🤖 AI is analyzing your data...
                      </p>
                      <p
                        style={{
                          color: "var(--text-tertiary)",
                          fontSize: "var(--text-xs)",
                        }}
                      >
                        This may take up to 60 seconds
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                // Recommendations Display
                <div style={{ padding: "var(--space-4)" }}>
                  <div
                    className="info-item"
                    style={{
                      marginBottom: "var(--space-4)",
                      padding: "var(--space-4)",
                    }}
                  >
                    <h3
                      style={{
                        marginBottom: "var(--space-2)",
                        color: "var(--text-primary)",
                        fontSize: "var(--text-xl)",
                        fontWeight: 700,
                      }}
                    >
                      {recommendations.restaurant_name}
                    </h3>
                    <p
                      style={{
                        color: "var(--text-secondary)",
                        fontSize: "var(--text-sm)",
                      }}
                    >
                      📅 {recommendations.recommendation_date} • Confidence:{" "}
                      <strong>{recommendations.confidence_level}</strong>
                    </p>
                  </div>

                  <div style={{ display: "grid", gap: "var(--space-4)" }}>
                    {recommendations.recommendations?.map((rec, index) => (
                      <div
                        key={rec.campaign_id || index}
                        className="profile-card"
                        style={{
                          padding: "var(--space-4)",
                          border: "2px solid var(--color-primary)",
                        }}
                      >
                        <div
                          style={{
                            display: "flex",
                            justifyContent: "space-between",
                            alignItems: "start",
                            marginBottom: "var(--space-3)",
                          }}
                        >
                          <h4
                            style={{
                              fontSize: "var(--text-lg)",
                              fontWeight: 700,
                              color: "var(--text-primary)",
                            }}
                          >
                            Campaign #{index + 1}
                          </h4>
                          <span
                            className="badge-primary"
                            style={{
                              padding: "6px 16px",
                              fontSize: "var(--text-sm)",
                              fontWeight: 700,
                            }}
                          >
                            {rec.discount_percentage}% OFF
                          </span>
                        </div>

                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr",
                            gap: "var(--space-3)",
                            marginBottom: "var(--space-3)",
                          }}
                        >
                          <div className="info-item">
                            <p className="info-label">Start Date</p>
                            <p className="info-value">{rec.start_date}</p>
                          </div>
                          <div className="info-item">
                            <p className="info-label">End Date</p>
                            <p className="info-value">
                              {rec.end_date} ({rec.duration_days}d)
                            </p>
                          </div>
                        </div>

                        <div
                          style={{
                            display: "grid",
                            gridTemplateColumns: "1fr 1fr 1fr",
                            gap: "var(--space-3)",
                            marginBottom: "var(--space-3)",
                          }}
                        >
                          <div className="stat-item">
                            <div className="stat-value">
                              {rec.expected_uplift?.toFixed(1)}%
                            </div>
                            <div className="stat-label">Expected Uplift</div>
                          </div>
                          <div className="stat-item">
                            <div className="stat-value">
                              {rec.expected_roi?.toFixed(1)}%
                            </div>
                            <div className="stat-label">Expected ROI</div>
                          </div>
                          <div className="stat-item">
                            <div className="stat-value">
                              ${rec.expected_revenue?.toFixed(0)}
                            </div>
                            <div className="stat-label">Expected Revenue</div>
                          </div>
                        </div>

                        <div style={{ marginBottom: "var(--space-3)" }}>
                          <p
                            style={{
                              fontSize: "var(--text-sm)",
                              color: "var(--text-secondary)",
                              marginBottom: "var(--space-2)",
                              fontWeight: 600,
                            }}
                          >
                            Items Included:
                          </p>
                          <div
                            style={{
                              display: "flex",
                              flexWrap: "wrap",
                              gap: "var(--space-2)",
                            }}
                          >
                            {rec.items?.map((item, idx) => (
                              <span
                                key={idx}
                                className="badge"
                                style={{
                                  padding: "4px 12px",
                                  background: "var(--bg-secondary)",
                                  color: "var(--text-primary)",
                                  border: "1px solid var(--border-color)",
                                }}
                              >
                                {item}
                              </span>
                            ))}
                          </div>
                        </div>

                        {rec.reasoning && (
                          <div
                            className="alert-card alert-low"
                            style={{
                              padding: "var(--space-3)",
                              marginTop: "var(--space-3)",
                            }}
                          >
                            <p
                              style={{
                                fontSize: "var(--text-sm)",
                                color: "var(--text-primary)",
                                margin: 0,
                              }}
                            >
                              <strong>💡 AI Insight:</strong> {rec.reasoning}
                            </p>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>

                  <button
                    className="btn-secondary"
                    onClick={() => {
                      setRecommendations(null)
                      setShowRecommendationModal(false)
                    }}
                    style={{ width: "100%", marginTop: "var(--space-4)" }}
                  >
                    Close
                  </button>
                </div>
              )}
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

      // Close modal immediately
      setShowUploadOrders(false)

      try {
        setOrdersLoading(true)
        const response = await api.orders.uploadOrdersCSV(file)
        setActionMessage({
          type: "success",
          text: `Orders uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchOrders(ordersFilter)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload orders",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        if (ordersFileInput.current) ordersFileInput.current.value = ""
      }
    }

    const handleItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Close modal immediately
      setShowUploadItems(false)

      try {
        setOrdersLoading(true)
        const response = await api.items.uploadItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        if (itemsFileInput.current) itemsFileInput.current.value = ""
      }
    }

    const handleOrderItemsUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Close modal immediately
      setShowUploadOrderItems(false)

      try {
        setOrdersLoading(true)
        const response = await api.orders.uploadOrderItemsCSV(file)
        setActionMessage({
          type: "success",
          text: `Order items uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload order items",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
        if (orderItemsFileInput.current) orderItemsFileInput.current.value = ""
      }
    }

    const handleDeliveriesUpload = async (event) => {
      const file = event.target.files[0]
      if (!file) return

      // Close modal immediately
      setShowUploadDeliveries(false)

      try {
        setOrdersLoading(true)
        const response = await api.deliveries.uploadDeliveriesCSV(file)
        setActionMessage({
          type: "success",
          text: `Deliveries uploaded: ${response.success_count} successful, ${response.error_count} failed`,
        })
        setTimeout(() => setActionMessage(null), 5000)
        await fetchOrders(ordersFilter, ordersDataType)
      } catch (err) {
        setActionMessage({
          type: "error",
          text: err.message || "Failed to upload deliveries",
        })
        setTimeout(() => setActionMessage(null), 4000)
      } finally {
        setOrdersLoading(false)
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
                    color: "var(--text-secondary)",
                    marginBottom: "var(--space-2)",
                  }}
                >
                  {insight.title}
                </p>
                <h3
                  style={{
                    fontSize: "var(--text-2xl)",
                    fontWeight: 700,
                    color: primaryColor,
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
          <div
            className="section-wrapper"
            style={{ marginTop: "var(--space-6)" }}
          >
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
                      marginBottom: "var(--space-2)",
                      color: "var(--gray-700)",
                    }}
                  >
                    Orders
                  </h3>
                  <p
                    style={{
                      fontSize: "var(--text-xs)",
                      color: "var(--gray-500)",
                      marginBottom: "var(--space-3)",
                    }}
                  >
                    Showing first 100 of {ordersData.length} orders
                  </p>
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
                      {ordersData.slice(0, 100).map((order, index) => (
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
                      marginBottom: "var(--space-2)",
                      color: "var(--gray-700)",
                    }}
                  >
                    Order Items
                  </h3>
                  <p
                    style={{
                      fontSize: "var(--text-xs)",
                      color: "var(--gray-500)",
                      marginBottom: "var(--space-3)",
                    }}
                  >
                    Showing first 100 of {orderItemsData.length} order items
                  </p>
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
                        {orderItemsData
                          .slice(0, 100)
                          .map((orderItem, index) => (
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
                  <>
                    <p
                      style={{
                        fontSize: "var(--text-sm)",
                        color: "var(--gray-500)",
                        marginBottom: "var(--space-3)",
                      }}
                    >
                      Showing first 100 of {ordersData.length} items
                    </p>
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
                        {ordersData.slice(0, 100).map((item, index) => (
                          <tr
                            key={item.item_id || `item-${index}`}
                            style={{
                              borderBottom: "1px solid var(--gray-200)",
                            }}
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
                  </>
                ) : (
                  <>
                    <p
                      style={{
                        fontSize: "var(--text-sm)",
                        color: "var(--gray-500)",
                        marginBottom: "var(--space-3)",
                      }}
                    >
                      Showing first 100 of {ordersData.length} deliveries
                    </p>
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
                        {ordersData.slice(0, 100).map((delivery, index) => (
                          <tr
                            key={delivery.order_id || `delivery-${index}`}
                            style={{
                              borderBottom: "1px solid var(--gray-200)",
                            }}
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
                  </>
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
      // Map salary_per_hour to hourly_salary for display
      const mappedEmployees = (data.employees || []).map((emp) => ({
        ...emp,
        hourly_salary: emp.salary_per_hour || emp.hourly_salary,
      }))
      setEmployees(mappedEmployees)

      // Calculate total labor cost from all employees (weekly: hourly_salary * 40 hours)
      const totalWeeklyLabor = mappedEmployees.reduce((sum, emp) => {
        const hourlyRate = parseFloat(emp.hourly_salary) || 0
        return sum + hourlyRate * 40 // Assuming 40 hours per week
      }, 0)
      setLaborCost(totalWeeklyLabor)
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

    // Validate file type
    if (!file.name.endsWith('.csv')) {
      setActionMessage({
        type: "error",
        text: "Please upload a CSV file",
      })
      setTimeout(() => setActionMessage(null), 4000)
      event.target.value = ""
      return
    }

    setDelegateLoading(true)
    setShowCsvUploadModal(false)

    try {
      console.log("Uploading CSV file to backend:", file.name)
      
      // Send the entire CSV file to the backend for processing
      const response = await api.staffing.bulkUploadEmployees(file)
      
      console.log("Bulk upload response:", response)

      // Refresh employee list
      await fetchEmployees()

      // Build detailed message from backend response
      const successCount = response.created_count || 0
      const errorCount = response.failed_count || 0
      const createdEmployees = response.created || []
      const failedEmployees = response.failed || []

      let message = `Successfully uploaded ${successCount} employee(s).`
      
      if (errorCount > 0) {
        message += ` ${errorCount} failed:`
        failedEmployees.forEach((emp) => {
          message += `\n• ${emp.email || emp.full_name || 'Unknown'}: ${emp.error || 'Unknown error'}`
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
        text: err.message || err.data?.error || "Failed to upload CSV file",
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
        hourly_salary: parseFloat(delegateForm.hourly_salary),
      })
      setShowDelegateModal(false)
      setDelegateForm({
        full_name: "",
        email: "",
        role: "",
        hourly_salary: "",
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

  // Fetch all requests for Requests Management tab
  const fetchAllRequests = async () => {
    setAllRequestsLoading(true)
    setAllRequestsError("")
    try {
      // Fetch all employees first to get their requests
      const employeesResponse = await api.staffing.getAllEmployees()
      const employeesList = employeesResponse.employees || []

      // Fetch requests for each employee
      const requestsPromises = employeesList.map(async (employee) => {
        try {
          const response = await api.requests.getEmployeeRequests(employee.id)
          return {
            employee,
            requests: response.requests || [],
          }
        } catch (err) {
          console.error(
            `Error fetching requests for ${employee.full_name}:`,
            err,
          )
          return {
            employee,
            requests: [],
          }
        }
      })

      const employeeRequestsData = await Promise.all(requestsPromises)

      // Filter to only include employees with requests
      const employeesWithRequests = employeeRequestsData.filter(
        (data) => data.requests.length > 0,
      )

      setAllRequests(employeesWithRequests)
    } catch (err) {
      console.error("Error fetching all requests:", err)
      setAllRequestsError(err.message || "Failed to load requests")
    } finally {
      setAllRequestsLoading(false)
    }
  }

  // Handle approve request from Requests Management tab
  const handleApproveRequestFromTab = async (employeeId, requestId) => {
    setRequestActionLoading(true)
    try {
      await api.requests.approveRequest(employeeId, requestId)
      setRequestActionMessage({
        type: "success",
        text: "Request approved successfully!",
      })
      setTimeout(() => setRequestActionMessage(null), 3000)
      // Refresh the requests list
      await fetchAllRequests()
    } catch (err) {
      setRequestActionMessage({
        type: "error",
        text: err.message || "Failed to approve request",
      })
      setTimeout(() => setRequestActionMessage(null), 3000)
    } finally {
      setRequestActionLoading(false)
    }
  }

  // Handle decline request from Requests Management tab
  const handleDeclineRequestFromTab = async (employeeId, requestId) => {
    setRequestActionLoading(true)
    try {
      await api.requests.declineRequest(employeeId, requestId)
      setRequestActionMessage({
        type: "success",
        text: "Request declined successfully!",
      })
      setTimeout(() => setRequestActionMessage(null), 3000)
      // Refresh the requests list
      await fetchAllRequests()
    } catch (err) {
      setRequestActionMessage({
        type: "error",
        text: err.message || "Failed to decline request",
      })
      setTimeout(() => setRequestActionMessage(null), 3000)
    } finally {
      setRequestActionLoading(false)
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

  // Load all requests when requests tab is active
  useEffect(() => {
    if (activeTab === "requests") {
      fetchAllRequests()
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
                        {emp.hourly_salary != null
                          ? `$${emp.hourly_salary}`
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
                      value={delegateForm.hourly_salary}
                      onChange={(e) =>
                        setDelegateForm({
                          ...delegateForm,
                          hourly_salary: e.target.value,
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
                      {selectedEmployee.hourly_salary != null
                        ? `$${selectedEmployee.hourly_salary}`
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
                    {employeeRequests.map((req) => {
                      const isPending =
                        req.status === "in queue" || req.status === "pending"
                      const isApproved = req.status === "approved"
                      return (
                        <div
                          key={req.request_id}
                          className={`alert-card ${isPending ? "alert-medium" : isApproved ? "alert-low" : "alert-high"}`}
                        >
                          <div className="alert-header">
                            <div
                              className={`alert-badge ${isPending ? "priority-medium" : isApproved ? "priority-low" : "priority-high"}`}
                            >
                              {req.status === "in queue"
                                ? "PENDING"
                                : req.status?.toUpperCase() || "PENDING"}
                            </div>
                            <span className="alert-timestamp">
                              {req.type === "calloff"
                                ? "Call Off"
                                : req.type === "holiday"
                                  ? "Holiday / Leave"
                                  : req.type === "resign"
                                    ? "Resignation"
                                    : req.type}
                            </span>
                          </div>
                          <p className="alert-message">
                            {req.message || "No reason provided"}
                          </p>
                          {(req.start_date || req.end_date) && (
                            <p
                              className="alert-timestamp"
                              style={{ marginTop: "8px" }}
                            >
                              {req.start_date && req.end_date
                                ? `${req.start_date} to ${req.end_date}`
                                : req.start_date || req.end_date}
                            </p>
                          )}
                          {isPending && (
                            <div className="alert-actions">
                              <button
                                className="btn-primary btn-sm"
                                onClick={() =>
                                  handleApproveRequest(
                                    selectedEmployee.id,
                                    req.request_id,
                                  )
                                }
                                style={{
                                  backgroundColor: "#10b981",
                                  borderColor: "#10b981",
                                }}
                              >
                                ✓ Approve
                              </button>
                              <button
                                className="btn-secondary btn-sm"
                                onClick={() =>
                                  handleDeclineRequest(
                                    selectedEmployee.id,
                                    req.request_id,
                                  )
                                }
                                style={{
                                  color: accentColor,
                                  borderColor: accentColor,
                                }}
                              >
                                ✕ Decline
                              </button>
                            </div>
                          )}
                        </div>
                      )
                    })}
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
                    Required columns: full_name, email, role, hourly_salary
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
  // REQUESTS MANAGEMENT
  // ============================================================================

  const renderRequests = () => {
    const getRequestTypeLabel = (type) => {
      const labels = {
        calloff: "Call Off",
        holiday: "Holiday / Leave",
        resign: "Resignation",
      }
      return labels[type] || type
    }

    const getStatusBadgeClass = (status) => {
      switch (status) {
        case "approved":
          return "status-badge status-approved"
        case "declined":
          return "status-badge status-declined"
        case "pending":
        default:
          return "status-badge status-pending"
      }
    }

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">Employee Requests Management</h1>
            <p className="page-subtitle">
              Review and manage employee time-off and other requests
            </p>
          </div>
        </div>

        {requestActionMessage && (
          <div
            className={`alert ${
              requestActionMessage.type === "success"
                ? "alert-success"
                : "alert-error"
            }`}
            style={{ marginBottom: "var(--space-4)" }}
          >
            {requestActionMessage.text}
          </div>
        )}

        {allRequestsLoading ? (
          <div className="loading-state">
            <div className="spinner"></div>
            <p>Loading requests...</p>
          </div>
        ) : allRequestsError ? (
          <div className="error-state">
            <img
              src={MissedTargetIcon}
              alt="Error"
              className="error-icon-svg"
            />
            <h3>Error Loading Requests</h3>
            <p>{allRequestsError}</p>
            <button className="btn-primary" onClick={fetchAllRequests}>
              Retry
            </button>
          </div>
        ) : allRequests.length === 0 ? (
          <div className="empty-state">
            <img src={InfoIcon} alt="No Requests" className="empty-icon-svg" />
            <h3>No Pending Requests</h3>
            <p>There are currently no employee requests to review.</p>
          </div>
        ) : (
          <div className="requests-container">
            {allRequests.map(({ employee, requests }) => (
              <div key={employee.id} className="employee-requests-section">
                <div className="employee-header">
                  <div className="employee-info">
                    <div className="employee-avatar">
                      {employee.full_name
                        .split(" ")
                        .map((n) => n[0])
                        .join("")
                        .toUpperCase()
                        .slice(0, 2)}
                    </div>
                    <div>
                      <h3 className="employee-name">{employee.full_name}</h3>
                      <p className="employee-role">{employee.user_role}</p>
                    </div>
                  </div>
                  <div className="requests-count">
                    {requests.length} Request{requests.length !== 1 ? "s" : ""}
                  </div>
                </div>

                <div className="requests-list">
                  {requests.map((request) => {
                    const isPending =
                      request.status === "in queue" ||
                      request.status === "pending"
                    return (
                      <div key={request.request_id} className="request-card">
                        <div className="request-header">
                          <div className="request-type">
                            {getRequestTypeLabel(request.type)}
                          </div>
                          <span
                            className={getStatusBadgeClass(
                              request.status === "in queue"
                                ? "pending"
                                : request.status,
                            )}
                          >
                            {request.status === "in queue"
                              ? "PENDING"
                              : request.status?.toUpperCase() || "PENDING"}
                          </span>
                        </div>
                        <div className="request-body">
                          <p className="request-message">{request.message}</p>
                          {request.start_date && (
                            <div className="request-dates">
                              <strong>Dates:</strong>{" "}
                              {new Date(
                                request.start_date,
                              ).toLocaleDateString()}
                              {request.end_date &&
                                ` - ${new Date(
                                  request.end_date,
                                ).toLocaleDateString()}`}
                            </div>
                          )}
                        </div>
                        <div className="request-footer">
                          <span className="request-date">
                            Submitted:{" "}
                            {new Date(
                              request.submitted_at,
                            ).toLocaleDateString()}
                          </span>
                          {isPending && (
                            <div className="request-actions">
                              <button
                                className="btn-approve"
                                onClick={() =>
                                  handleApproveRequestFromTab(
                                    employee.id,
                                    request.request_id,
                                  )
                                }
                                disabled={requestActionLoading}
                                style={{
                                  backgroundColor: "#10b981",
                                  color: "#ffffff",
                                  border: "none",
                                }}
                              >
                                ✓ Approve
                              </button>
                              <button
                                className="btn-decline"
                                onClick={() =>
                                  handleDeclineRequestFromTab(
                                    employee.id,
                                    request.request_id,
                                  )
                                }
                                disabled={requestActionLoading}
                                style={{
                                  backgroundColor: accentColor,
                                  color: "#ffffff",
                                  border: "none",
                                }}
                              >
                                ✕ Decline
                              </button>
                            </div>
                          )}
                        </div>
                      </div>
                    )
                  })}
                </div>
              </div>
            ))}
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

      await api.roles.updateRole(selectedRole.role_id, payload)
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
      role: role.role_id,
      min_needed_per_shift: role.min_present || 1,
      items_per_role_per_hour: role.items_per_employee_per_hour || "",
      need_for_demand: role.producing || false,
      independent:
        role.is_independent !== undefined ? role.is_independent : true,
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
            Shift Rules & Operating Hours
          </h2>
        </div>
        <p className="section-description">
          Configure shift scheduling parameters and operating hours for your
          organization
        </p>

        <div className="settings-grid" style={{ marginTop: "var(--space-4)" }}>
          {/* Basic Shift Parameters */}
          <div className="setting-item">
            <label className="setting-label">
              Minimum Shift Length (hours)
            </label>
            <input
              className="setting-input"
              type="number"
              min="1"
              max="24"
              value={shiftRulesForm.shift_min_hours}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  shift_min_hours: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">
              Maximum Shift Length (hours)
            </label>
            <input
              className="setting-input"
              type="number"
              min="1"
              max="24"
              value={shiftRulesForm.shift_max_hours}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  shift_max_hours: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Minimum Weekly Hours</label>
            <input
              className="setting-input"
              type="number"
              min="0"
              max="168"
              value={shiftRulesForm.min_weekly_hours}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  min_weekly_hours: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Maximum Weekly Hours</label>
            <input
              className="setting-input"
              type="number"
              min="0"
              max="168"
              value={shiftRulesForm.max_weekly_hours}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  max_weekly_hours: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">
              Minimum Rest Slots Between Shifts
            </label>
            <input
              className="setting-input"
              type="number"
              min="0"
              max="24"
              value={shiftRulesForm.min_rest_slots}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  min_rest_slots: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Slot Length (hours)</label>
            <input
              className="setting-input"
              type="number"
              step="0.25"
              min="0.25"
              max="4"
              value={shiftRulesForm.slot_len_hour}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  slot_len_hour: e.target.value,
                })
              }
            />
            <p
              style={{
                fontSize: "var(--text-xs)",
                color: "var(--gray-500)",
                marginTop: "var(--space-1)",
              }}
            >
              Time unit for scheduling (e.g., 0.5 = 30 minutes)
            </p>
          </div>
          <div className="setting-item">
            <label className="setting-label">
              Minimum Shift Length (slots)
            </label>
            <input
              className="setting-input"
              type="number"
              min="1"
              max="48"
              value={shiftRulesForm.min_shift_length_slots}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  min_shift_length_slots: e.target.value,
                })
              }
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Waiting Time (minutes)</label>
            <input
              className="setting-input"
              type="number"
              min="0"
              max="120"
              value={shiftRulesForm.waiting_time}
              onChange={(e) =>
                setShiftRulesForm({
                  ...shiftRulesForm,
                  waiting_time: e.target.value,
                })
              }
            />
          </div>
        </div>

        {/* Toggle Switches - with spacing */}
        <div style={{ marginTop: "var(--space-8)" }}>
          <div
            className="toggle-item"
            style={{ marginBottom: "var(--space-4)" }}
          >
            <div className="toggle-content">
              <h4 className="toggle-title">Fixed Shifts</h4>
              <p className="toggle-description">
                Enable if you have predefined shift times each day
              </p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={shiftRulesForm.fixed_shifts}
                onChange={(e) =>
                  setShiftRulesForm({
                    ...shiftRulesForm,
                    fixed_shifts: e.target.checked,
                  })
                }
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          {shiftRulesForm.fixed_shifts && (
            <div
              style={{
                marginTop: "var(--space-4)",
                marginBottom: "var(--space-6)",
                padding: "var(--space-5)",
                background: "var(--gray-50)",
                borderRadius: "var(--radius-lg)",
                border: "1px solid var(--gray-200)",
              }}
            >
              <h4
                style={{
                  marginBottom: "var(--space-4)",
                  fontSize: "var(--text-base)",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                }}
              >
                Fixed Shift Configuration
              </h4>

              <div
                className="setting-item"
                style={{ marginBottom: "var(--space-5)" }}
              >
                <label className="setting-label">
                  Number of Shifts per Day
                </label>
                <input
                  className="setting-input"
                  type="number"
                  min="1"
                  max="10"
                  value={shiftRulesForm.number_of_shifts_per_day}
                  onChange={(e) => {
                    const num = parseInt(e.target.value)
                    setShiftRulesForm({
                      ...shiftRulesForm,
                      number_of_shifts_per_day: num,
                    })

                    // Adjust shift times array
                    const newShifts = [...shiftTimes]
                    while (newShifts.length < num) {
                      const lastShift = newShifts[newShifts.length - 1] || {
                        to: "09:00",
                      }
                      newShifts.push({ from: lastShift.to, to: "17:00" })
                    }
                    while (newShifts.length > num) {
                      newShifts.pop()
                    }
                    setShiftTimes(newShifts)
                  }}
                />
              </div>

              <h5
                style={{
                  marginBottom: "var(--space-3)",
                  fontSize: "var(--text-sm)",
                  fontWeight: 600,
                  color: "var(--text-primary)",
                }}
              >
                Default Shift Times
              </h5>
              {shiftTimes.map((shift, index) => (
                <div
                  key={index}
                  style={{
                    display: "flex",
                    gap: "var(--space-3)",
                    marginBottom: "var(--space-3)",
                    alignItems: "center",
                  }}
                >
                  <span
                    style={{
                      minWidth: "80px",
                      fontSize: "var(--text-sm)",
                      fontWeight: 500,
                      color: "var(--text-primary)",
                    }}
                  >
                    Shift {index + 1}:
                  </span>
                  <input
                    type="time"
                    className="setting-input"
                    style={{ flex: 1 }}
                    value={shift.from}
                    onChange={(e) => {
                      const newShifts = [...shiftTimes]
                      newShifts[index].from = e.target.value
                      setShiftTimes(newShifts)
                    }}
                  />
                  <span
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--gray-500)",
                    }}
                  >
                    to
                  </span>
                  <input
                    type="time"
                    className="setting-input"
                    style={{ flex: 1 }}
                    value={shift.to}
                    onChange={(e) => {
                      const newShifts = [...shiftTimes]
                      newShifts[index].to = e.target.value
                      setShiftTimes(newShifts)
                    }}
                  />
                </div>
              ))}

              <div style={{ marginTop: "var(--space-6)" }}>
                <h5
                  style={{
                    marginBottom: "var(--space-3)",
                    fontSize: "var(--text-sm)",
                    fontWeight: 600,
                    color: "var(--text-primary)",
                  }}
                >
                  Custom Day Shifts
                </h5>

                {[
                  "monday",
                  "tuesday",
                  "wednesday",
                  "thursday",
                  "friday",
                  "saturday",
                  "sunday",
                ].map((day) => (
                  <div key={day} style={{ marginBottom: "var(--space-4)" }}>
                    <div
                      className="toggle-item"
                      style={{
                        padding: "var(--space-3)",
                        background: "var(--bg-primary)",
                        borderRadius: "var(--radius-md)",
                        border: "1px solid var(--gray-300)",
                      }}
                    >
                      <div className="toggle-content">
                        <h4
                          className="toggle-title"
                          style={{
                            fontSize: "var(--text-sm)",
                            color: "var(--text-primary)",
                          }}
                        >
                          {day}
                        </h4>
                        <p
                          className="toggle-description"
                          style={{ fontSize: "var(--text-xs)" }}
                        >
                          Use custom shifts for this day
                        </p>
                      </div>
                      <label className="toggle-switch">
                        <input
                          type="checkbox"
                          checked={!!customDayShifts[day]}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setCustomDayShifts({
                                ...customDayShifts,
                                [day]: [...shiftTimes],
                              })
                            } else {
                              const newCustom = { ...customDayShifts }
                              delete newCustom[day]
                              setCustomDayShifts(newCustom)
                            }
                          }}
                        />
                        <span className="toggle-slider"></span>
                      </label>
                    </div>

                    {customDayShifts[day] && (
                      <div
                        style={{
                          marginTop: "var(--space-3)",
                          marginLeft: "var(--space-4)",
                          padding: "var(--space-4)",
                          background: "var(--bg-primary)",
                          borderRadius: "var(--radius-md)",
                          border: "1px solid var(--gray-300)",
                        }}
                      >
                        {customDayShifts[day].map((shift, idx) => (
                          <div
                            key={idx}
                            style={{
                              display: "flex",
                              gap: "var(--space-2)",
                              marginBottom: "var(--space-2)",
                              alignItems: "center",
                            }}
                          >
                            <span
                              style={{
                                minWidth: "60px",
                                fontSize: "var(--text-xs)",
                                color: "var(--text-primary)",
                              }}
                            >
                              Shift {idx + 1}:
                            </span>
                            <input
                              type="time"
                              className="setting-input"
                              style={{
                                flex: 1,
                                fontSize: "var(--text-xs)",
                                padding: "var(--space-2)",
                              }}
                              value={shift.from}
                              onChange={(e) => {
                                const newCustom = { ...customDayShifts }
                                newCustom[day][idx].from = e.target.value
                                setCustomDayShifts(newCustom)
                              }}
                            />
                            <span
                              style={{
                                fontSize: "var(--text-xs)",
                                color: "var(--gray-500)",
                              }}
                            >
                              to
                            </span>
                            <input
                              type="time"
                              className="setting-input"
                              style={{
                                flex: 1,
                                fontSize: "var(--text-xs)",
                                padding: "var(--space-2)",
                              }}
                              value={shift.to}
                              onChange={(e) => {
                                const newCustom = { ...customDayShifts }
                                newCustom[day][idx].to = e.target.value
                                setCustomDayShifts(newCustom)
                              }}
                            />
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          <div
            className="toggle-item"
            style={{ marginBottom: "var(--space-4)" }}
          >
            <div className="toggle-content">
              <h4 className="toggle-title">Meet All Demand</h4>
              <p className="toggle-description">
                Schedule enough staff to meet all predicted demand
              </p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={shiftRulesForm.meet_all_demand}
                onChange={(e) =>
                  setShiftRulesForm({
                    ...shiftRulesForm,
                    meet_all_demand: e.target.checked,
                  })
                }
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div
            className="toggle-item"
            style={{ marginBottom: "var(--space-4)" }}
          >
            <div className="toggle-content">
              <h4 className="toggle-title">Receiving Phone Orders</h4>
              <p className="toggle-description">
                Organization accepts phone orders
              </p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={shiftRulesForm.receiving_phone}
                onChange={(e) =>
                  setShiftRulesForm({
                    ...shiftRulesForm,
                    receiving_phone: e.target.checked,
                  })
                }
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div
            className="toggle-item"
            style={{ marginBottom: "var(--space-4)" }}
          >
            <div className="toggle-content">
              <h4 className="toggle-title">Delivery Service</h4>
              <p className="toggle-description">
                Organization offers delivery service
              </p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={shiftRulesForm.delivery}
                onChange={(e) =>
                  setShiftRulesForm({
                    ...shiftRulesForm,
                    delivery: e.target.checked,
                  })
                }
              />
              <span className="toggle-slider"></span>
            </label>
          </div>

          <div
            className="toggle-item"
            style={{ marginBottom: "var(--space-4)" }}
          >
            <div className="toggle-content">
              <h4 className="toggle-title">Accepting Orders</h4>
              <p className="toggle-description">
                Organization is currently accepting new orders
              </p>
            </div>
            <label className="toggle-switch">
              <input
                type="checkbox"
                checked={shiftRulesForm.accepting_orders}
                onChange={(e) =>
                  setShiftRulesForm({
                    ...shiftRulesForm,
                    accepting_orders: e.target.checked,
                  })
                }
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>

        {/* Operating Hours */}
        <div style={{ marginTop: "var(--space-8)" }}>
          <h4
            style={{
              marginBottom: "var(--space-4)",
              fontSize: "var(--text-lg)",
              fontWeight: 600,
              color: "var(--text-primary)",
            }}
          >
            Operating Hours
          </h4>
          <div style={{ display: "grid", gap: "var(--space-3)" }}>
            {operatingHours.map((day, index) => (
              <div
                key={day.weekday}
                style={{
                  display: "flex",
                  gap: "var(--space-3)",
                  alignItems: "center",
                  padding: "var(--space-4)",
                  background: "var(--gray-50)",
                  borderRadius: "var(--radius-md)",
                  border: "1px solid var(--gray-200)",
                }}
              >
                <span
                  style={{
                    minWidth: "100px",
                    fontWeight: 500,
                    color: "var(--text-primary)",
                  }}
                >
                  {day.weekday}
                </span>
                <label
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "var(--space-2)",
                  }}
                >
                  <input
                    type="checkbox"
                    checked={day.closed || false}
                    onChange={(e) => {
                      const newHours = [...operatingHours]
                      newHours[index].closed = e.target.checked
                      if (e.target.checked) {
                        newHours[index].opening_time = ""
                        newHours[index].closing_time = ""
                      }
                      setOperatingHours(newHours)
                    }}
                  />
                  <span
                    style={{
                      fontSize: "var(--text-sm)",
                      color: "var(--text-primary)",
                    }}
                  >
                    Closed
                  </span>
                </label>
                {!day.closed && (
                  <>
                    <input
                      type="time"
                      className="setting-input"
                      style={{ flex: 1 }}
                      value={day.opening_time}
                      onChange={(e) => {
                        const newHours = [...operatingHours]
                        newHours[index].opening_time = e.target.value
                        setOperatingHours(newHours)
                      }}
                    />
                    <span style={{ color: "var(--gray-500)" }}>to</span>
                    <input
                      type="time"
                      className="setting-input"
                      style={{ flex: 1 }}
                      value={day.closing_time}
                      onChange={(e) => {
                        const newHours = [...operatingHours]
                        newHours[index].closing_time = e.target.value
                        setOperatingHours(newHours)
                      }}
                    />
                  </>
                )}
              </div>
            ))}
          </div>
        </div>

        <div
          className="settings-footer"
          style={{ marginTop: "var(--space-8)" }}
        >
          <button
            className="btn-secondary"
            onClick={() => {
              fetchShiftRules()
              setActionMessage({
                type: "success",
                text: "Reset to saved values",
              })
              setTimeout(() => setActionMessage(null), 3000)
            }}
          >
            Reset to Defaults
          </button>
          <button
            className="btn-primary"
            onClick={handleSaveShiftRules}
            disabled={shiftRulesLoading}
          >
            {shiftRulesLoading ? "Saving..." : "Save Shift Rules"}
          </button>
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
                    key={role.role_id}
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
                      <span className="badge badge-primary">
                        {role.role_id}
                      </span>
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.min_present}
                    </td>
                    <td
                      style={{
                        padding: "var(--space-4)",
                        fontSize: "var(--text-base)",
                        color: "var(--gray-700)",
                        verticalAlign: "middle",
                      }}
                    >
                      {role.producing ? (
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
                      {role.items_per_employee_per_hour != null
                        ? role.items_per_employee_per_hour
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
                      {role.is_independent ? (
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
                      {role.role_id !== "admin" &&
                        role.role_id !== "manager" && (
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
                      {(role.role_id === "admin" ||
                        role.role_id === "manager") && (
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
              <strong>{confirmDeleteRole.role_id}</strong>? This action cannot
              be undone and may fail if employees are assigned to this role.
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
                onClick={() => handleDeleteRole(confirmDeleteRole.role_id)}
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

    // Get data from currentUser
    const displayName = currentUser?.full_name || "Loading..."
    const displayEmail = currentUser?.email || "Loading..."
    const displayRole = currentUser?.user_role || "Loading..."
    const displayOrganization =
      currentUser?.organization_name || currentUser?.organization || "N/A"
    const displaySalary =
      currentUser?.hourly_salary != null
        ? `$${currentUser.hourly_salary}/hr`
        : "N/A"
    const displayMaxHours = currentUser?.max_hours_per_week || "N/A"
    const displayPrefHours = currentUser?.preferred_hours_per_week || "N/A"
    const displayMaxConsecSlots = currentUser?.max_consec_slots || "N/A"
    const displayOnCall =
      currentUser?.on_call !== undefined
        ? currentUser.on_call
          ? "Yes"
          : "No"
        : "N/A"

    // Extract insights data for statistics
    const getInsightValue = (titleMatch) => {
      const insight = insights.find((i) =>
        i.title.toLowerCase().includes(titleMatch.toLowerCase()),
      )
      return insight ? insight.statistic : "N/A"
    }

    // Get role-specific statistics
    const getRoleStats = () => {
      if (currentUser?.user_role === "admin") {
        return {
          stat1: {
            label: "Total Employees",
            value: getInsightValue("Number of Employees"),
          },
          stat2: { label: "Active Roles", value: roles.length },
          stat3: { label: "Revenue", value: getInsightValue("Total Revenue") },
          stat4: {
            label: "Orders Today",
            value: getInsightValue("Orders Served Today"),
          },
        }
      } else if (currentUser?.user_role === "manager") {
        return {
          stat1: {
            label: "Team Size",
            value: getInsightValue("Number of Employees"),
          },
          stat2: {
            label: "Deliveries Today",
            value: getInsightValue("deliveries today"),
          },
          stat3: {
            label: "Orders Today",
            value: getInsightValue("Orders Served Today"),
          },
          stat4: { label: "My Salary", value: displaySalary },
        }
      } else {
        // Employee
        return {
          stat1: { label: "My Salary", value: displaySalary },
          stat2: { label: "My Role", value: displayRole },
          stat3: {
            label: "Hours This Week",
            value: profileData?.hours_worked_this_week || "N/A",
          },
          stat4: {
            label: "Total Hours",
            value: profileData?.hours_worked || "N/A",
          },
        }
      }
    }

    const roleStats = getRoleStats()

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
                <p
                  className="profile-role"
                  style={{ textTransform: "capitalize" }}
                >
                  {displayRole}
                </p>
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
                    <span className="info-value">{displayOrganization}</span>
                  </div>
                  {currentUser?.user_role !== "admin" && (
                    <>
                      <div className="info-item">
                        <span className="info-label">Hourly Rate</span>
                        <span className="info-value">{displaySalary}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Max Hours/Week</span>
                        <span className="info-value">{displayMaxHours}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">Preferred Hours/Week</span>
                        <span className="info-value">{displayPrefHours}</span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">
                          Max Consecutive Slots
                        </span>
                        <span className="info-value">
                          {displayMaxConsecSlots}
                        </span>
                      </div>
                      <div className="info-item">
                        <span className="info-label">On Call</span>
                        <span className="info-value">
                          <span
                            className={`badge ${currentUser?.on_call ? "badge-primary" : "badge-secondary"}`}
                          >
                            {displayOnCall}
                          </span>
                        </span>
                      </div>
                    </>
                  )}
                </div>
              </div>

              {/* Work Statistics Card */}
              {currentUser?.user_role !== "admin" && profileData && (
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
                          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                        />
                      </svg>
                      Work Hours
                    </h3>
                  </div>
                  <div className="profile-info-grid">
                    <div className="info-item">
                      <span className="info-label">Total Hours Worked</span>
                      <span
                        className="info-value"
                        style={{
                          fontSize: "var(--text-2xl)",
                          fontWeight: 700,
                          color: "var(--color-primary)",
                        }}
                      >
                        {profileData.hours_worked || "0"} hrs
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">This Week</span>
                      <span
                        className="info-value"
                        style={{
                          fontSize: "var(--text-2xl)",
                          fontWeight: 700,
                          color: "var(--color-secondary)",
                        }}
                      >
                        {profileData.hours_worked_this_week || "0"} hrs
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Utilization Rate</span>
                      <span className="info-value">
                        {currentUser?.max_hours_per_week &&
                        profileData.hours_worked_this_week
                          ? `${((profileData.hours_worked_this_week / currentUser.max_hours_per_week) * 100).toFixed(1)}%`
                          : "N/A"}
                      </span>
                    </div>
                    <div className="info-item">
                      <span className="info-label">Weekly Earnings</span>
                      <span
                        className="info-value"
                        style={{ color: "var(--color-accent)" }}
                      >
                        {currentUser?.hourly_salary &&
                        profileData.hours_worked_this_week
                          ? `$${(currentUser.hourly_salary * profileData.hours_worked_this_week).toFixed(2)}`
                          : "N/A"}
                      </span>
                    </div>
                  </div>
                </div>
              )}

              {/* Statistics Card */}
              <div
                className="profile-card"
                data-animation="slide-up"
                style={{
                  animationDelay:
                    currentUser?.user_role !== "admin" && profileData
                      ? "0.2s"
                      : "0.1s",
                }}
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
                    {currentUser?.user_role === "admin"
                      ? "Organization Statistics"
                      : "My Statistics"}
                  </h3>
                </div>
                <div className="profile-stats-grid">
                  <div className="stat-item">
                    <div className="stat-value">{roleStats.stat1.value}</div>
                    <div className="stat-label">{roleStats.stat1.label}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{roleStats.stat2.value}</div>
                    <div className="stat-label">{roleStats.stat2.label}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{roleStats.stat3.value}</div>
                    <div className="stat-label">{roleStats.stat3.label}</div>
                  </div>
                  <div className="stat-item">
                    <div className="stat-value">{roleStats.stat4.value}</div>
                    <div className="stat-label">{roleStats.stat4.label}</div>
                  </div>
                </div>
              </div>

              {/* Security Settings Card */}
              <div
                className="profile-card profile-card-full"
                data-animation="slide-up"
                style={{
                  animationDelay:
                    currentUser?.user_role !== "admin" && profileData
                      ? "0.3s"
                      : "0.2s",
                }}
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
                      <div className="info-subtitle">
                        <span className="badge badge-primary">Active</span>
                      </div>
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
                  {currentUser?.updated_at && (
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
                          d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
                        />
                      </svg>
                      <div>
                        <div className="info-title">Last Updated</div>
                        <div className="info-subtitle">
                          {new Date(currentUser.updated_at).toLocaleDateString(
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
                <h1 className="logo">AntiClockWise</h1>
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
                  {currentUser?.full_name || "Admin"}
                </div>
                <div className="user-role">
                  {currentUser?.user_role || "Administrator"}
                </div>
              </div>
            )}
          </div>
          {!sidebarCollapsed && (
            <button
              className="logout-btn"
              onClick={async () => {
                try {
                  await api.auth.logout()
                  // Redirect to login page
                  window.location.href = "/"
                } catch (err) {
                  console.error("Logout failed:", err)
                  // Still redirect even if API call fails
                  window.location.href = "/"
                }
              }}
            >
              Logout
            </button>
          )}
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
            {activeTab === "requests" && renderRequests()}
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

      {/* Upload Loading Overlay */}
      {(campaignsLoading || ordersLoading) && (
        <div className="upload-loader-overlay">
          <div className="loader-container">
            <svg
              width="120"
              height="120"
              viewBox="0 0 120 120"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <g transform="translate(60, 60)">
                <path
                  className="iso-slice slice-1"
                  d="M0 -15 L25 0 L0 15 L-25 0 Z"
                />
                <path
                  className="iso-slice slice-2"
                  d="M0 -15 L25 0 L0 15 L-25 0 Z"
                />
                <path
                  className="iso-slice slice-3"
                  d="M0 -15 L25 0 L0 15 L-25 0 Z"
                />
              </g>
            </svg>
            <div className="loader-text">Uploading data...</div>
          </div>
        </div>
      )}
    </div>
  )
}

export default AdminDashboard
