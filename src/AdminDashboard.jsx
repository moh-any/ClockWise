import { useState, useEffect, useRef } from "react"
import "./AdminDashboard.css"
import api from "./services/api"

// Import SVG icons
import HomeIcon from "./Icons/Home_Icon.svg"
import ScheduleIcon from "./Icons/Schedule_Icon.svg"
import AnalyticsIcon from "./Icons/Analytics_Icon.svg"
import PlanningIcon from "./Icons/Planning_Icon.svg"
import SettingsIcon from "./Icons/Settings_Icon.svg"
import InfoIcon from "./Icons/Info_Icon.svg"
import ChartUpIcon from "./Icons/Chart-Up-Icon.svg"
import ChartDownIcon from "./Icons/Chart-down-Icon.svg"
import TargetHitIcon from "./Icons/Target-Hit-Icon.svg"
import MissedTargetIcon from "./Icons/Missed-Target-Icon.svg"
import LocationIcon from "./Icons/location-Icon.svg"
import CloudUploadIcon from "./Icons/Cloud-Upload-Icon.svg"
import ConfigurationIcon from "./Icons/Configuration-Icon.svg"
import EmployeeIcon from "./Icons/Employee-Icon.svg"

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("home")
  const [requiredInfoSubTab, setRequiredInfoSubTab] = useState("location")
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [primaryColor, setPrimaryColor] = useState("#4A90E2")
  const [secondaryColor, setSecondaryColor] = useState("#7B68EE")
  const [accentColor, setAccentColor] = useState("#FF6B6B")

  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  const [staffingSummary, setStaffingSummary] = useState(null)
  const [totalHeadcount, setTotalHeadcount] = useState(0)
  const [laborCost, setLaborCost] = useState(0)
  const [revenue, setRevenue] = useState(0)
  const [currentlyClocked, setCurrentlyClocked] = useState(0)
  const [expectedClocked, setExpectedClocked] = useState(0)
  const [selectedCoords, setSelectedCoords] = useState({ lat: null, lng: null })
  const mapInstance = useRef(null)
  const configFileInput = useRef(null)
  const rosterFileInput = useRef(null)

  const [aiAlerts, setAiAlerts] = useState([
    {
      id: 1,
      priority: "high",
      message: "High demand predicted for Friday; 4 additional hires suggested",
      timestamp: "2 hours ago",
      dismissed: false,
    },
    {
      id: 2,
      priority: "medium",
      message: "Monday morning shift is understaffed by 15%",
      timestamp: "5 hours ago",
      dismissed: false,
    },
    {
      id: 3,
      priority: "low",
      message: "Labor costs trending 3% below budget this week",
      timestamp: "1 day ago",
      dismissed: false,
    },
  ])

  const [heatMapData, setHeatMapData] = useState(() => {
    const data = []
    for (let hour = 0; hour < 24; hour++) {
      const row = []
      for (let day = 0; day < 7; day++) {
        let value = 0
        if (hour >= 8 && hour <= 18) {
          value = 40 + Math.random() * 60
        } else if ((hour >= 6 && hour < 8) || (hour > 18 && hour <= 22)) {
          value = 20 + Math.random() * 40
        } else {
          value = Math.random() * 20
        }
        row.push(Math.round(value))
      }
      data.push(row)
    }
    return data
  })

  const days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

  const navigationItems = [
    { id: "home", label: "Dashboard", icon: HomeIcon },
    { id: "schedule", label: "Schedule", icon: ScheduleIcon },
    { id: "analytics", label: "Analytics", icon: AnalyticsIcon },
    { id: "planning", label: "Planning", icon: PlanningIcon },
    { id: "settings", label: "Settings", icon: SettingsIcon },
    { id: "requiredinfo", label: "Setup", icon: InfoIcon },
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

      const root = document.documentElement
      root.style.setProperty("--color-primary", primary)
      root.style.setProperty("--color-secondary", secondary)
      root.style.setProperty("--color-accent", accent)
      root.style.setProperty("--primary-contrast", getContrastColor(primary))
      root.style.setProperty(
        "--secondary-contrast",
        getContrastColor(secondary),
      )
      root.style.setProperty("--accent-contrast", getContrastColor(accent))
    }

    fetchStaffingData()

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

  const fetchStaffingData = async () => {
    try {
      setLoading(true)
      setError("")

      const summary = await api.staffing.getStaffingSummary()
      setStaffingSummary(summary)

      if (summary) {
        setTotalHeadcount(summary.total_headcount || 0)
        setLaborCost(summary.labor_cost || 0)
        setRevenue(summary.revenue || 0)
        setCurrentlyClocked(summary.currently_clocked || 0)
        setExpectedClocked(summary.expected_clocked || 0)
      }
    } catch (err) {
      console.error("Error fetching staffing data:", err)
      setError(err.message || "Failed to load dashboard data")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (activeTab === "requiredinfo" && requiredInfoSubTab === "location") {
      const timer = setTimeout(() => {
        initializeMap()
      }, 100)
      return () => {
        clearTimeout(timer)
        if (mapInstance.current) {
          mapInstance.current.remove()
          mapInstance.current = null
        }
      }
    } else {
      if (mapInstance.current) {
        mapInstance.current.remove()
        mapInstance.current = null
      }
    }
  }, [activeTab, requiredInfoSubTab])

  const initializeMap = () => {
    if (typeof window.mapboxgl === "undefined") {
      console.log("Mapbox GL not loaded yet")
      return
    }

    const mapContainer = document.getElementById("location-map")
    if (!mapContainer) return

    if (mapInstance.current) {
      mapInstance.current.remove()
      mapInstance.current = null
    }

    window.mapboxgl.accessToken =
      "pk.eyJ1IjoibW9zdGFmYTE5MjYiLCJhIjoiY21sOW1xZWNiMDRobTNlczczNDc0cGM0aCJ9.z2un235WCxTP0RswBTewPg"

    const map = new window.mapboxgl.Map({
      container: "location-map",
      style: "mapbox://styles/mapbox/satellite-streets-v12",
      projection: "globe",
      zoom: 2,
      center: [0, 0],
      attributionControl: true,
    })

    map.on("click", (e) => {
      const lat = e.lngLat.lat.toFixed(6)
      const lng = e.lngLat.lng.toFixed(6)
      setSelectedCoords({ lat, lng })
    })

    mapInstance.current = map
  }

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

  const renderAnalytics = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Analytics & Reports</h1>
          <p className="page-subtitle">Data-driven workforce insights</p>
        </div>
        <button className="btn-primary">Generate Report</button>
      </div>

      <div className="analytics-grid">
        <div className="chart-card">
          <h3 className="chart-title">Labor Cost Trends</h3>
          <div className="chart-placeholder">
            <svg
              className="chart-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z"
              />
            </svg>
            <p>Chart visualization</p>
          </div>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">Attendance Patterns</h3>
          <div className="chart-placeholder">
            <svg
              className="chart-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M16 8v8m-4-5v5m-4-2v2m-2 4h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
              />
            </svg>
            <p>Chart visualization</p>
          </div>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">Department Performance</h3>
          <div className="chart-placeholder">
            <svg
              className="chart-icon"
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
            <p>Chart visualization</p>
          </div>
        </div>
        <div className="chart-card">
          <h3 className="chart-title">Revenue vs Labor Cost</h3>
          <div className="chart-placeholder">
            <svg
              className="chart-icon"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"
              />
            </svg>
            <p>Chart visualization</p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderPlanning = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Workforce Planning</h1>
          <p className="page-subtitle">Strategic insights for growth</p>
        </div>
        <button className="btn-primary">Create Campaign</button>
      </div>

      <div className="planning-metrics">
        <div className="metric-card metric-success">
          <img src={ChartUpIcon} alt="Hires" className="metric-icon-svg" />
          <div className="metric-content">
            <h4>Recent Hires</h4>
            <div className="metric-value">24</div>
            <p className="metric-label">Last 30 days</p>
          </div>
        </div>
        <div className="metric-card metric-warning">
          <img
            src={ChartDownIcon}
            alt="Attrition"
            className="metric-icon-svg"
          />
          <div className="metric-content">
            <h4>Attrition Rate</h4>
            <div className="metric-value">5.2%</div>
            <p className="metric-label">Below industry avg</p>
          </div>
        </div>
        <div className="metric-card metric-info">
          <img src={TargetHitIcon} alt="Goal" className="metric-icon-svg" />
          <div className="metric-content">
            <h4>Hiring Goal</h4>
            <div className="metric-value">85%</div>
            <p className="metric-label">On track</p>
          </div>
        </div>
      </div>

      <div className="section-wrapper">
        <h2 className="section-title">AI-Powered Campaign Suggestions</h2>
        <div className="campaigns-list">
          <div className="campaign-card">
            <div className="campaign-priority priority-high">High Priority</div>
            <h3 className="campaign-title">Black Friday Hiring Blitz</h3>
            <p className="campaign-description">
              Projected 40% demand increase. Recommend hiring 15 additional
              staff by Nov 1st.
            </p>
            <div className="campaign-footer">
              <button className="btn-primary btn-sm">Launch Campaign</button>
              <button className="btn-link">View Forecast</button>
            </div>
          </div>
          <div className="campaign-card">
            <div className="campaign-priority priority-medium">
              Medium Priority
            </div>
            <h3 className="campaign-title">Q2 Expansion Prep</h3>
            <p className="campaign-description">
              New location opening requires 8-10 trained staff. Start
              recruitment Q1.
            </p>
            <div className="campaign-footer">
              <button className="btn-primary btn-sm">Launch Campaign</button>
              <button className="btn-link">View Details</button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )

  const renderOrgSettings = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Organization Settings</h1>
          <p className="page-subtitle">Configure system parameters</p>
        </div>
      </div>

      <div className="settings-section">
        <h2 className="section-title">Hourly Rates</h2>
        <div className="settings-grid">
          <div className="setting-item">
            <label className="setting-label">Base Rate</label>
            <input
              type="number"
              className="setting-input"
              placeholder="$15.00"
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Overtime Rate</label>
            <input
              type="number"
              className="setting-input"
              placeholder="$22.50"
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Weekend Premium</label>
            <input
              type="number"
              className="setting-input"
              placeholder="$18.00"
            />
          </div>
          <div className="setting-item">
            <label className="setting-label">Holiday Rate</label>
            <input
              type="number"
              className="setting-input"
              placeholder="$30.00"
            />
          </div>
        </div>
      </div>

      <div className="settings-section">
        <h2 className="section-title">Shift Rules</h2>
        <div className="settings-grid">
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
      </div>

      <div className="settings-section">
        <h2 className="section-title">System Logic</h2>
        <div className="settings-toggles">
          <div className="toggle-item">
            <div className="toggle-content">
              <h4 className="toggle-title">Auto-Approve Shifts</h4>
              <p className="toggle-description">
                Automatically approve all shift requests
              </p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="toggle-item">
            <div className="toggle-content">
              <h4 className="toggle-title">Overtime Alerts</h4>
              <p className="toggle-description">
                Notify managers when overtime is approaching
              </p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
          <div className="toggle-item">
            <div className="toggle-content">
              <h4 className="toggle-title">AI Recommendations</h4>
              <p className="toggle-description">
                Enable intelligent scheduling suggestions
              </p>
            </div>
            <label className="toggle-switch">
              <input type="checkbox" defaultChecked />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>
      </div>

      <div className="settings-footer">
        <button className="btn-secondary">Reset to Defaults</button>
        <button className="btn-primary">Save All Changes</button>
      </div>
    </div>
  )

  const renderRequiredInfo = () => (
    <div className="premium-content fade-in">
      <div className="content-header">
        <div>
          <h1 className="page-title">Setup & Configuration</h1>
          <p className="page-subtitle">
            Required information for system initialization
          </p>
        </div>
      </div>

      <div className="tabs-wrapper">
        <div className="tabs-nav">
          <button
            className={`tab-button ${requiredInfoSubTab === "location" ? "active" : ""}`}
            onClick={() => setRequiredInfoSubTab("location")}
          >
            <img src={LocationIcon} alt="Location" className="tab-icon-svg" />
            Location
          </button>
          <button
            className={`tab-button ${requiredInfoSubTab === "dataupload" ? "active" : ""}`}
            onClick={() => setRequiredInfoSubTab("dataupload")}
          >
            <img src={CloudUploadIcon} alt="Upload" className="tab-icon-svg" />
            Data Upload
          </button>
        </div>
      </div>

      {requiredInfoSubTab === "location" && (
        <div className="section-wrapper">
          <h2 className="section-title">Select Organization Location</h2>
          <p className="section-description">
            Click anywhere on the map to set your primary business location
          </p>

          {selectedCoords.lat && selectedCoords.lng && (
            <div className="coords-display">
              <div className="coords-item">
                <span className="coords-label">Latitude:</span>
                <span className="coords-value">{selectedCoords.lat}</span>
              </div>
              <div className="coords-item">
                <span className="coords-label">Longitude:</span>
                <span className="coords-value">{selectedCoords.lng}</span>
              </div>
              <button className="btn-primary btn-sm">Confirm Location</button>
            </div>
          )}

          <div id="location-map" className="map-container"></div>

          {!selectedCoords.lat && (
            <div className="map-hint">
              <p>👆 Click on the map to select your location</p>
            </div>
          )}
        </div>
      )}

      {requiredInfoSubTab === "dataupload" && (
        <div className="section-wrapper">
          <h2 className="section-title">Data Import</h2>
          <p className="section-description">
            Upload your configuration files to initialize the system
          </p>

          <div className="upload-grid">
            <div className="upload-card">
              <input
                type="file"
                ref={configFileInput}
                onChange={handleConfigUpload}
                style={{ display: "none" }}
                accept=".csv,.xlsx,.json"
              />
              <img
                src={ConfigurationIcon}
                alt="Configuration"
                className="upload-icon-svg"
              />
              <h3 className="upload-title">Configuration File</h3>
              <p className="upload-description">
                Upload your organization structure, departments, and roles
              </p>
              <ul className="upload-specs">
                <li>Supported formats: CSV, XLSX, JSON</li>
                <li>Maximum size: 10MB</li>
                <li>Must include: department_id, role_name, base_rate</li>
              </ul>
              <button
                className="btn-primary"
                onClick={() => configFileInput.current?.click()}
              >
                Choose File
              </button>
            </div>

            <div className="upload-card">
              <input
                type="file"
                ref={rosterFileInput}
                onChange={handleRosterUpload}
                style={{ display: "none" }}
                accept=".csv,.xlsx,.json"
              />
              <img
                src={EmployeeIcon}
                alt="Employees"
                className="upload-icon-svg"
              />
              <h3 className="upload-title">Employee Roster</h3>
              <p className="upload-description">
                Import your complete employee list with contact details
              </p>
              <ul className="upload-specs">
                <li>Supported formats: CSV, XLSX, JSON</li>
                <li>Maximum size: 25MB</li>
                <li>Must include: employee_id, name, email, role</li>
              </ul>
              <button
                className="btn-primary"
                onClick={() => rosterFileInput.current?.click()}
              >
                Choose File
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )

  return (
    <div className="dashboard-wrapper">
      {/* Premium Sidebar */}
      <aside className={`sidebar ${sidebarCollapsed ? "collapsed" : ""}`}>
        <div className="sidebar-header">
          <div className="logo-wrapper">
            <h1 className="logo">ClockWise</h1>
            {!sidebarCollapsed && <span className="logo-badge">Admin</span>}
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
          <div className="user-profile">
            <div className="user-avatar">AD</div>
            {!sidebarCollapsed && (
              <div className="user-info">
                <div className="user-name">Admin</div>
                <div className="user-role">System Admin</div>
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
            <button className="btn-primary" onClick={fetchStaffingData}>
              Retry
            </button>
          </div>
        )}
        {!loading && (
          <>
            {activeTab === "home" && renderHomeDashboard()}
            {activeTab === "schedule" && renderMasterSchedule()}
            {activeTab === "analytics" && renderAnalytics()}
            {activeTab === "planning" && renderPlanning()}
            {activeTab === "settings" && renderOrgSettings()}
            {activeTab === "requiredinfo" && renderRequiredInfo()}
          </>
        )}
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
