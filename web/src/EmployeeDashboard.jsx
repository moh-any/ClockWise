import { useState, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import "./EmployeeDashboard.css"
import api from "./services/api"

// Import SVG icons
import HomeIcon from "./Icons/Home_Icon.svg"
import ScheduleIcon from "./Icons/Schedule_Icon.svg"
import SettingsIcon from "./Icons/Settings_Icon.svg"
import InfoIcon from "./Icons/Info_Icon.svg"
import LightModeIcon from "./Icons/Light-Mode-Icon.svg"
import DarkModeIcon from "./Icons/Dark-Mode-Icon.svg"
import MissedTargetIcon from "./Icons/Missed-Target-Icon.svg"

function EmployeeDashboard() {
  const navigate = useNavigate()
  const [activeTab, setActiveTab] = useState("home")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [showEmployeeProfile, setShowEmployeeProfile] = useState(false)
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
  const [profileData, setProfileData] = useState(null)
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

  // Preferences state
  const [preferences, setPreferences] = useState([])
  const [userRoles, setUserRoles] = useState([])
  const [maxHoursPerWeek, setMaxHoursPerWeek] = useState(40)
  const [preferredHoursPerWeek, setPreferredHoursPerWeek] = useState(35)
  const [maxConsecSlots, setMaxConsecSlots] = useState(8)
  const [onCall, setOnCall] = useState(false)
  const [roles, setRoles] = useState([])
  const [preferencesLoading, setPreferencesLoading] = useState(false)
  const [preferencesError, setPreferencesError] = useState("")
  const [preferencesSuccess, setPreferencesSuccess] = useState("")
  const [weeklyAvailabilitySaved, setWeeklyAvailabilitySaved] = useState(false)

  // Requests state
  const [requests, setRequests] = useState([])
  const [requestForm, setRequestForm] = useState({
    type: "calloff",
    message: "",
  })
  const [requestsLoading, setRequestsLoading] = useState(false)
  const [requestsListLoading, setRequestsListLoading] = useState(false)
  const [requestsError, setRequestsError] = useState("")
  const [requestsSuccess, setRequestsSuccess] = useState("")

  // Schedule state
  const [scheduleData, setScheduleData] = useState([])
  const [scheduleLoading, setScheduleLoading] = useState(false)
  const [scheduleError, setScheduleError] = useState("")

  const navigationItems = [
    { id: "home", label: "Dashboard", icon: HomeIcon },
    { id: "schedule", label: "Schedule", icon: ScheduleIcon },
    { id: "requests", label: "Requests", icon: InfoIcon },
    { id: "preferences", label: "Preferences", icon: SettingsIcon },
    { id: "profile", label: "Profile", icon: InfoIcon },
  ]

  const days = [
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
  ]
  const daysShort = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

  const getContrastColor = (hexColor) => {
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
      const primary = colors[0] || primaryColor
      const secondary = colors[1] || secondaryColor
      const accent = colors[2] || accentColor

      setPrimaryColor(primary)
      setSecondaryColor(secondary)
      setAccentColor(accent)

      // Set scoped CSS variables for Employee Dashboard
      const empDashboard = document.querySelector(".employee-dashboard-wrapper")
      if (empDashboard) {
        empDashboard.style.setProperty("--emp-color-primary", primary)
        empDashboard.style.setProperty("--emp-color-secondary", secondary)
        empDashboard.style.setProperty("--emp-color-accent", accent)
        empDashboard.style.setProperty(
          "--emp-primary-contrast",
          getContrastColor(primary),
        )
        empDashboard.style.setProperty(
          "--emp-secondary-contrast",
          getContrastColor(secondary),
        )
        empDashboard.style.setProperty(
          "--emp-accent-contrast",
          getContrastColor(accent),
        )
      }
    }
  }, [])

  useEffect(() => {
    // Apply dark mode class to employee dashboard only
    const empDashboard = document.querySelector(".employee-dashboard-wrapper")
    if (empDashboard) {
      if (darkMode) {
        empDashboard.classList.add("dark-mode")
      } else {
        empDashboard.classList.remove("dark-mode")
      }
    }
  }, [darkMode])

  useEffect(() => {
    fetchDashboardData()
    fetchCurrentUser()
  }, [])

  useEffect(() => {
    if (activeTab === "requests") {
      console.log("Requests tab activated, currentUser:", currentUser)
      if (currentUser?.user_id) {
        fetchUserRequests()
      } else {
        console.log("Waiting for currentUser to load...")
      }
    }
  }, [activeTab, currentUser])

  useEffect(() => {
    if (activeTab === "schedule") {
      fetchSchedule()
    }
  }, [activeTab])

  const fetchCurrentUser = async () => {
    try {
      // Try to get from cache first
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        setCurrentUser(parsedUser)
      }

      // Fetch fresh data from API
      const userData = await api.auth.getCurrentUser()
      setCurrentUser(userData)
    } catch (err) {
      console.error("Error fetching user data:", err)
      // Still try to use cached data
      const cached = localStorage.getItem("current_user")
      if (cached) {
        const parsedUser = JSON.parse(cached)
        setCurrentUser(parsedUser)
      }
    }
  }

  const fetchSchedule = async () => {
    try {
      setScheduleLoading(true)
      setScheduleError("")
      const response = await api.dashboard.getMySchedule()
      if (response && response.data) {
        setScheduleData(response.data)
      }
    } catch (err) {
      console.error("Error fetching schedule:", err)
      setScheduleError(err.message || "Failed to load schedule")
    } finally {
      setScheduleLoading(false)
    }
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
        }
      } catch (err) {
        console.error("Error fetching insights:", err)
      }

      // Fetch profile data
      try {
        const profile = await api.profile.getProfile()
        if (profile && profile.data) {
          setProfileData(profile.data)
        }
      } catch (err) {
        console.error("Error fetching profile:", err)
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

      // Fetch preferences
      try {
        const prefsResponse = await api.preferences.getPreferences()
        if (prefsResponse && prefsResponse.data) {
          const prefs = prefsResponse.data
          setPreferences(prefs.preferences || [])
          setUserRoles(prefs.user_roles || [])
          setMaxHoursPerWeek(prefs.max_hours_per_week || 40)
          setPreferredHoursPerWeek(prefs.preferred_hours_per_week || 35)
          setMaxConsecSlots(prefs.max_consec_slots || 8)
          setOnCall(prefs.on_call || false)
        }
      } catch (err) {
        console.error("Error fetching preferences:", err)
      }
    } catch (err) {
      console.error("Error fetching dashboard data:", err)
      setError(err.message || "Failed to load dashboard data")
    } finally {
      setLoading(false)
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
    if (passwordForm.new_password.length < 8) {
      setPasswordError("New password must be at least 8 characters")
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

  const handleLogout = async () => {
    try {
      await api.auth.logout()
      navigate("/")
    } catch (err) {
      console.error("Logout error:", err)
      // Still navigate to home even if API call fails
      navigate("/")
    }
  }

  const handlePreferenceChange = (day, field, value) => {
    const updatedPreferences = [...preferences]
    const dayPref = updatedPreferences.find((p) => p.day === day)

    if (dayPref) {
      dayPref[field] = value
    } else {
      updatedPreferences.push({
        day,
        [field]: value,
        preferred_start_time: "",
        preferred_end_time: "",
        available_start_time: "",
        available_end_time: "",
      })
    }

    setPreferences(updatedPreferences)
    // Reset weekly availability saved flag when user makes changes
    setWeeklyAvailabilitySaved(false)
  }

  // Check if a day has all time fields filled
  const isDayFullyFilled = (dayPref) => {
    return (
      dayPref &&
      dayPref.preferred_start_time &&
      dayPref.preferred_end_time &&
      dayPref.available_start_time &&
      dayPref.available_end_time
    )
  }

  // Check if any day is fully filled
  const isAnyDayFullyFilled = () => {
    return preferences.some(isDayFullyFilled)
  }

  // Check if ALL days are fully filled
  const isAllDaysFilled = () => {
    if (preferences.length !== days.length) return false
    return days.every((day) => {
      const dayPref = preferences.find((p) => p.day === day)
      return isDayFullyFilled(dayPref)
    })
  }

  // Copy first fully filled day to all days
  const handleApplyToAllDays = () => {
    const fullyFilledDay = preferences.find(isDayFullyFilled)

    if (!fullyFilledDay) {
      return
    }

    const updatedPreferences = days.map((day) => ({
      day,
      preferred_start_time: fullyFilledDay.preferred_start_time,
      preferred_end_time: fullyFilledDay.preferred_end_time,
      available_start_time: fullyFilledDay.available_start_time,
      available_end_time: fullyFilledDay.available_end_time,
    }))

    setPreferences(updatedPreferences)
    // Reset weekly availability saved flag when applying to all days
    setWeeklyAvailabilitySaved(false)
  }

  // Save weekly availability (just marks as ready, actual save happens with main Save button)
  const handleSaveWeeklyAvailability = () => {
    if (isAllDaysFilled()) {
      setWeeklyAvailabilitySaved(true)
      setPreferencesSuccess(
        "Weekly availability confirmed! Click 'Save Preferences' to upload.",
      )
      setTimeout(() => {
        setPreferencesSuccess("")
      }, 4000)
    }
  }

  const handleSavePreferences = async () => {
    setPreferencesLoading(true)
    setPreferencesError("")
    setPreferencesSuccess("")

    try {
      // Filter out empty preferences
      const validPreferences = preferences.filter(
        (p) => p.preferred_start_time && p.preferred_end_time,
      )

      await api.preferences.savePreferences({
        preferences: validPreferences,
        user_roles: userRoles,
        max_hours_per_week: maxHoursPerWeek,
        preferred_hours_per_week: preferredHoursPerWeek,
        max_consec_slots: maxConsecSlots,
        on_call: onCall,
      })

      setPreferencesSuccess("Preferences saved successfully!")
      // Reset weekly availability flag after successful save
      setWeeklyAvailabilitySaved(false)
      setTimeout(() => {
        setPreferencesSuccess("")
      }, 3000)
    } catch (err) {
      setPreferencesError(err.message || "Failed to save preferences")
    } finally {
      setPreferencesLoading(false)
    }
  }

  // Fetch user's submitted requests
  const fetchUserRequests = async () => {
    const orgId = localStorage.getItem("org_id")
    if (!currentUser?.user_id) {
      console.log("Cannot fetch requests: user_id not available", currentUser)
      return
    }
    if (!orgId) {
      console.log("Cannot fetch requests: organization_id not available")
      return
    }

    console.log("Fetching requests for employee:", currentUser.user_id)
    setRequestsListLoading(true)
    setRequestsError("")
    try {
      const response = await api.requests.getEmployeeRequests(
        currentUser.user_id,
      )
      console.log("Requests fetched successfully:", response)
      setRequests(response.requests || [])
      if (response.requests && response.requests.length === 0) {
        console.log("No requests found for this employee")
      }
    } catch (err) {
      console.error("Error fetching requests:", err)
      setRequestsError(err.message || "Failed to load requests")
      setRequests([])
    } finally {
      setRequestsListLoading(false)
    }
  }

  // Submit a new request
  const handleSubmitRequest = async (e) => {
    e.preventDefault()
    setRequestsLoading(true)
    setRequestsError("")
    setRequestsSuccess("")

    try {
      await api.requests.submitRequest(requestForm)
      setRequestsSuccess("Request submitted successfully!")
      setRequestForm({
        type: "calloff",
        message: "",
      })

      // Refresh the requests list
      await fetchUserRequests()

      setTimeout(() => {
        setRequestsSuccess("")
      }, 3000)
    } catch (err) {
      setRequestsError(err.message || "Failed to submit request")
    } finally {
      setRequestsLoading(false)
    }
  }

  const renderSkeletonLoader = () => (
    <div className="skeleton-loader">
      <div className="skeleton-card"></div>
      <div className="skeleton-card"></div>
      <div className="skeleton-card"></div>
    </div>
  )

  const renderHomeDashboard = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">
            Welcome Back, {currentUser?.full_name?.split(" ")[0] || "Employee"}
          </h1>
          <p className="page-subtitle">Your personal workspace dashboard</p>
        </div>
      </div>

      {/* Profile Summary Cards */}
      {profileData && (
        <div className="kpi-grid">
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Hours Worked This Week</div>
              <div className="kpi-value">
                {profileData.hours_worked_this_week || "0"} hrs
              </div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Total Hours Worked</div>
              <div className="kpi-value">
                {profileData.hours_worked || "0"} hrs
              </div>
            </div>
          </div>
          <div className="kpi-card">
            <div className="kpi-content">
              <div className="kpi-label">Your Role</div>
              <div className="kpi-value">{profileData.user_role || "N/A"}</div>
            </div>
          </div>
        </div>
      )}

      {/* Insights Section */}
      {insights && insights.length > 0 && (
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">
              <img src={InfoIcon} alt="Insights" className="title-icon-svg" />
              Your Insights
            </h2>
          </div>
          <div className="insights-grid">
            {insights.map((insight, index) => (
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

  // Transform API schedule data to match expected format
  const personalScheduleData = scheduleData.map(shift => {
    const startDate = new Date(shift.start_time)
    const endDate = new Date(shift.end_time)
    const dayOfWeek = startDate.getDay()
    
    return {
      day: dayOfWeek,
      startHour: startDate.getHours(),
      endHour: endDate.getHours(),
      role: currentUser?.user_role || "Employee",
      date: shift.date,
    }
  })

  const calculateTotalHours = () => {
    return personalScheduleData.reduce((total, shift) => {
      return total + (shift.endHour - shift.startHour)
    }, 0)
  }

  const formatHour = (hour) => {
    if (hour === 0) return "12 AM"
    if (hour === 12) return "12 PM"
    if (hour < 12) return `${hour} AM`
    return `${hour - 12} PM`
  }

  const renderSchedule = () => {
    const headerGradient = `linear-gradient(135deg, ${primaryColor}, ${secondaryColor})`
    const cornerGradient = `linear-gradient(135deg, ${secondaryColor}, ${accentColor})`
    const totalHours = calculateTotalHours()

    return (
      <div className="premium-content fade-in">
        <div className="content-header">
          <div>
            <h1 className="page-title">My Schedule</h1>
            <p className="page-subtitle">Your weekly work schedule</p>
          </div>
          <div className="schedule-summary">
            <div className="summary-card">
              <span className="summary-label">Total Hours</span>
              <span className="summary-value">{totalHours}h</span>
            </div>
            <div className="summary-card">
              <span className="summary-label">Shifts</span>
              <span className="summary-value">
                {personalScheduleData.length}
              </span>
            </div>
          </div>
        </div>

        {scheduleLoading && (
          <div className="personal-schedule-alert">
            <div className="alert-icon">⏳</div>
            <div className="alert-content">
              Loading your schedule...
            </div>
          </div>
        )}

        {scheduleError && (
          <div className="personal-schedule-alert" style={{ borderColor: accentColor }}>
            <div className="alert-icon">⚠️</div>
            <div className="alert-content">
              <strong>Error:</strong> {scheduleError}
            </div>
          </div>
        )}

        {!scheduleLoading && !scheduleError && personalScheduleData.length === 0 && (
          <div className="personal-schedule-alert">
            <div className="alert-icon">ℹ️</div>
            <div className="alert-content">
              <strong>No Schedule:</strong> You don't have any shifts scheduled for the next 7 days.
            </div>
          </div>
        )}

        <div className="personal-schedule-view">
          <div className="schedule-grid">
            <div
              className="schedule-header-cell schedule-corner-cell"
              style={{
                background: cornerGradient,
                gridRow: 1,
                gridColumn: 1,
              }}
            >
              <div className="corner-label">Time / Day</div>
            </div>
            {daysShort.map((day, dayIndex) => (
              <div
                key={dayIndex}
                className="schedule-header-cell"
                style={{
                  background: headerGradient,
                  gridRow: 1,
                  gridColumn: dayIndex + 2,
                }}
              >
                <span className="day-name">{day}</span>
              </div>
            ))}

            {/* Hour Labels */}
            {Array.from({ length: 24 }).map((_, hour) => (
              <div
                key={`hour-${hour}`}
                className="schedule-hour-label"
                style={{
                  gridRow: hour + 2,
                  gridColumn: 1,
                }}
              >
                <span className="hour-time">{formatHour(hour)}</span>
              </div>
            ))}

            {/* Shift Blocks - spanning multiple hours */}
            {personalScheduleData.map((shift, idx) => {
              const dayIndex = daysShort.findIndex((d) => {
                const dayMap = {
                  Mon: 1,
                  Tue: 2,
                  Wed: 3,
                  Thu: 4,
                  Fri: 5,
                  Sat: 6,
                  Sun: 0,
                }
                return dayMap[d] === shift.day
              })

              return (
                <div
                  key={`shift-${idx}`}
                  className="shift-block"
                  style={{
                    gridRow: `${shift.startHour + 2} / ${shift.endHour + 2}`,
                    gridColumn: dayIndex + 2,
                    backgroundColor: primaryColor,
                    borderColor: primaryColor,
                  }}
                >
                  <div className="shift-info">
                    <div className="shift-role">{shift.role}</div>
                    <div className="shift-hours">
                      {formatHour(shift.startHour)} -{" "}
                      {formatHour(shift.endHour)}
                    </div>
                  </div>
                </div>
              )
            })}

            {/* Background cells for empty slots */}
            {Array.from({ length: 24 }).map((_, hour) =>
              daysShort.map((_, dayIndex) => {
                const dayMap = {
                  Mon: 1,
                  Tue: 2,
                  Wed: 3,
                  Thu: 4,
                  Fri: 5,
                  Sat: 6,
                  Sun: 0,
                }
                const actualDay = dayMap[daysShort[dayIndex]]
                const hasShift = personalScheduleData.some(
                  (s) =>
                    s.day === actualDay &&
                    hour >= s.startHour &&
                    hour < s.endHour,
                )
                return hasShift ? null : (
                  <div
                    key={`cell-${hour}-${dayIndex}`}
                    className="schedule-cell empty-cell"
                    style={{
                      gridRow: hour + 2,
                      gridColumn: dayIndex + 2,
                    }}
                  />
                )
              }),
            )}
          </div>
        </div>
      </div>
    )
  }

  const renderPreferences = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Work Preferences</h1>
          <p className="page-subtitle">
            Manage your availability and work preferences
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={handleSavePreferences}
          disabled={preferencesLoading}
        >
          {preferencesLoading ? "Saving..." : "Save Preferences"}
        </button>
      </div>

      {preferencesError && (
        <div
          className="alert alert-error"
          style={{ marginBottom: "var(--emp-space-4)" }}
        >
          {preferencesError}
        </div>
      )}

      {preferencesSuccess && (
        <div
          className="alert alert-success"
          style={{ marginBottom: "var(--emp-space-4)" }}
        >
          {preferencesSuccess}
        </div>
      )}

      <div className="section-wrapper">
        <div className="section-header">
          <h2 className="section-title">General Settings</h2>
        </div>
        <div className="preferences-grid">
          <div className="form-group">
            <label className="form-label">Roles You Can Perform</label>
            <div className="roles-checkboxes">
              {roles
                .filter(
                  (role) => role.role !== "admin" && role.role !== "manager",
                )
                .map((role) => (
                  <label key={role.role} className="checkbox-label">
                    <input
                      type="checkbox"
                      checked={userRoles.includes(role.role)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setUserRoles([...userRoles, role.role])
                        } else {
                          setUserRoles(userRoles.filter((r) => r !== role.role))
                        }
                      }}
                    />
                    <span>{role.role}</span>
                  </label>
                ))}
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Hours Per Week</label>
              <input
                type="number"
                className="form-input"
                value={maxHoursPerWeek}
                onChange={(e) => setMaxHoursPerWeek(parseInt(e.target.value))}
                min="0"
                max="168"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Preferred Hours Per Week</label>
              <input
                type="number"
                className="form-input"
                value={preferredHoursPerWeek}
                onChange={(e) =>
                  setPreferredHoursPerWeek(parseInt(e.target.value))
                }
                min="0"
                max="168"
              />
            </div>
          </div>

          <div className="form-row">
            <div className="form-group">
              <label className="form-label">Max Consecutive Slots</label>
              <input
                type="number"
                className="form-input"
                value={maxConsecSlots}
                onChange={(e) => setMaxConsecSlots(parseInt(e.target.value))}
                min="1"
                max="24"
              />
            </div>

            <div className="form-group">
              <label className="form-label">Available On-Call</label>
              <label className="checkbox-switch">
                <input
                  type="checkbox"
                  checked={onCall}
                  onChange={(e) => setOnCall(e.target.checked)}
                />
                <span className="checkbox-text">{onCall ? "Yes" : "No"}</span>
              </label>
            </div>
          </div>
        </div>
      </div>

      <div
        className="section-wrapper"
        style={{ marginTop: "var(--emp-space-6)" }}
      >
        <div className="section-header">
          <h2 className="section-title">Weekly Availability</h2>
          <div style={{ display: "flex", gap: "var(--emp-space-3)" }}>
            <button
              className="btn-apply-all"
              onClick={handleApplyToAllDays}
              disabled={!isAnyDayFullyFilled()}
              title={
                !isAnyDayFullyFilled()
                  ? "Fill out one complete day first"
                  : "Apply first complete day to all days"
              }
            >
              Apply to All Days
            </button>
            <button
              className="btn-primary"
              onClick={handleSaveWeeklyAvailability}
              disabled={!isAllDaysFilled()}
              title={
                !isAllDaysFilled()
                  ? "Complete all days first (4 time slots per day)"
                  : "Confirm weekly availability is complete"
              }
              style={{
                opacity: isAllDaysFilled() ? 1 : 0.5,
                cursor: isAllDaysFilled() ? "pointer" : "not-allowed",
              }}
            >
              {weeklyAvailabilitySaved
                ? "✓ Weekly Availability Saved"
                : "Save Weekly Availability"}
            </button>
          </div>
        </div>
        <div className="preferences-table">
          {days.map((day, index) => {
            const dayPref = preferences.find((p) => p.day === day)
            return (
              <div key={day} className="preference-row">
                <div className="preference-day">{daysShort[index]}</div>
                <div className="preference-fields">
                  <div className="time-group">
                    <label className="time-label">Preferred Start</label>
                    <input
                      type="time"
                      className="form-input"
                      value={dayPref?.preferred_start_time || ""}
                      onChange={(e) =>
                        handlePreferenceChange(
                          day,
                          "preferred_start_time",
                          e.target.value,
                        )
                      }
                    />
                  </div>
                  <div className="time-group">
                    <label className="time-label">Preferred End</label>
                    <input
                      type="time"
                      className="form-input"
                      value={dayPref?.preferred_end_time || ""}
                      onChange={(e) =>
                        handlePreferenceChange(
                          day,
                          "preferred_end_time",
                          e.target.value,
                        )
                      }
                    />
                  </div>
                  <div className="time-group">
                    <label className="time-label">Available Start</label>
                    <input
                      type="time"
                      className="form-input"
                      value={dayPref?.available_start_time || ""}
                      onChange={(e) =>
                        handlePreferenceChange(
                          day,
                          "available_start_time",
                          e.target.value,
                        )
                      }
                    />
                  </div>
                  <div className="time-group">
                    <label className="time-label">Available End</label>
                    <input
                      type="time"
                      className="form-input"
                      value={dayPref?.available_end_time || ""}
                      onChange={(e) =>
                        handlePreferenceChange(
                          day,
                          "available_end_time",
                          e.target.value,
                        )
                      }
                    />
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )

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
            <h1 className="page-title">My Requests</h1>
            <p className="page-subtitle">
              Submit and track your time-off and other requests
            </p>
          </div>
        </div>

        {/* Submit New Request Form */}
        <div className="section-wrapper">
          <div className="section-header">
            <h2 className="section-title">Submit New Request</h2>
          </div>

          <form onSubmit={handleSubmitRequest} className="request-form">
            {requestsError && (
              <div className="alert alert-error">{requestsError}</div>
            )}
            {requestsSuccess && (
              <div className="alert alert-success">{requestsSuccess}</div>
            )}

            <div className="form-group">
              <label className="form-label">Request Type</label>
              <select
                className="form-input"
                value={requestForm.type}
                onChange={(e) =>
                  setRequestForm({ ...requestForm, type: e.target.value })
                }
                required
              >
                <option value="calloff">Call Off (Sick/Emergency)</option>
                <option value="holiday">Holiday / Vacation</option>
                <option value="resign">Resignation</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Message / Reason</label>
              <textarea
                className="form-input"
                rows="4"
                placeholder="Please provide details about your request..."
                value={requestForm.message}
                onChange={(e) =>
                  setRequestForm({ ...requestForm, message: e.target.value })
                }
                required
                minLength={10}
              />
              <small className="form-hint">Minimum 10 characters</small>
            </div>

            <button
              type="submit"
              className="btn-primary"
              disabled={requestsLoading}
            >
              {requestsLoading ? "Submitting..." : "Submit Request"}
            </button>
          </form>
        </div>

        {/* My Requests List */}
        <div
          className="section-wrapper"
          style={{ marginTop: "var(--emp-space-6)" }}
        >
          <div className="section-header">
            <h2 className="section-title">My Submitted Requests</h2>
          </div>

          {requestsListLoading ? (
            <div
              className="empty-state"
              style={{ padding: "var(--emp-space-8)" }}
            >
              <p>Loading your requests...</p>
            </div>
          ) : requestsError ? (
            <div className="empty-state" style={{ color: "var(--emp-color-danger, #ef4444)" }}>
              <p>{requestsError}</p>
            </div>
          ) : requests.length === 0 ? (
            <div className="empty-state">
              <p>You haven't submitted any requests yet.</p>
            </div>
          ) : (
            <div className="requests-list">
              {requests.map((request) => (
                <div key={request.request_id} className="request-card">
                  <div className="request-header">
                    <div className="request-type">
                      {getRequestTypeLabel(request.type)}
                    </div>
                    <span className={getStatusBadgeClass(request.status === "in queue" ? "pending" : request.status)}>
                      {request.status === "in queue" ? "PENDING" : request.status?.toUpperCase() || "PENDING"}
                    </span>
                  </div>
                  <div className="request-body">
                    <p className="request-message">{request.message}</p>
                    {request.start_date && (
                      <div className="request-dates">
                        <strong>Dates:</strong>{" "}
                        {new Date(request.start_date).toLocaleDateString()}
                        {request.end_date &&
                          ` - ${new Date(request.end_date).toLocaleDateString()}`}
                      </div>
                    )}
                  </div>
                  <div className="request-footer">
                    <span className="request-date">
                      Submitted:{" "}
                      {new Date(request.submitted_at).toLocaleDateString()}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    )
  }

  const renderProfile = () => (
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
              {currentUser?.full_name || profileData?.full_name || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Email</div>
            <div className="info-value">
              {currentUser?.email || profileData?.email || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Role</div>
            <div className="info-value">
              {currentUser?.user_role || profileData?.user_role || "N/A"}
            </div>
          </div>
          <div className="info-item">
            <div className="info-label">Organization</div>
            <div className="info-value">
              {profileData?.organization || "N/A"}
            </div>
          </div>
          {(currentUser?.salary_per_hour || profileData?.salary_per_hour) && (
            <div className="info-item">
              <div className="info-label">Salary Per Hour</div>
              <div className="info-value">
                ${currentUser?.salary_per_hour || profileData?.salary_per_hour}
              </div>
            </div>
          )}
          <div className="info-item">
            <div className="info-label">Member Since</div>
            <div className="info-value">
              {profileData?.created_at
                ? new Date(profileData.created_at).toLocaleDateString()
                : "N/A"}
            </div>
          </div>
          {profileData?.hours_worked !== null &&
            profileData?.hours_worked !== undefined && (
              <div className="info-item">
                <div className="info-label">Total Hours Worked</div>
                <div className="info-value">{profileData.hours_worked} hrs</div>
              </div>
            )}
          {profileData?.hours_worked_this_week !== null &&
            profileData?.hours_worked_this_week !== undefined && (
              <div className="info-item">
                <div className="info-label">Hours This Week</div>
                <div className="info-value">
                  {profileData.hours_worked_this_week} hrs
                </div>
              </div>
            )}
          {(currentUser?.max_hours_per_week ||
            currentUser?.max_hours_per_week === 0) && (
            <div className="info-item">
              <div className="info-label">Max Hours Per Week</div>
              <div className="info-value">
                {currentUser.max_hours_per_week} hrs
              </div>
            </div>
          )}
          {(currentUser?.preferred_hours_per_week ||
            currentUser?.preferred_hours_per_week === 0) && (
            <div className="info-item">
              <div className="info-label">Preferred Hours Per Week</div>
              <div className="info-value">
                {currentUser.preferred_hours_per_week} hrs
              </div>
            </div>
          )}
        </div>
      </div>

      <div
        className="section-wrapper"
        style={{ marginTop: "var(--emp-space-6)" }}
      >
        <div className="section-header">
          <h2 className="section-title">Change Password</h2>
        </div>
        <form onSubmit={handleChangePassword} className="password-form">
          {passwordError && (
            <div className="alert alert-error">{passwordError}</div>
          )}
          {passwordSuccess && (
            <div className="alert alert-success">{passwordSuccess}</div>
          )}
          <div className="form-group">
            <label className="form-label">Current Password</label>
            <input
              type="password"
              className="form-input"
              value={passwordForm.old_password}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
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
              value={passwordForm.new_password}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
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
              value={passwordForm.confirm_password}
              onChange={(e) =>
                setPasswordForm({
                  ...passwordForm,
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
            disabled={passwordLoading}
          >
            {passwordLoading ? "Changing..." : "Change Password"}
          </button>
        </form>
      </div>
    </div>
  )

  return (
    <div
      className={`employee-dashboard-wrapper ${darkMode ? "dark-mode" : ""}`}
    >
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
                <span className="logo-badge">Employee</span>
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
            <div className="user-avatar">
              {(() => {
                const fullName =
                  currentUser?.full_name || profileData?.full_name || ""
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
            {!sidebarCollapsed && (
              <div className="user-info">
                <div className="user-name">
                  {currentUser?.full_name ||
                    profileData?.full_name ||
                    "Loading..."}
                </div>
                <div className="user-role">
                  {currentUser?.user_role ||
                    profileData?.user_role ||
                    "Employee"}
                </div>
              </div>
            )}
          </div>
          {!sidebarCollapsed && (
            <button className="logout-btn" onClick={handleLogout}>
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
            {activeTab === "schedule" && renderSchedule()}
            {activeTab === "requests" && renderRequests()}
            {activeTab === "preferences" && renderPreferences()}
            {activeTab === "profile" && renderProfile()}
          </>
        )}
      </main>

      {/* Mobile Bottom Navigation */}
      <nav className="mobile-nav">
        {navigationItems.map((item) => (
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

export default EmployeeDashboard
