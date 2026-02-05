package server

import (
	"log"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/middleware"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

// @title           ClockWise API
// @version         1.0.0
// @description     ClockWise is a workforce management and scheduling platform for organizations.
// @termsOfService  http://swagger.io/terms/

// @contact.name   ClockWise API Support
// @contact.email  ziadeliwa@aucegypt.edu

// @license.name  MIT License
// @license.url   https://opensource.org/license/mit

// @host      localhost:8080
// @BasePath  /api

// @securityDefinitions.apikey BearerAuth
// @in header
// @name Authorization

// @externalDocs.description  OpenAPI
// @externalDocs.url          https://swagger.io/resources/open-api/
func (s *Server) RegisterRoutes() http.Handler {
	r := gin.Default()
	gin.SetMode(gin.TestMode)

	r.RedirectTrailingSlash = false

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:3000"},
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowHeaders:     []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true,
	}))

	api := r.Group("/api")
	r.GET("/health", s.healthHandler)

	authMiddleware, err := middleware.NewAuthMiddleware(s.userStore)
	if err != nil {
		log.Fatal("JWT Error:" + err.Error())
	}

	if err := authMiddleware.MiddlewareInit(); err != nil {
		log.Fatal("authMiddleware.MiddlewareInit() Error:" + err.Error())
	}

	// --- Public Routes ---
	api.POST("/login", authMiddleware.LoginHandler)
	api.POST("/register", s.orgHandler.RegisterOrganization)

	// --- Protected Routes ---
	auth := api.Group("/auth")
	auth.Use(authMiddleware.MiddlewareFunc())
	auth.POST("/refresh", authMiddleware.RefreshHandler)
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
	organization := api.Group("/:org")
	organization.Use(authMiddleware.MiddlewareFunc())

	organization.GET("")          // Get organization details
	organization.POST("/request") // Request Calloff. An employee can request a calloff from their organization

	// TODO: roles routes editing
	roles := organization.Group("/roles")
	roles.GET("")  // Get All roles
	roles.POST("") // Create roles

	roles.GET("/:role")    // Get role
	roles.PUT("/:role")    // Update role
	roles.DELETE("/:role") // Delete role

	dashboard := organization.Group("/dashboard")
	dashboard.GET("") // Change according to the current user

	schedule := dashboard.Group("/schedule")
	schedule.GET("")          // Get Schedule
	schedule.PUT("")          // Edit Schedule
	schedule.POST("/refresh") // Refresh Schedule

	insights := organization.Group("/insights")
	insights.GET("", s.insightHandler.GetInsightsHandler) // Get All insights

	staffing := organization.Group("/staffing")
	staffing.GET("", s.staffingHandler.GetStaffingSummary)
	staffing.POST("", s.orgHandler.DelegateUser)
	staffing.POST("/upload", s.staffingHandler.UploadEmployeesCSV)

	employees := staffing.Group("/employees")
	employees.GET("", s.staffingHandler.GetAllEmployees)

	employee := employees.Group("/:id")
	employee.DELETE("/layoff", s.employeeHandler.LayoffEmployee)
	employee.GET("", s.employeeHandler.GetEmployeeDetails)

	employee.GET("/schedule") // Get Employee Schedule
	employee.PUT("/schedule") // Edit Employee Schedule

	employee.GET("/requests", s.employeeHandler.GetEmployeeRequests)
	employee.POST("/requests/approve", s.employeeHandler.ApproveRequest)
	employee.POST("/requests/decline", s.employeeHandler.DeclineRequest)

	preferences := organization.Group("/preferences") // Employees only
	preferences.GET("")                               // Get Current Employee Preferences
	preferences.POST("")                              // Edit current preferences

	rules := organization.Group("/rules") // Rules of the organization
	rules.GET("")                         // Get all the rules of the organization
	rules.POST("")                        // Edit the rules of the organization

	return r
}

// healthHandler godoc
// @Summary      Health check
// @Description  Returns the health status of the API and database connection
// @Tags         Health
// @Accept       json
// @Produce      json
// @Success      200 {object} map[string]interface{} "API is healthy"
// @Router       /health [get]
func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, s.db.Health())
}
