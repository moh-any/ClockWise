package server

import (
	"log"
	"net/http"

	"BitShift/internal/api"
	"BitShift/internal/middleware"
	"BitShift/internal/service"

	jwt "github.com/appleboy/gin-jwt/v2"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func (s *Server) RegisterRoutes() http.Handler {
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"},
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
	r.POST("/register-org", orgHandler.RegisterOrganization)

	// --- Protected Routes ---
	auth := r.Group("/auth")
	auth.Use(authMiddleware.MiddlewareFunc())
	{
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
	}

	return r
}

func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, s.db.Health())
}
