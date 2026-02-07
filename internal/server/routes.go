package server

import (
	"log"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/middleware"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/gin-contrib/cors"
	"github.com/gin-contrib/gzip"
	"github.com/gin-gonic/gin"
)

// TODO: Add Caching
// TODO: Add Nginx for rate limiting

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
	gin.SetMode(gin.DebugMode)

	r.Use(gzip.Gzip(gzip.BestCompression))

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

	// Profile Management (protected)
	auth.GET("/profile", s.profileHandler.GetProfileHandler)
	auth.POST("/profile/changepassword", s.profileHandler.ChangePasswordHandler)

	// Role management
	organization := api.Group("/:org")
	organization.Use(authMiddleware.MiddlewareFunc())

	organization.GET("", s.orgHandler.GetOrganizationProfile)                  // Get organization details
	organization.POST("/request", s.employeeHandler.RequestHandlerForEmployee) // Request Calloff. An employee can request a calloff from their organization

	// Orders Management & Insights
	orders := organization.Group("/orders")
	orders.GET("", s.orderHandler.GetOrdersInsights)
	orders.POST("/upload/orders", s.orderHandler.UploadAllPastOrdersCSV)
	orders.POST("/upload/items", s.orderHandler.UploadOrderItemsCSV)
	orders.GET("/all", s.orderHandler.GetAllOrders)
	orders.GET("/week", s.orderHandler.GetAllOrdersForLastWeek)
	orders.GET("/today", s.orderHandler.GetAllOrdersToday)

	// Delivery Management & Insights
	deliveries := organization.Group("/deliveries")
	deliveries.GET("", s.orderHandler.GetDeliveryInsights)
	deliveries.POST("/upload", s.orderHandler.UploadAllPastDeliveriesCSV)
	deliveries.GET("/all", s.orderHandler.GetAllDeliveries)
	deliveries.GET("/week", s.orderHandler.GetAllDeliveriesForLastWeek)
	deliveries.GET("/today", s.orderHandler.GetAllDeliveriesToday)

	// Items Management & Insights
	items := organization.Group("/items")
	items.GET("", s.orderHandler.GetItemsInsights)
	items.POST("/upload", s.orderHandler.UploadItemsCSV)
	items.GET("/all", s.orderHandler.GetAllItems)

	// Role management
	roles := organization.Group("/roles")
	roles.GET("", s.rolesHandler.GetAllRoles)         // Get All roles
	roles.POST("", s.rolesHandler.CreateRole)         // Create role
	roles.GET("/:role", s.rolesHandler.GetRole)       // Get role
	roles.PUT("/:role", s.rolesHandler.UpdateRole)    // Update role
	roles.DELETE("/:role", s.rolesHandler.DeleteRole) // Delete role

	// TODO: Dashboard which includes, demands, insights, general info
	dashboard := organization.Group("/dashboard")
	dashboard.GET("/demand", s.dashboardHandler.GetDemandHeatMapHandler)
	dashboard.POST("/demand/refresh", s.dashboardHandler.RefreshDemandHeatMapHandler) // Send data and fetch demand from demand service

	// TODO: Surge ML Model Handlin
	surge := dashboard.Group("/surge")
	surge.GET("", s.alertHandler.GetAlertInsightsHandler) // Get All Alerts
	surge.GET("/all", s.alertHandler.GetAllAlertsHandler)
	surge.GET("/week", s.alertHandler.GetAllAlertsForLastWeekHandler)

	// Only called by external ML api
	api.GET("/:org/surge/demand_data") // Get demand data for the ml model
	api.POST("/:org/surge/alert")      // Send alert from the ml model

	// TODO: Schedule that retrieves the predicted scheduler from the model based on the given constraints (need to enforce adding settings)
	schedule := dashboard.Group("/schedule")
	schedule.GET("", s.scheduleHandler.GetScheduleHandler)              // Get Schedule for user, admin, manager
	schedule.POST("/predict", s.scheduleHandler.PredictScheduleHandler) // Refresh Schedule with the new weekly schedule

	// TODO: Campaigns Management & Insights
	campaigns := organization.Group("/campaigns")
	campaigns.GET("", s.campaignHandler.GetCampaignsInsightsHandler)       // Campaign insights
	campaigns.POST("/upload", s.campaignHandler.UploadCampaignsCSVHandler) // Upload Campaigns CSV
	campaigns.POST("/upload/items", s.campaignHandler.UploadCampaignsItemsCSVHandlers)
	campaigns.GET("/all", s.campaignHandler.GetAllCampaignsHandler)             // Get All Campaigns
	campaigns.GET("/week", s.campaignHandler.GetAllCampaignsForLastWeekHandler) // Get All Campaigns for last week

	// TODO Add connection to campaign model routes

	// TODO: Offers management to those on call and in the shift in the current shift
	offers := organization.Group("/offers")
	offers.GET("")          // Get all offers that start_time is before now
	offers.POST("/accept")  // Accept an offer
	offers.POST("/decline") // Decline an offer

	// Insights that change from a user to another about general statistics & analytics
	insights := organization.Group("/insights")
	insights.GET("", s.insightHandler.GetInsightsHandler) // Get All insights

	// Staffing Management Done by Managers and admins
	staffing := organization.Group("/staffing")
	staffing.GET("", s.staffingHandler.GetStaffingSummary)
	staffing.POST("", s.orgHandler.DelegateUser)
	staffing.POST("/upload", s.staffingHandler.UploadEmployeesCSV)

	employees := staffing.Group("/employees")
	employees.GET("", s.staffingHandler.GetAllEmployees)

	employee := employees.Group("/:id")
	employee.DELETE("/layoff", s.employeeHandler.LayoffEmployee)
	employee.GET("", s.employeeHandler.GetEmployeeDetails)

	// TODO Handle Get Employee Schedule
	employee.GET("/schedule", s.scheduleHandler.GetEmployeeScheduleHandler) // Get Employee Schedule

	employee.GET("/requests", s.employeeHandler.GetEmployeeRequests)

	// TODO: Handle offers after accepting the request
	employee.POST("/requests/approve", s.employeeHandler.ApproveRequest)
	employee.POST("/requests/decline", s.employeeHandler.DeclineRequest)

	// Preferences set by managers and employees
	preferences := organization.Group("/preferences")                           // Employees only
	preferences.GET("", s.preferencesHandler.GetCurrentEmployeePreferences)     // Get Current Employee Preferences
	preferences.POST("", s.preferencesHandler.UpdateCurrentEmployeePreferences) // Edit current preferences

	// Rules set by the organization to be used in the scheduler and reccommendors
	rules := organization.Group("/rules")                  // Rules of the organization
	rules.GET("", s.rulesHandler.GetOrganizationRules)     // Get all the rules of the organization
	rules.POST("", s.rulesHandler.UpdateOrganizationRules) // Edit the rules of the organization

	// Not found handling
	r.NoRoute(s.notFoundHandler)
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

// healthHandler godoc
// @Summary      Not found Handling
// @Description  Returns 404 not found
// @Tags         Health
// @Accept       json
// @Produce      json
// @Success      404 {object} map[string]interface{} "404 Not Found"
// @Router       any
func (s *Server) notFoundHandler(c *gin.Context) {
	c.JSON(http.StatusNotFound, gin.H{"error": "404 Not Found"})
}
