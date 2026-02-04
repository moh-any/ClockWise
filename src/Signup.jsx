import { useState } from "react"
import "./Signup.css"

function Signup({ onClose, onSwitchToLogin, isClosing }) {
  const [organizationName, setOrganizationName] = useState("")
  const [address, setAddress] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [color1, setColor1] = useState("")
  const [color2, setColor2] = useState("")
  const [color3, setColor3] = useState("")
  const [hexInput1, setHexInput1] = useState("")
  const [hexInput2, setHexInput2] = useState("")
  const [hexInput3, setHexInput3] = useState("")

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

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log("Signup submitted", {
      organizationName,
      address,
      email,
      password,
      colors: [color1, color2, color3],
    })
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
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="address">
              Address
            </label>
            <input
              className="signup-input"
              type="text"
              id="address"
              value={address}
              onChange={(e) => setAddress(e.target.value)}
              placeholder="Enter your address"
              required
            />
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="email">
              Email
            </label>
            <input
              className="signup-input"
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="Enter your email"
              required
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
              placeholder="Enter your password"
              required
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
          <button type="submit" className="signup-submit-btn">
            Sign Up
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
