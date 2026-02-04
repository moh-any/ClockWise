import { Navigate } from "react-router-dom"

function ProtectedRoute({ children }) {
  const token = localStorage.getItem("access_token")

  if (!token) {
    // Redirect to home page if not authenticated
    return <Navigate to="/" replace />
  }

  return children
}

export default ProtectedRoute
