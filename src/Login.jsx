import { useState } from "react"
import "./Login.css"

function Login({ onClose, onSwitchToSignup, isClosing }) {
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")

  const handleSubmit = (e) => {
    e.preventDefault()
    console.log("Login submitted", { email, password })
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
          <button type="submit" className="login-submit-btn">
            Log In
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
