import { useState, useRef, useEffect } from "react"
import { useNavigate } from "react-router-dom"
import "./Signup.css"
import api from "./services/api"

function Signup({ onClose, onSwitchToLogin, isClosing }) {
  const navigate = useNavigate()
  const [showMap, setShowMap] = useState(false)
  const [organizationName, setOrganizationName] = useState("")
  const [address, setAddress] = useState("")
  const [orgType, setOrgType] = useState("restaurant")
  const [orgPhone, setOrgPhone] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [fullName, setFullName] = useState("")
  const [color1, setColor1] = useState("")
  const [color2, setColor2] = useState("")
  const [color3, setColor3] = useState("")
  const [hexInput1, setHexInput1] = useState("")
  const [hexInput2, setHexInput2] = useState("")
  const [hexInput3, setHexInput3] = useState("")
  const [latitude, setLatitude] = useState(null)
  const [longitude, setLongitude] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)
  const mapInstance = useRef(null)
  const markerInstance = useRef(null)

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

  // Load Mapbox library
  useEffect(() => {
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

  // Initialize map when showMap becomes true
  useEffect(() => {
    if (!showMap) return

    const initializeMap = () => {
      if (typeof window.mapboxgl === "undefined") {
        console.log("Mapbox GL not loaded yet, retrying...")
        return false
      }

      const mapContainer = document.getElementById("signup-map")
      if (!mapContainer || mapInstance.current) return true

      try {
        window.mapboxgl.accessToken =
          "pk.eyJ1IjoibW9zdGFmYTE5MjYiLCJhIjoiY21sOW1xZWNiMDRobTNlczczNDc0cGM0aCJ9.z2un235WCxTP0RswBTewPg"

        const map = new window.mapboxgl.Map({
          container: "signup-map",
          style: "mapbox://styles/mapbox/satellite-streets-v12",
          projection: "globe",
          zoom: 2,
          center: [0, 0],
          attributionControl: true,
        })

        map.on("click", (e) => {
          const lat = e.lngLat.lat.toFixed(6)
          const lng = e.lngLat.lng.toFixed(6)
          setLatitude(lat)
          setLongitude(lng)

          // Remove old marker if exists
          if (markerInstance.current) {
            markerInstance.current.remove()
          }

          // Add new marker
          markerInstance.current = new window.mapboxgl.Marker({
            color: color1 || "#4A90E2",
          })
            .setLngLat([lng, lat])
            .addTo(map)
        })

        mapInstance.current = map
        return true
      } catch (error) {
        console.error("Error initializing map:", error)
        return false
      }
    }

    // Try to initialize immediately, then retry if needed
    let attempts = 0
    const maxAttempts = 20
    const intervalId = setInterval(() => {
      attempts++
      if (initializeMap() || attempts >= maxAttempts) {
        clearInterval(intervalId)
        if (attempts >= maxAttempts && !mapInstance.current) {
          console.error("Failed to initialize map after", maxAttempts, "attempts")
        }
      }
    }, 200)

    return () => {
      clearInterval(intervalId)
      if (mapInstance.current) {
        mapInstance.current.remove()
        mapInstance.current = null
      }
      if (markerInstance.current) {
        markerInstance.current.remove()
        markerInstance.current = null
      }
    }
  }, [showMap, color1])

  const handleInitialSubmit = async (e) => {
    e.preventDefault()
    setError(null)

    // Validate colors
    if (!color1 || !color2 || !color3) {
      setError("Please select all three organization colors")
      return
    }

    // Save colors to localStorage
    const colors = [color1, color2, color3]
    localStorage.setItem("orgColors", JSON.stringify(colors))

    // Show map for location selection
    setShowMap(true)
  }

  const handleFinalSubmit = async () => {
    if (!latitude || !longitude) {
      setError("Please select your location on the map")
      return
    }

    setLoading(true)
    setError(null)

    try {
      // Register organization with backend
      const registrationData = {
        org_name: organizationName,
        org_address: address || undefined,
        org_type: orgType,
        org_phone: orgPhone,
        latitude: parseFloat(latitude),
        longitude: parseFloat(longitude),
        admin_email: email,
        admin_full_name: fullName,
        admin_password: password,
        hex1: color1.replace("#", ""),
        hex2: color2.replace("#", ""),
        hex3: color3.replace("#", ""),
      }

      const response = await api.auth.register(registrationData)

      console.log("Registration successful:", response)
      console.log("Organization ID:", response.organization_id)

      // Auto-login after registration using the same credentials
      const loginResponse = await api.auth.login({ email, password })

      console.log("Login successful, token saved to localStorage")
      console.log("Access token:", loginResponse.access_token)

      // Close the signup modal and navigate to admin dashboard
      onClose()
      navigate("/admin")
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

        {!showMap ? (
          <>
            <div className="signup-header">
              <h2 className="signup-title">Create Account</h2>
              <p className="signup-subtitle">Join Clockwise today</p>
            </div>

            {error && <div className="signup-error-message">{error}</div>}

            <form className="signup-form" onSubmit={handleInitialSubmit}>
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
            <label className="signup-label" htmlFor="orgType">
              Organization Type
            </label>
            <select
              className="signup-input"
              id="orgType"
              value={orgType}
              onChange={(e) => setOrgType(e.target.value)}
              required
              disabled={loading}
            >
              <option value="restaurant">Restaurant</option>
              <option value="cafe">Cafe</option>
              <option value="bar">Bar</option>
              <option value="lounge">Lounge</option>
              <option value="pub">Pub</option>
            </select>
          </div>
          <div className="signup-form-group">
            <label className="signup-label" htmlFor="orgPhone">
              Organization Phone
            </label>
            <input
              className="signup-input"
              type="tel"
              id="orgPhone"
              value={orgPhone}
              onChange={(e) => setOrgPhone(e.target.value)}
              placeholder="+1234567890"
              required
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
              placeholder="Enter your password (min 8 characters)"
              required
              minLength="8"
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
            Continue to Location
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
          </>
        ) : (
          <>
            <div className="signup-header">
              <h2 className="signup-title">Select Your Location</h2>
              <p className="signup-subtitle">
                Click anywhere on the globe to set your organization's location
              </p>
            </div>

            {error && <div className="signup-error-message">{error}</div>}

            {latitude && longitude && (
              <div 
                style={{
                  background: 'var(--gray-50)',
                  border: '1px solid var(--gray-200)',
                  borderRadius: '8px',
                  padding: '12px',
                  marginBottom: '16px',
                  display: 'flex',
                  justifyContent: 'space-around',
                }}
              >
                <div>
                  <span style={{ fontSize: '12px', color: 'var(--gray-600)' }}>Latitude: </span>
                  <span style={{ fontWeight: 600, color: 'var(--gray-900)' }}>{latitude}</span>
                </div>
                <div>
                  <span style={{ fontSize: '12px', color: 'var(--gray-600)' }}>Longitude: </span>
                  <span style={{ fontWeight: 600, color: 'var(--gray-900)' }}>{longitude}</span>
                </div>
              </div>
            )}

            <div
              id="signup-map"
              style={{
                width: '100%',
                height: '500px',
                borderRadius: '12px',
                overflow: 'hidden',
                marginBottom: '20px',
              }}
            ></div>

            {!latitude && (
              <p
                style={{
                  textAlign: 'center',
                  color: 'var(--gray-600)',
                  fontSize: '14px',
                  marginBottom: '16px',
                }}
              >
                👆 Click on the map to select your location
              </p>
            )}

            <div style={{ display: 'flex', gap: '12px' }}>
              <button
                className="signup-submit-btn"
                style={{ flex: 1, background: 'var(--gray-400)' }}
                onClick={() => setShowMap(false)}
                disabled={loading}
              >
                Back
              </button>
              <button
                className="signup-submit-btn"
                style={{ flex: 2 }}
                onClick={handleFinalSubmit}
                disabled={loading || !latitude || !longitude}
              >
                {loading ? "Creating Account..." : "Complete Signup"}
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default Signup
