import { useState } from "react"
import { Link } from "react-router-dom"
import "./App.css"
import Login from "./Login"

function App() {
  const [showLogin, setShowLogin] = useState(false)

  return (
    <div className="App">
      <nav className="navbar">
        {/* <div class="mainLogo">
          <svg
            version="1.0"
            xmlns="http://www.w3.org/2000/svg"
            width="120.000000pt"
            height="57.000000pt"
            viewBox="0 0 456.000000 219.000000"
            preserveAspectRatio="xMidYMid meet"
            class="Logo"
          >
            <g
              transform="translate(0.000000,219.000000) scale(0.100000,-0.100000)"
              fill="#000000"
              stroke="none"
            >
              <g class="letterB">
                <path
                  d="M60 1090 l0 -1030 523 0 522 0 335 113 c184 63 413 140 508 171 l172
        58 0 274 0 274 -205 0 -206 0 3 138 3 137 203 3 202 2 0 270 0 270 -27 11
        c-16 6 -246 85 -513 175 l-485 164 -517 0 -518 0 0 -1030z m1440 375 l0 -105
        -410 0 -410 0 0 105 0 105 410 0 410 0 0 -105z m0 -755 l0 -100 -410 0 -410 0
        0 100 0 100 410 0 410 0 0 -100z"
                />
              </g>
              <g class="upperS">
                <path
                  d="M2702 1843 l-292 -277 2 -170 3 -170 405 -102 c223 -56 408 -100 413
        -97 4 2 7 125 7 274 l0 269 614 0 615 0 3 23 c2 12 2 136 0 275 l-3 252 -737
        0 -737 0 -293 -277z"
                />
              </g>
              <g class="lowerS">
                <path
                  d="M3650 880 l0 -270 -620 0 -620 0 0 -275 0 -275 740 0 741 0 289 271
        c172 162 290 280 292 293 2 12 1 90 -2 175 l-5 154 -390 98 c-214 54 -398 99
        -407 99 -17 0 -18 -19 -18 -270z"
                />
              </g>
            </g>
          </svg>
          <h3 class="user1">Bit</h3>
          <h3 class="user2">Shift</h3>
        </div>
           */}
        <h2>Clockwise</h2>
        <div className="auth-buttons">
          <button className="btn">Sign Up</button>
          <button className="btn" onClick={() => setShowLogin(true)}>
            Log In
          </button>
        </div>
      </nav>
      <main className="main-content">
        <section className="hero">
          <h1 className="hero-title">Clockwise</h1>
          <p className="hero-subtitle">
            AI-powered shift scheduling that adapts to any situation
          </p>
          <button className="cta-btn">Get Started</button>
        </section>

        <section className="features">
          <div className="feature-card">
            <h3>Smart Scheduling</h3>
            <p>ML-based approach to optimize staff allocation</p>
          </div>
          <div className="feature-card">
            <h3>Cost Aware</h3>
            <p>Designed to help reduce operational overhead</p>
          </div>
          <div className="feature-card">
            <h3>Adaptive</h3>
            <p>Handles emergencies and schedule changes</p>
          </div>
        </section>

        <section className="how-it-works">
          <h2 className="section-title">How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="step-number">01</div>
              <h3>Input Your Data</h3>
              <p>
                Upload employee availability, skills, and business requirements
              </p>
            </div>
            <div className="step">
              <div className="step-number">02</div>
              <h3>AI Analysis</h3>
              <p>Our ML model processes patterns and optimizes schedules</p>
            </div>
            <div className="step">
              <div className="step-number">03</div>
              <h3>Deploy & Adapt</h3>
              <p>
                Real-time adjustments for emergencies and changing conditions
              </p>
            </div>
          </div>
        </section>

        <section className="use-cases">
          <h2 className="section-title">Use Cases</h2>
          <div className="use-case-grid">
            <div className="use-case">
              <h3>Healthcare</h3>
              <p>Shift management with emergency coverage</p>
            </div>
            <div className="use-case">
              <h3>Retail</h3>
              <p>Scheduling for peak hours and demand</p>
            </div>
            <div className="use-case">
              <h3>Manufacturing</h3>
              <p>Operations with skill-based assignments</p>
            </div>
            <div className="use-case">
              <h3>Services</h3>
              <p>Coverage optimization and backup planning</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>© 2026 Bit Shift. All rights reserved.</p>
      </footer>

      {showLogin && <Login onClose={() => setShowLogin(false)} />}
    </div>
  )
}

export default App
