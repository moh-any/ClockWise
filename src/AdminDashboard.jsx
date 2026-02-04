import { useState, useEffect } from "react"
import "./AdminDashboard.css"
import api from "./services/api"

function AdminDashboard() {
  const [activeTab, setActiveTab] = useState("home")
  const [primaryColor, setPrimaryColor] = useState("#4A90E2")
  const [secondaryColor, setSecondaryColor] = useState("#7B68EE")
  const [accentColor, setAccentColor] = useState("#FF6B6B")

  // Loading and error states
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  // Data from API
  const [staffingSummary, setStaffingSummary] = useState(null)
  const [totalHeadcount, setTotalHeadcount] = useState(0)
  const [laborCost, setLaborCost] = useState(0)
  const [revenue, setRevenue] = useState(0)
  const [currentlyClocked, setCurrentlyClocked] = useState(0)
  const [expectedClocked, setExpectedClocked] = useState(0)

  const [aiAlerts, setAiAlerts] = useState([
    {
      id: 1,
      priority: "high",
      message: "High demand predicted for Friday; 4 additional hires suggested",
      timestamp: "2 hours ago",
    },
    {
      id: 2,
      priority: "medium",
      message: "Monday morning shift is understaffed by 15%",
      timestamp: "5 hours ago",
    },
    {
      id: 3,
      priority: "low",
      message: "Labor costs trending 3% below budget this week",
      timestamp: "1 day ago",
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

  const getContrastColor = (hexColor) => {
    const hex = hexColor.replace("#", "")
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)
    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255
    return luminance > 0.5 ? "#000000" : "#FFFFFF"
  }

  const getHeatColor = (intensity) => {
    const hex = secondaryColor.replace("#", "")
    const r = parseInt(hex.substr(0, 2), 16)
    const g = parseInt(hex.substr(2, 2), 16)
    const b = parseInt(hex.substr(4, 2), 16)

    const accentHex = accentColor.replace("#", "")
    const accentR = parseInt(accentHex.substr(0, 2), 16)
    const accentG = parseInt(accentHex.substr(2, 2), 16)
    const accentB = parseInt(accentHex.substr(4, 2), 16)

    const luminance = (0.299 * r + 0.587 * g + 0.114 * b) / 255

    const factor = intensity / 100

    if (luminance > 0.6) {
      const newR = Math.round(255 - (255 - r) * factor)
      const newG = Math.round(255 - (255 - g) * factor)
      const newB = Math.round(255 - (255 - b) * factor)

      if (intensity > 80) {
        const accentMix = ((intensity - 80) / 20) * 0.15
        return `rgb(${Math.round(newR * (1 - accentMix) + accentR * accentMix)}, ${Math.round(newG * (1 - accentMix) + accentG * accentMix)}, ${Math.round(newB * (1 - accentMix) + accentB * accentMix)})`
      }

      return `rgb(${newR}, ${newG}, ${newB})`
    } else {
      const baseR = Math.round(r + (255 - r) * 0.85)
      const baseG = Math.round(g + (255 - g) * 0.85)
      const baseB = Math.round(b + (255 - b) * 0.85)

      const newR = Math.round(baseR - (baseR - r) * factor)
      const newG = Math.round(baseG - (baseG - g) * factor)
      const newB = Math.round(baseB - (baseB - b) * factor)

      if (intensity > 80) {
        const accentMix = ((intensity - 80) / 20) * 0.15
        return `rgb(${Math.round(newR * (1 - accentMix) + accentR * accentMix)}, ${Math.round(newG * (1 - accentMix) + accentG * accentMix)}, ${Math.round(newB * (1 - accentMix) + accentB * accentMix)})`
      }

      return `rgb(${newR}, ${newG}, ${newB})`
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

      const wrapper = document.querySelector(".admin-dashboard-wrapper")
      if (wrapper) {
        wrapper.style.setProperty("--primary-color", primary)
        wrapper.style.setProperty("--secondary-color", secondary)
        wrapper.style.setProperty("--accent-color", accent)
        wrapper.style.setProperty(
          "--primary-contrast",
          getContrastColor(primary),
        )
        wrapper.style.setProperty(
          "--secondary-contrast",
          getContrastColor(secondary),
        )
        wrapper.style.setProperty("--accent-contrast", getContrastColor(accent))
      }
    }

    // Fetch staffing summary data
    fetchStaffingData()
  }, [])

  const fetchStaffingData = async () => {
    try {
      setLoading(true)
      setError("")
      
      const summary = await api.staffing.getStaffingSummary()
      setStaffingSummary(summary)
      
      // Update KPI values from API response
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
      // Keep default values if API fails
    } finally {
      setLoading(false)
    }
  }

  const renderHomeDashboard = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">Organization Pulse</h1>

      {/* KPI Cards */}
      <div className="admin-kpi-grid">
        <div
          className="admin-kpi-card"
          style={{ borderLeftColor: primaryColor }}
        >
          <div className="admin-kpi-header">
            <span className="admin-kpi-label">Total Headcount</span>
            <span className="admin-kpi-icon">ICON</span>
          </div>
          <div className="admin-kpi-value">{totalHeadcount}</div>
          <div className="admin-kpi-subtitle">Active Employees</div>
        </div>

        <div
          className="admin-kpi-card"
          style={{ borderLeftColor: secondaryColor }}
        >
          <div className="admin-kpi-header">
            <span className="admin-kpi-label">Labor Cost vs Revenue</span>
            <span className="admin-kpi-icon">ICON</span>
          </div>
          <div className="admin-kpi-value">
            ${(laborCost / 1000).toFixed(1)}k / ${(revenue / 1000).toFixed(0)}k
          </div>
          <div className="admin-kpi-subtitle">
            {((laborCost / revenue) * 100).toFixed(1)}% Labor Cost Ratio
          </div>
        </div>

        <div
          className="admin-kpi-card"
          style={{ borderLeftColor: accentColor }}
        >
          <div className="admin-kpi-header">
            <span className="admin-kpi-label">Current Live Status</span>
            <span className="admin-kpi-icon">ICON</span>
          </div>
          <div className="admin-kpi-value">
            {currentlyClocked} / {expectedClocked}
          </div>
          <div className="admin-kpi-subtitle">
            {((currentlyClocked / expectedClocked) * 100).toFixed(0)}% Clocked
            In
          </div>
        </div>
      </div>

      {/* AI Alerts */}
      <div className="admin-section">
        <h2 className="admin-section-title">Urgent Insights</h2>
        <div className="admin-alerts-container">
          {aiAlerts.map((alert) => (
            <div
              key={alert.id}
              className={`admin-alert admin-alert-${alert.priority}`}
              style={{
                borderLeftColor:
                  alert.priority === "high"
                    ? accentColor
                    : alert.priority === "medium"
                      ? secondaryColor
                      : primaryColor,
              }}
            >
              <div className="admin-alert-header">
                <span className="admin-alert-priority">
                  {alert.priority.toUpperCase()}
                </span>
                <span className="admin-alert-time">{alert.timestamp}</span>
              </div>
              <div className="admin-alert-message">{alert.message}</div>
            </div>
          ))}
        </div>
      </div>

      {/* Demand Heat Map */}
      <div className="admin-section">
        <h2 className="admin-section-title">Weekly Demand Heat Map</h2>
        <p className="admin-section-description">
          Peak hours analysis across the organization - darker cells indicate
          higher demand
        </p>
        <div className="admin-heatmap-container">
          <div className="admin-heatmap-wrapper">
            <div className="admin-heatmap-row admin-heatmap-header">
              <div className="admin-heatmap-cell admin-heatmap-corner">
                Hour
              </div>
              {days.map((day) => (
                <div
                  key={day}
                  className="admin-heatmap-cell admin-heatmap-day-header"
                >
                  {day}
                </div>
              ))}
            </div>
            {heatMapData.map((row, hourIndex) => (
              <div key={hourIndex} className="admin-heatmap-row">
                <div className="admin-heatmap-cell admin-heatmap-hour-label">
                  {String(hourIndex).padStart(2, "0")}:00
                </div>
                {row.map((intensity, dayIndex) => (
                  <div
                    key={dayIndex}
                    className="admin-heatmap-cell admin-heatmap-data-cell"
                    style={{
                      backgroundColor: getHeatColor(intensity),
                      color: getContrastColor(getHeatColor(intensity)),
                    }}
                    title={`${days[dayIndex]} ${String(hourIndex).padStart(2, "0")}:00 - ${intensity}% capacity`}
                  >
                    {intensity}%
                  </div>
                ))}
              </div>
            ))}
          </div>
          <div className="admin-heatmap-legend">
            <span className="admin-legend-label">Low Demand</span>
            <div
              className="admin-legend-gradient"
              style={{
                background: `linear-gradient(to right, ${getHeatColor(0)}, ${getHeatColor(100)})`,
              }}
            ></div>
            <span className="admin-legend-label">High Demand</span>
          </div>
        </div>
      </div>
    </div>
  )

  const renderMasterSchedule = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">Master Schedule</h1>
      <div className="admin-filters-bar">
        <select
          className="admin-filter-select"
          style={{ borderColor: primaryColor }}
        >
          <option>All Departments</option>
          <option>Sales</option>
          <option>Operations</option>
          <option>Customer Service</option>
          <option>IT</option>
        </select>
        <select
          className="admin-filter-select"
          style={{ borderColor: primaryColor }}
        >
          <option>All Segments</option>
          <option>Morning Shift</option>
          <option>Evening Shift</option>
          <option>Night Shift</option>
        </select>
        <button
          className="admin-btn-primary"
          style={{
            backgroundColor: primaryColor,
            color: getContrastColor(primaryColor),
          }}
        >
          Export Schedule
        </button>
      </div>
      <div className="admin-placeholder-content">
        <div className="admin-placeholder-icon">CALENDAR</div>
        <p>Full organization calendar view will be displayed here</p>
        <p className="admin-placeholder-subtitle">
          Filterable by departments and segments
        </p>
      </div>
    </div>
  )

  const renderAnalytics = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">Analytics & Reports</h1>
      <div className="admin-analytics-grid">
        <div className="admin-analytics-card">
          <h3>Labor Cost Trends</h3>
          <div className="admin-placeholder-chart">CHART_ICON</div>
        </div>
        <div className="admin-analytics-card">
          <h3>Attendance Patterns</h3>
          <div className="admin-placeholder-chart">CHART_ICON</div>
        </div>
        <div className="admin-analytics-card">
          <h3>Department Performance</h3>
          <div className="admin-placeholder-chart">CHART_ICON</div>
        </div>
        <div className="admin-analytics-card">
          <h3>Revenue vs Labor Cost</h3>
          <div className="admin-placeholder-chart">CHART_ICON</div>
        </div>
      </div>
    </div>
  )

  const renderPlanning = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">Workforce Planning</h1>

      <div className="admin-planning-section">
        <h2 className="admin-section-title">Long-term Trends</h2>
        <div className="admin-planning-card">
          <div className="admin-placeholder-chart">TREND_CHART</div>
        </div>
      </div>

      <div className="admin-planning-section">
        <h2 className="admin-section-title">Hiring & Layoff Data</h2>
        <div className="admin-planning-grid">
          <div className="admin-planning-metric">
            <span className="admin-metric-label">Planned Hires (Q1)</span>
            <span
              className="admin-metric-value"
              style={{ color: primaryColor }}
            >
              12
            </span>
          </div>
          <div className="admin-planning-metric">
            <span className="admin-metric-label">Open Positions</span>
            <span
              className="admin-metric-value"
              style={{ color: secondaryColor }}
            >
              7
            </span>
          </div>
          <div className="admin-planning-metric">
            <span className="admin-metric-label">Turnover Rate</span>
            <span className="admin-metric-value" style={{ color: accentColor }}>
              8.5%
            </span>
          </div>
        </div>
      </div>

      <div className="admin-planning-section">
        <h2 className="admin-section-title">Campaign Suggestions</h2>
        <div className="admin-campaigns-list">
          <div
            className="admin-campaign-item"
            style={{ borderLeftColor: primaryColor }}
          >
            <h4>Summer Staffing Drive</h4>
            <p>Increase headcount by 15% for seasonal demand spike</p>
          </div>
          <div
            className="admin-campaign-item"
            style={{ borderLeftColor: secondaryColor }}
          >
            <h4>Training Initiative</h4>
            <p>Upskill 30 employees for cross-functional coverage</p>
          </div>
        </div>
      </div>
    </div>
  )

  const renderOrgSettings = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">
        Organization Settings - Control Tower
      </h1>

      <div className="admin-settings-section">
        <h2 className="admin-section-title">Hourly Rates</h2>
        <div className="admin-settings-grid">
          <div className="admin-setting-item">
            <label className="admin-setting-label">Base Hourly Rate</label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="15.00"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">Overtime Multiplier</label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="1.5"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">Weekend Rate</label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="18.00"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">Holiday Rate</label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="22.50"
              style={{ borderColor: primaryColor }}
            />
          </div>
        </div>
      </div>

      <div className="admin-settings-section">
        <h2 className="admin-section-title">Shift Rules</h2>
        <div className="admin-settings-grid">
          <div className="admin-setting-item">
            <label className="admin-setting-label">
              Minimum Shift Duration (hours)
            </label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="4"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">
              Maximum Shift Duration (hours)
            </label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="12"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">
              Break Duration (minutes)
            </label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="30"
              style={{ borderColor: primaryColor }}
            />
          </div>
          <div className="admin-setting-item">
            <label className="admin-setting-label">Max Weekly Hours</label>
            <input
              type="number"
              className="admin-setting-input"
              placeholder="40"
              style={{ borderColor: primaryColor }}
            />
          </div>
        </div>
      </div>

      <div className="admin-settings-section">
        <h2 className="admin-section-title">System Logic</h2>
        <div className="admin-settings-list">
          <div className="admin-setting-toggle">
            <span className="admin-toggle-label">
              Enable AI Recommendations
            </span>
            <label className="admin-toggle-switch">
              <input type="checkbox" defaultChecked />
              <span
                className="admin-toggle-slider"
                style={{ backgroundColor: primaryColor }}
              ></span>
            </label>
          </div>
          <div className="admin-setting-toggle">
            <span className="admin-toggle-label">
              Auto-approve Time-off Requests
            </span>
            <label className="admin-toggle-switch">
              <input type="checkbox" />
              <span className="admin-toggle-slider"></span>
            </label>
          </div>
          <div className="admin-setting-toggle">
            <span className="admin-toggle-label">
              Send Weekly Analytics Reports
            </span>
            <label className="admin-toggle-switch">
              <input type="checkbox" defaultChecked />
              <span
                className="admin-toggle-slider"
                style={{ backgroundColor: primaryColor }}
              ></span>
            </label>
          </div>
        </div>
      </div>

      <button
        className="admin-btn-primary admin-btn-save"
        style={{
          backgroundColor: primaryColor,
          color: getContrastColor(primaryColor),
        }}
      >
        Save All Settings
      </button>
    </div>
  )

  const renderProfile = () => (
    <div className="admin-dashboard-content">
      <h1 className="admin-page-title">Admin Profile</h1>

      <div className="admin-profile-container">
        <div className="admin-profile-header">
          <div
            className="admin-profile-avatar"
            style={{
              backgroundColor: primaryColor,
              color: getContrastColor(primaryColor),
            }}
          >
            AVATAR
          </div>
          <div className="admin-profile-info">
            <h2 className="admin-profile-name">Administrator</h2>
            <p className="admin-profile-role">System Administrator</p>
          </div>
        </div>

        <div className="admin-profile-section">
          <h3 className="admin-profile-section-title">Personal Information</h3>
          <div className="admin-settings-grid">
            <div className="admin-setting-item">
              <label className="admin-setting-label">Full Name</label>
              <input
                type="text"
                className="admin-setting-input"
                placeholder="John Doe"
                style={{ borderColor: primaryColor }}
              />
            </div>
            <div className="admin-setting-item">
              <label className="admin-setting-label">Email</label>
              <input
                type="email"
                className="admin-setting-input"
                placeholder="admin@organization.com"
                style={{ borderColor: primaryColor }}
              />
            </div>
            <div className="admin-setting-item">
              <label className="admin-setting-label">Phone</label>
              <input
                type="tel"
                className="admin-setting-input"
                placeholder="+1 (555) 123-4567"
                style={{ borderColor: primaryColor }}
              />
            </div>
            <div className="admin-setting-item">
              <label className="admin-setting-label">Department</label>
              <input
                type="text"
                className="admin-setting-input"
                placeholder="Administration"
                style={{ borderColor: primaryColor }}
              />
            </div>
          </div>
        </div>

        <div className="admin-profile-section">
          <h3 className="admin-profile-section-title">Security</h3>
          <div className="admin-settings-grid">
            <div className="admin-setting-item">
              <label className="admin-setting-label">Current Password</label>
              <input
                type="password"
                className="admin-setting-input"
                placeholder="••••••••"
                style={{ borderColor: primaryColor }}
              />
            </div>
            <div className="admin-setting-item">
              <label className="admin-setting-label">New Password</label>
              <input
                type="password"
                className="admin-setting-input"
                placeholder="••••••••"
                style={{ borderColor: primaryColor }}
              />
            </div>
            <div className="admin-setting-item">
              <label className="admin-setting-label">
                Confirm New Password
              </label>
              <input
                type="password"
                className="admin-setting-input"
                placeholder="••••••••"
                style={{ borderColor: primaryColor }}
              />
            </div>
          </div>
        </div>

        <div className="admin-profile-section">
          <h3 className="admin-profile-section-title">Organization Theme</h3>
          <div className="admin-color-preview-grid">
            <div className="admin-color-preview-item">
              <div
                className="admin-color-preview-box"
                style={{ backgroundColor: primaryColor }}
              ></div>
              <span className="admin-color-preview-label">Primary</span>
              <span className="admin-color-preview-value">{primaryColor}</span>
            </div>
            <div className="admin-color-preview-item">
              <div
                className="admin-color-preview-box"
                style={{ backgroundColor: secondaryColor }}
              ></div>
              <span className="admin-color-preview-label">Secondary</span>
              <span className="admin-color-preview-value">
                {secondaryColor}
              </span>
            </div>
            <div className="admin-color-preview-item">
              <div
                className="admin-color-preview-box"
                style={{ backgroundColor: accentColor }}
              ></div>
              <span className="admin-color-preview-label">Accent</span>
              <span className="admin-color-preview-value">{accentColor}</span>
            </div>
          </div>
        </div>

        <button
          className="admin-btn-primary admin-btn-save"
          style={{
            backgroundColor: primaryColor,
            color: getContrastColor(primaryColor),
          }}
        >
          Update Profile
        </button>
      </div>
    </div>
  )

  return (
    <div className="admin-dashboard-wrapper">
      {/* Sidebar Navigation */}
      <aside className="admin-sidebar">
        <div className="admin-logo-section">
          <h1 className="admin-logo">ClockWise</h1>
          <p className="admin-logo-subtitle">Admin Dashboard</p>
        </div>

        <nav className="admin-nav">
          <button
            className={`admin-nav-item ${activeTab === "home" ? "active" : ""}`}
            onClick={() => setActiveTab("home")}
            style={
              activeTab === "home"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Home
          </button>

          <button
            className={`admin-nav-item ${activeTab === "schedule" ? "active" : ""}`}
            onClick={() => setActiveTab("schedule")}
            style={
              activeTab === "schedule"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Master Schedule
          </button>

          <button
            className={`admin-nav-item ${activeTab === "analytics" ? "active" : ""}`}
            onClick={() => setActiveTab("analytics")}
            style={
              activeTab === "analytics"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Analytics
          </button>

          <button
            className={`admin-nav-item ${activeTab === "planning" ? "active" : ""}`}
            onClick={() => setActiveTab("planning")}
            style={
              activeTab === "planning"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Planning
          </button>

          <button
            className={`admin-nav-item ${activeTab === "settings" ? "active" : ""}`}
            onClick={() => setActiveTab("settings")}
            style={
              activeTab === "settings"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Org Settings
          </button>
        </nav>

        <div className="admin-sidebar-footer">
          <button
            className={`admin-nav-item ${activeTab === "profile" ? "active" : ""}`}
            onClick={() => setActiveTab("profile")}
            style={
              activeTab === "profile"
                ? {
                    backgroundColor: primaryColor,
                    color: getContrastColor(primaryColor),
                  }
                : {}
            }
          >
            Profile
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="admin-main-content">
        {loading && (
          <div className="admin-loading-overlay">
            <div className="admin-loading-spinner"></div>
            <p>Loading dashboard data...</p>
          </div>
        )}
        
        {error && !loading && (
          <div className="admin-error-banner">
            <span className="admin-error-icon">!</span>
            <span>{error}</span>
            <button 
              className="admin-error-retry"
              onClick={fetchStaffingData}
            >
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
            {activeTab === "profile" && renderProfile()}
          </>
        )}
      </main>
    </div>
  )
}

export default AdminDashboard
