package server

import (
	"log"
	"net/http"

	"ClockWise/backend/internal/api"
	"ClockWise/backend/internal/middleware"
	"ClockWise/backend/internal/service"

	jwt "github.com/appleboy/gin-jwt/v2"
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

	emailService := service.NewSMTPEmailService()

	orgHandler := api.NewOrgHandler(s.orgStore, s.userStore, emailService)

	authMiddleware, err := middleware.NewAuthMiddleware(s.userStore)
	if err != nil {
		log.Fatal("JWT Error:" + err.Error())
	}

	if err := authMiddleware.MiddlewareInit(); err != nil {
		log.Fatal("authMiddleware.MiddlewareInit() Error:" + err.Error())
	}

	// --- Public Routes ---
	r.POST("/login", authMiddleware.LoginHandler)
	r.POST("/register", orgHandler.RegisterOrganization)

	// --- Protected Routes ---
	auth := r.Group("/auth")
	auth.Use(authMiddleware.MiddlewareFunc())
	auth.GET("/refresh_token", authMiddleware.RefreshHandler)
	auth.POST("/logout", authMiddleware.LogoutHandler)
	auth.POST("/delegate", orgHandler.DelegateUser)
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

	organization.PUT("/")  // Update Organization
	organization.GET("/")  // Get organization details
	organization.POST("/request") // Request Calloff from organization Employees Only

	dashboard := organization.Group("/dashboard")
	dashboard.GET("/") // Change according to the current user

	schedule := dashboard.Group("/schedule")
	schedule.GET("/")         // Get Schedule
	schedule.POST("/refresh") // Refresh Schedule
	schedule.PUT("/")         // Edit Schedule

	insights := organization.Group("/insights")
	insights.GET("/") // Get All insights

	settings := organization.Group("/settings")
	settings.GET("/") // Show Current Settings (General Info)
	settings.PUT("/") // Edit Settings (General Info)

	staffing := organization.Group("/staffing")
	staffing.GET("/") // Show Staffing Summary & Insights

	employees := staffing.Group("/employees")
	employees.GET("/")        // Get All employees
	employees.POST("/")       // Create a new employee  (Hire)
	employees.POST("/upload") // upload employees csv to the server

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
	perferences.PUT("/")                             // Edit current perferences and refresh schedule

	rules := organization.Group("/rules") // Rules of the organization
	rules.GET("/")                        // Get all the rules of the organization
	rules.PUT("/")                        // Edit the rules of the organization
	return r
}

func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, s.db.Health())
}
