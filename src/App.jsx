import { useState, useEffect, useRef } from "react"
import { Link } from "react-router-dom"
import "./App.css"
import Login from "./Login"
import Signup from "./Signup"

function App() {
  const [showLogin, setShowLogin] = useState(false)
  const [showSignup, setShowSignup] = useState(false)
  const [isClosingLogin, setIsClosingLogin] = useState(false)
  const [isClosingSignup, setIsClosingSignup] = useState(false)

  useEffect(() => {
    if (showLogin || showSignup) {
      document.documentElement.style.overflow = "hidden"
    } else {
      document.documentElement.style.overflow = "unset"
    }

    return () => {
      document.documentElement.style.overflow = "unset"
    }
  }, [showLogin, showSignup])

  const handleCloseLogin = () => {
    setIsClosingLogin(true)
    setTimeout(() => {
      setShowLogin(false)
      setIsClosingLogin(false)
    }, 600)
  }

  const handleCloseSignup = () => {
    setIsClosingSignup(true)
    setTimeout(() => {
      setShowSignup(false)
      setIsClosingSignup(false)
    }, 600)
  }

  const handleSwitchToSignup = () => {
    setIsClosingLogin(true)
    setShowSignup(true)
    setTimeout(() => {
      setShowLogin(false)
      setIsClosingLogin(false)
    }, 600)
  }

  const handleSwitchToLogin = () => {
    setIsClosingSignup(true)
    setShowLogin(true)
    setTimeout(() => {
      setShowSignup(false)
      setIsClosingSignup(false)
    }, 600)
  }

  const logoRef = useRef(null)

  useEffect(() => {
    const box = logoRef.current
    if (!box) return

    const handleMouseEnter = () => {
      box.classList.remove("exitAnim")
      box.classList.add("hoverActive")
    }

    const handleMouseLeave = () => {
      box.classList.remove("hoverActive")
      box.classList.add("exitAnim")
      setTimeout(() => {
        box.classList.remove("exitAnim")
      }, 1000)
    }

    box.addEventListener("mouseenter", handleMouseEnter)
    box.addEventListener("mouseleave", handleMouseLeave)

    return () => {
      box.removeEventListener("mouseenter", handleMouseEnter)
      box.removeEventListener("mouseleave", handleMouseLeave)
    }
  }, [])

  return (
    <div className="app">
      <nav className="navbar">
        <div className="clockwiseLogo" ref={logoRef}>
          <div className="logoImagesBox">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              width="60px"
              height="60px"
              className="logo1"
              viewBox="1100 1 1240 1"
            >
              <path d="M1664.5-602.5c-31 1-59.9 5-63.9 8.4-4.5 4-7.3 19.8-7.3 44.7 0 44.6 7.3 55.9 37.3 55.9h19.2v27.7c0 30.5.6 30-42.4 37.3-32.2 5.6-84.7 24.3-127.1 45.2-106.8 53.7-204 162.1-250.3 279.7-25.4 65-33.9 122.6-30.5 208.4 2.8 77.4 10.2 112.5 36.7 178.6 55.4 138.4 186.5 254.8 337.3 299.4 69 21 176.9 25.5 246.4 11.3 175.1-35 330-166 389.2-330 70.7-193.2 26.6-399.4-117-549.1-37.8-39.6-37.2-35.6-15.7-66.1 1.1-.6 7.9 1.7 16.4 5 12.4 5.7 16.3 5.2 26.5-3.9 18-16.4 27.7-37.8 21.5-49.1-6.2-10.2-105.7-83.1-114.1-83.1-8.5 0-43.6 40.7-43.6 50.9 0 5 5.1 14 11.3 19.7 10.8 10.2 10.8 10.2 0 25.5l-11.3 15.8-38.4-18.7a502 502 0 0 0-140.7-45.2l-29.9-4v-27c0-26.6.6-26.6 20.3-30 31.7-5 36.2-11.9 36.2-52.5 0-28.9-2.3-38.5-11.3-47.5-11.9-11.9-9-11.9-154.8-7.3m169 264.4c83 23.1 170 80.8 223.7 148 64.4 81.4 95.4 169 95.4 270 0 72.4-13.5 128.9-48.5 199.5-45.8 93.8-144.1 179.1-243.6 213-55.9 18.7-119.2 27.7-170 23.8C1402.3 493 1214.7 206 1310.2-64.1c22.6-64.4 48-104 102.3-158.2 66.7-66.7 128.8-101.1 217.5-121 49.2-10.6 154.8-8.4 203.4 5.2" />
              <g className="inner1">
                <path d="M1635.7-295.2a387 387 0 0 0-301.2 356 386.3 386.3 0 0 0 366.1 404.5c70.7 3.4 123.8-7.9 191-40.7 41.8-20.9 61.6-35 96-69.5 68.4-68.3 102.9-137.3 114.2-228.2 14.7-120.4-23.2-226.6-112.4-315.3-80.8-80.2-162.2-113.6-274-112.4-31.7.5-67.3 2.8-79.7 5.6m87 274.6c0 28.8 1.1 52.6 2.2 52.6.6 0 21-6.3 45.2-13.6C1807 7 1813.7 6 1813.7 13.9c0 14.1-91.6 326.5-97.8 332.2-1.1 1.1-4-46.3-6.2-106.2-1.7-59.4-4.5-109.6-6.2-110.8-1.7-1.7-21 2.9-43.5 9-22 6.9-41.3 11.4-43 10.2-1.1-1.7 20.4-78.5 48-171.7l49.8-169 3.4 60c2.2 32.7 4 83.6 4.5 111.8" />
              </g>
            </svg>

            <svg
              version="1.0"
              xmlns="http://www.w3.org/2000/svg"
              width="65.25pt"
              height="48.825pt"
              viewBox="1020 1 1700 1"
              preserveAspectRatio="xMidYMid meet"
              className="logo2"
            >
              <g
                transform="translate(0.000000,1700.000000) scale(0.55,-0.55)"
                fill="#000000"
                stroke="none"
              >
                <path d="M2546 4034 c-11 -10 -16 -34 -16 -74 0 -67 15 -90 61 -90 28 0 29 -2 29 -48 l0 -48 -62 -13 c-435 -89 -751 -535 -689 -972 45 -310 213 -545 488 -683 147 -73 338 -102 520 -77 49 6 385 30 748 52 597 36 731 46 655 48 -14 1 -187 12 -385 26 -198 13 -417 27 -487 31 -71 4 -128 9 -128 11 0 2 33 35 73 73 l72 70 275 21 c151 11 389 28 528 38 139 11 255 21 258 24 2 2 -53 7 -123 10 -131 5 -836 49 -840 52 -1 0 12 35 30 76 l32 75 320 23 c176 12 442 30 590 39 316 20 334 17 -330 52 -214 11 -425 23 -468 26 l-78 6 3 77 3 76 400 21 c220 12 508 27 640 34 295 15 454 27 398 29 -131 4 -1238 51 -1338 57 l-121 6 -11 47 c-6 25 -14 53 -17 61 -6 14 56 19 511 44 285 16 615 34 733 40 l215 12 -135 7 c-127 7 -1347 57 -1381 57 -16 0 -84 88 -75 98 3 2 157 15 343 28 345 24 409 30 338 33 -63 2 -800 63 -803 66 -2 2 4 15 13 29 15 22 19 24 42 13 23 -10 28 -8 54 21 16 18 29 41 29 51 0 30 -160 151 -199 151 -13 0 -30 -15 -46 -38 -26 -40 -26 -66 1 -76 11 -4 12 -10 5 -23 -26 -45 -24 -45 -102 -8 -74 34 -211 75 -256 75 -21 0 -23 4 -23 50 0 49 1 50 29 50 45 0 61 23 61 86 0 97 5 94 -195 94 -144 0 -176 -3 -189 -16z m352 -420 c46 -9 116 -34 172 -61 80 -40 109 -61 186 -137 76 -77 97 -106 136 -186 65 -134 82 -211 76 -357 -9 -204 -70 -345 -213 -488 -142 -142 -284 -204 -486 -213 -95 -4 -130 -1 -200 17 -590 147 -754 900 -279 1282 79 63 202 124 290 143 88 19 225 19 318 0z" />
              </g>
            </svg>

            <svg
              version="1.0"
              xmlns="http://www.w3.org/2000/svg"
              width="67.5pt"
              height="50.175pt"
              viewBox="480 1 1600 1"
              preserveAspectRatio="xMidYMid meet"
              className="logo3"
            >
              <g
                transform="translate(0.000000,1500.000000) scale(0.5,-0.5)"
                fill="#000000"
                stroke="none"
              >
                <path d="M3080 4031 c-5 -11 -10 -44 -10 -74 0 -61 19 -87 63 -87 26 0 27 -3 27 -49 l0 -48 -50 -7 c-114 -15 -249 -72 -383 -160 l-52 -34 -395 -31 c-217 -18 -406 -33 -420 -34 -26 -3 16 -6 443 -37 136 -9 250 -20 253 -22 9 -10 -59 -98 -75 -98 -36 0 -1257 -50 -1381 -57 l-135 -7 125 -7 c1354 -74 1341 -73 1334 -89 -3 -8 -11 -36 -17 -61 l-11 -47 -121 -6 c-100 -6 -1207 -53 -1338 -57 -56 -2 103 -14 398 -29 132 -7 420 -22 640 -34 l400 -21 3 -77 c2 -43 2 -78 0 -78 -2 0 -122 -7 -268 -15 -146 -8 -398 -22 -560 -30 -162 -9 -299 -17 -305 -19 -5 -1 51 -6 125 -10 74 -4 326 -20 560 -37 234 -16 437 -29 453 -29 25 0 31 -8 62 -77 20 -42 34 -77 33 -78 -5 -4 -873 -56 -922 -55 -27 0 -47 -3 -43 -6 3 -3 120 -14 259 -25 139 -10 377 -27 528 -38 l275 -21 73 -70 c39 -38 72 -71 72 -73 0 -2 -57 -7 -127 -11 -71 -4 -290 -18 -488 -31 -198 -14 -371 -25 -384 -25 -13 0 -22 -2 -20 -4 2 -3 306 -23 674 -45 369 -22 705 -46 749 -52 105 -16 281 -6 374 21 245 69 458 252 561 484 149 332 83 705 -173 980 -54 58 -55 60 -38 80 9 12 17 22 18 24 1 1 13 -2 27 -7 28 -11 43 -2 71 39 22 33 20 46 -8 71 -35 31 -167 119 -178 119 -5 0 -22 -15 -39 -32 -31 -35 -38 -75 -14 -84 19 -7 19 -23 1 -47 -14 -18 -18 -17 -90 18 -42 20 -117 46 -166 58 l-90 22 0 48 c0 45 1 47 29 47 46 0 61 23 61 90 0 90 0 90 -205 90 -162 0 -175 -1 -185 -19z m332 -416 c236 -49 453 -241 533 -472 122 -350 -34 -738 -360 -899 -115 -56 -218 -77 -354 -72 -202 9 -344 71 -486 213 -143 143 -204 284 -213 488 -6 146 11 223 76 357 39 80 60 109 136 186 77 76 106 97 186 137 52 25 127 53 165 61 93 19 226 20 317 1z" />
              </g>
            </svg>
          </div>
          <h1 className="logoName">ClockWise</h1>
        </div>
        <div className="authButtons">
          <button className="btn" onClick={() => setShowSignup(true)}>
            Sign Up
          </button>
          <button className="btn" onClick={() => setShowLogin(true)}>
            Log In
          </button>
        </div>
      </nav>
      <main className="mainContent">
        <section className="hero">
          <h1 className="heroTitle">ClockWise</h1>
          <p className="hero-subtitle">
            AI-powered shift scheduling that adapts to any situation
          </p>
          <button className="ctaBtn" onClick={() => setShowSignup(true)}>
            Get Started
          </button>
        </section>

        <section className="features">
          <div className="featureCard">
            <h3>Smart Scheduling</h3>
            <p>ML-based approach to optimize staff allocation</p>
          </div>
          <div className="featureCard">
            <h3>Cost Aware</h3>
            <p>Designed to help reduce operational overhead</p>
          </div>
          <div className="featureCard">
            <h3>Adaptive</h3>
            <p>Handles emergencies and schedule changes</p>
          </div>
        </section>

        <section className="howItWorks">
          <h2 className="sectionTitle">How It Works</h2>
          <div className="steps">
            <div className="step">
              <div className="stepNumber">01</div>
              <h3>Input Your Data</h3>
              <p>
                Upload employee availability, skills, and business requirements
              </p>
            </div>
            <div className="step">
              <div className="stepNumber">02</div>
              <h3>AI Analysis</h3>
              <p>Our ML model processes patterns and optimizes schedules</p>
            </div>
            <div className="step">
              <div className="stepNumber">03</div>
              <h3>Deploy & Adapt</h3>
              <p>
                Real-time adjustments for emergencies and changing conditions
              </p>
            </div>
          </div>
        </section>

        <section className="useCases">
          <h2 className="sectionTitle">Use Cases</h2>
          <div className="useCaseGrid">
            <div className="useCase">
              <h3>Healthcare</h3>
              <p>Shift management with emergency coverage</p>
            </div>
            <div className="useCase">
              <h3>Retail</h3>
              <p>Scheduling for peak hours and demand</p>
            </div>
            <div className="useCase">
              <h3>Manufacturing</h3>
              <p>Operations with skill-based assignments</p>
            </div>
            <div className="useCase">
              <h3>Services</h3>
              <p>Coverage optimization and backup planning</p>
            </div>
          </div>
        </section>
      </main>

      <footer className="footer">
        <p>© 2026 ClockWise. All rights reserved.</p>
      </footer>

      {showLogin && (
        <Login
          onClose={handleCloseLogin}
          onSwitchToSignup={handleSwitchToSignup}
          isClosing={isClosingLogin}
        />
      )}
      {showSignup && (
        <Signup
          onClose={handleCloseSignup}
          onSwitchToLogin={handleSwitchToLogin}
          isClosing={isClosingSignup}
        />
      )}
    </div>
  )
}

export default App
