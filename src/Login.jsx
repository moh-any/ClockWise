import { useState } from "react"
import { useNavigate } from "react-router-dom"
import "./Login.css"
import api from "./services/api"

function Login({ onClose, onSwitchToSignup, isClosing }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const response = await api.auth.login({ email, password })

      console.log("Login successful, token saved to localStorage")
      console.log("Access token:", response.access_token)

      // Get user info to determine role
      const userInfo = await api.auth.getCurrentUser()
      console.log("Full user info:", userInfo)

      // Fetch and restore organization colors
      try {
        const orgProfile = await api.organization.getProfile()
        if (orgProfile?.data) {
          // Ensure hex colors have # prefix (API returns without #)
          const addHashPrefix = (hex, fallback) => {
            if (!hex) return fallback
            return hex.startsWith("#") ? hex : `#${hex}`
          }

          const colors = [
            addHashPrefix(orgProfile.data.hex1, "#4A90E2"),
            addHashPrefix(orgProfile.data.hex2, "#7B68EE"),
            addHashPrefix(orgProfile.data.hex3, "#FF6B6B"),
          ]
          localStorage.setItem("orgColors", JSON.stringify(colors))
          console.log("Organization colors restored:", colors)
        }
      } catch (colorErr) {
        console.error("Failed to fetch organization colors:", colorErr)
        // Set default colors as fallback
        const defaultColors = ["#4A90E2", "#7B68EE", "#FF6B6B"]
        localStorage.setItem("orgColors", JSON.stringify(defaultColors))
        console.log("Using default colors as fallback:", defaultColors)
      }

      // Navigate based on user role - handle nested structure
      onClose()

      // API returns nested structure with user.user_role or claims.user_role
      const roleValue =
        userInfo?.user?.user_role ||
        userInfo?.claims?.user_role ||
        userInfo?.user_role ||
        "employee"
      const role = String(roleValue).toLowerCase().trim()

      console.log("Detected role:", role)

      if (role === "admin" || role === "manager") {
        console.log("✅ Navigating to /admin")
        navigate("/admin")
      } else {
        console.log("Navigating to /employee")
        navigate("/employee")
      }
    } catch (err) {
      setError(err.message || "Login failed. Please check your credentials.")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className={`login-overlay ${isClosing ? "closing" : ""}`}>
      <div className="login-container">
        <button className="login-close-btn" onClick={onClose}>
          ×
        </button>
        <div className="login-header">
          <h2 className="login-title">Welcome Back</h2>
          <p className="login-subtitle">Log in to your account</p>
        </div>
        {error && <div className="login-error-message">{error}</div>}
        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-form-group">
            <label className="login-label" htmlFor="email">
              Email
            </label>
            <input
              className="login-input"
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
            />
          </div>
          <div className="login-form-group">
            <label className="login-label" htmlFor="password">
              Password
            </label>
            <input
              className="login-input"
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password"
              required
              minLength="6"
              disabled={loading}
            />
          </div>
          <div className="login-options">
            <label className="login-checkbox-label">
              <input type="checkbox" className="login-checkbox" />
              Remember me
            </label>
            <a href="#" className="login-forgot-link">
              Forgot password?
            </a>
          </div>
          <button type="submit" className="login-submit-btn" disabled={loading}>
            {loading ? "Logging In..." : "Log In"}
          </button>
        </form>
        <div className="login-footer">
          <p className="login-footer-text">
            Don't have an account?{" "}
            <a
              href="#"
              className="login-signup-link"
              onClick={(e) => {
                e.preventDefault()
                onSwitchToSignup && onSwitchToSignup()
              }}
            >
              Sign up
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Login
