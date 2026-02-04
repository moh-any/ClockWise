package server

import (
	"log"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/middleware"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func (s *Server) RegisterRoutes() http.Handler {
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowHeaders:     []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true,
	}))

	r.GET("/health", s.healthHandler)

	authMiddleware, err := middleware.NewAuthMiddleware(s.userStore)
	if err != nil {
		log.Fatal("JWT Error:" + err.Error())
	}

	if err := authMiddleware.MiddlewareInit(); err != nil {
		log.Fatal("authMiddleware.MiddlewareInit() Error:" + err.Error())
	}

	// --- Public Routes ---
	r.POST("/login", authMiddleware.LoginHandler)
	r.POST("/register", s.orgHandler.RegisterOrganization)

	// --- Protected Routes ---
	auth := r.Group("/auth")
	auth.Use(authMiddleware.MiddlewareFunc())
	auth.POST("/refresh_token", authMiddleware.RefreshHandler)
	auth.POST("/logout", authMiddleware.LogoutHandler)
	auth.GET("/me", func(c *gin.Context) {
		claims := jwt.ExtractClaims(c)
		user, _ := c.Get("user")
		c.JSON(http.StatusOK, gin.H{
			"user":   user,
			"claims": claims,
		})
	})

	// Role management
	organization := r.Group("/:org")
	organization.Use(authMiddleware.MiddlewareFunc())

	organization.GET("/")         // Get organization details
	organization.PUT("/")         // Update Organization
	organization.POST("/request") // Request Calloff from organization Employees Only

	dashboard := organization.Group("/dashboard")
	dashboard.GET("/") // Change according to the current user

	schedule := dashboard.Group("/schedule")
	schedule.GET("/")         // Get Schedule
	schedule.PUT("/")         // Edit Schedule
	schedule.POST("/refresh") // Refresh Schedule

	insights := organization.Group("/insights")
	insights.GET("/") // Get All insights

	staffing := organization.Group("/staffing")
	staffing.GET("/") // Show Staffing Summary & Insights
	staffing.POST("/", s.orgHandler.DelegateUser)
	staffing.POST("/upload") // upload employees csv to the server

	employees := staffing.Group("/employees")
	employees.GET("/") // Get All employees

	employee := employees.Group("/:name")
	employee.DELETE("/layoff")         // Layoff an employees
	employee.GET("/")                  // Get Employee Details
	employee.GET("/schedule")          // Get Employee Schedule
	employee.PUT("/schedule")          // Edit Employee Schedule
	employee.GET("/requests")          // Show all requests
	employee.POST("/requests/approve") // Approve requests as a manager or org admin
	employee.POST("/requests/decline") // Decline requests as a manager or org admin

	perferences := organization.Group("/preferences") // Employees only
	perferences.GET("/")                              // Get Current Employee Perfrences
	perferences.PUT("/")                              // Edit current perferences and refresh schedule

	rules := organization.Group("/rules") // Rules of the organization
	rules.GET("/")                        // Get all the rules of the organization
	rules.PUT("/")                        // Edit the rules of the organization

	return r
}

func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, s.db.Health())
}
