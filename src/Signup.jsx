import { useState } from "react"
import "./Signup.css"
import api from "./services/api"

function Signup({ onClose, onSwitchToLogin, isClosing }) {
  const [organizationName, setOrganizationName] = useState("")
  const [address, setAddress] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [color1, setColor1] = useState("")
  const [color2, setColor2] = useState("")
  const [color3, setColor3] = useState("")
  const [hexInput1, setHexInput1] = useState("")
  const [hexInput2, setHexInput2] = useState("")
  const [hexInput3, setHexInput3] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleHexChange = (colorSetter, hexSetter, value) => {
    const hex = value.replace("#", "")
    hexSetter(hex)
    if (/^[0-9A-Fa-f]{6}$/.test(hex)) {
      colorSetter("#" + hex)
    }
  }

  const handleColorPickerChange = (colorSetter, hexSetter, value) => {
    colorSetter(value)
    hexSetter(value.replace("#", ""))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError(null)

    // Save colors to localStorage first
    const colors = [color1, color2, color3]
    localStorage.setItem("orgColors", JSON.stringify(colors))

    try {
      // Register organization with backend
      const registrationData = {
        org_name: organizationName,
        org_address: address || undefined,
        admin_email: email,
        admin_full_name: fullName,
        admin_password: password,
      }

      const response = await api.auth.register(registrationData)

      console.log("Registration successful:", response)

      // Auto-login after registration
      await api.auth.login({ email, password })

      // Fetch user information after successful login
      const userInfo = await api.auth.getCurrentUser()

      // Store user data in localStorage
      if (userInfo.user) {
        localStorage.setItem("user_info", JSON.stringify(userInfo.user))
      }

      // Redirect to admin dashboard
      window.location.href = "/admin"
    } catch (err) {
      console.error("Registration error:", err)
      setError(err.message || "Registration failed. Please try again.")
      setLoading(false)
    }
  }

  return (
    <div className={`signup-overlay ${isClosing ? "closing" : ""}`}>
      <div className="signup-container">
        <button className="signup-close-btn" onClick={onClose}>
          ×
        </button>
        <div className="signup-header">
          <h2 className="signup-title">Create Account</h2>
          <p className="signup-subtitle">Join Clockwise today</p>
        </div>

        {error && <div className="signup-error-message">{error}</div>}

        <form className="signup-form" onSubmit={handleSubmit}>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="organizationName">
              Organization Name
            </label>
            <input
              className="signup-input"
              type="text"
              id="organizationName"
              value={organizationName}
              onChange={(e) => setOrganizationName(e.target.value)}
              placeholder="Enter your organization name"
              required
              disabled={loading}
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="address">
              Address (Optional)
            </label>
            <input
              className="signup-input"
              type="text"
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter your address"
              disabled={loading}
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="fullName">
              Full Name
            </label>
            <input
              className="signup-input"
              type="text"
              id="fullName"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              placeholder="Enter your full name"
              required
              disabled={loading}
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="email">
              Admin Email
            </label>
            <input
              className="signup-input"
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
              disabled={loading}
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="password">
              Password
            </label>
            <input
              className="signup-input"
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="Enter your password (min 6 characters)"
              required
              minLength="6"
              disabled={loading}
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label">Organization Colors</label>
            <p className="signup-color-description">
              Choose 3 colors that represent your organization
            </p>
            <div className="signup-color-pickers">
              <div className="signup-color-picker-wrapper">
                <label
                  className={`signup-color-circle ${color1 ? "has-color" : ""}`}
                  htmlFor="color1"
                >
                  <div
                    className="signup-color-preview"
                    style={{ backgroundColor: color1 || "transparent" }}
                  >
                    {!color1 && <span className="plus-icon">+</span>}
                  </div>
                </label>
                <input
                  className="signup-color-input"
                  type="color"
                  id="color1"
                  value={color1 || "#000000"}
                  onChange={(e) =>
                    handleColorPickerChange(
                      setColor1,
                      setHexInput1,
                      e.target.value,
                    )
                  }
                />
                <input
                  className="signup-hex-input"
                  type="text"
                  placeholder="Hex code"
                  value={hexInput1}
                  onChange={(e) =>
                    handleHexChange(setColor1, setHexInput1, e.target.value)
                  }
                  maxLength={6}
                />
              </div>
              <div className="signup-color-picker-wrapper">
                <label
                  className={`signup-color-circle ${color2 ? "has-color" : ""}`}
                  htmlFor="color2"
                >
                  <div
                    className="signup-color-preview"
                    style={{ backgroundColor: color2 || "transparent" }}
                  >
                    {!color2 && <span className="plus-icon">+</span>}
                  </div>
                </label>
                <input
                  className="signup-color-input"
                  type="color"
                  id="color2"
                  value={color2 || "#000000"}
                  onChange={(e) =>
                    handleColorPickerChange(
                      setColor2,
                      setHexInput2,
                      e.target.value,
                    )
                  }
                />
                <input
                  className="signup-hex-input"
                  type="text"
                  placeholder="Hex code"
                  value={hexInput2}
                  onChange={(e) =>
                    handleHexChange(setColor2, setHexInput2, e.target.value)
                  }
                  maxLength={6}
                />
              </div>
              <div className="signup-color-picker-wrapper">
                <label
                  className={`signup-color-circle ${color3 ? "has-color" : ""}`}
                  htmlFor="color3"
                >
                  <div
                    className="signup-color-preview"
                    style={{ backgroundColor: color3 || "transparent" }}
                  >
                    {!color3 && <span className="plus-icon">+</span>}
                  </div>
                </label>
                <input
                  className="signup-color-input"
                  type="color"
                  id="color3"
                  value={color3 || "#000000"}
                  onChange={(e) =>
                    handleColorPickerChange(
                      setColor3,
                      setHexInput3,
                      e.target.value,
                    )
                  }
                />
                <input
                  className="signup-hex-input"
                  type="text"
                  placeholder="Hex code"
                  value={hexInput3}
                  onChange={(e) =>
                    handleHexChange(setColor3, setHexInput3, e.target.value)
                  }
                  maxLength={6}
                />
              </div>
            </div>
          </div>
          <button
            type="submit"
            className="signup-submit-btn"
            disabled={loading}
          >
            {loading ? "Creating Account..." : "Sign Up"}
          </button>
        </form>
        <div className="signup-footer">
          <p className="signup-footer-text">
            Already have an account?{" "}
            <a
              href="#"
              className="signup-login-link"
              onClick={(e) => {
                e.preventDefault()
                onSwitchToLogin && onSwitchToLogin()
              }}
            >
              Log in
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}

export default Signup
