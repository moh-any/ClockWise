package server

import (
	"log"
	"net/http"

	"BitShift/internal/api"
	"BitShift/internal/middleware"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/gin-contrib/cors"
	"github.com/gin-gonic/gin"
)

func (s *Server) RegisterRoutes() http.Handler {
	r := gin.Default()

	r.Use(cors.New(cors.Config{
		AllowOrigins:     []string{"http://localhost:5173"}, // Add your frontend URL
		AllowMethods:     []string{"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"},
		AllowHeaders:     []string{"Accept", "Authorization", "Content-Type"},
		AllowCredentials: true, // Enable cookies/auth
	}))

	r.GET("/", s.HelloWorldHandler)

	r.GET("/health", s.healthHandler)

	// Auth Middleware
	authMiddleware, err := middleware.NewAuthMiddleware(s.userStore)
	if err != nil {
		log.Fatal("JWT Error:" + err.Error())
	}

	// Init auth middleware
	if err := authMiddleware.MiddlewareInit(); err != nil {
		log.Fatal("authMiddleware.MiddlewareInit() Error:" + err.Error())
	}

	userHandler := api.NewUserHandler(s.userStore)

	// Public routes
	r.POST("/login", authMiddleware.LoginHandler)
	r.POST("/register", userHandler.Register) // Manager Only 

	// Auth routes
	auth := r.Group("/auth")
	auth.GET("/refresh_token", authMiddleware.RefreshHandler)
	auth.POST("/logout", authMiddleware.LogoutHandler)

	auth.Use(authMiddleware.MiddlewareFunc())
	{
		auth.GET("/me", func(c *gin.Context) {
			claims := jwt.ExtractClaims(c)
			user, _ := c.Get("user")
			c.JSON(200, gin.H{
				"userID":   claims["id"],
				"username": claims["username"],
				"email":    claims["email"],
				"role":     claims["user_role"],
				"userData": user,
			})
	})
	}
	

	// Role management
	dashboard := r.Group("/dashboard")
	dashboard.GET("")

	// Organization Admin  
	
	

	return r
}

func (s *Server) HelloWorldHandler(c *gin.Context) {
	resp := make(map[string]string)
	resp["message"] = "Hello World"

	c.JSON(http.StatusOK, resp)
}

func (s *Server) healthHandler(c *gin.Context) {
	c.JSON(http.StatusOK, s.db.Health())
}
