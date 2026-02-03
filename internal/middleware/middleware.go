package middleware

import (
	"os"
	"time"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/gin-gonic/gin"
	gojwt "github.com/golang-jwt/jwt/v5"
	"github.com/google/uuid"
)

var identityKey = "user"

type Login struct {
	Email    string `form:"email" json:"email" binding:"required"`
	Password string `form:"password" json:"password" binding:"required"`
}

func NewAuthMiddleware(userStore database.UserStore) (*jwt.GinJWTMiddleware, error) {
	return jwt.New(&jwt.GinJWTMiddleware{
		Realm:           "ClockWise",
		Key:             []byte(os.Getenv("JWT_SECRET")),
		Timeout:         time.Hour,
		MaxRefresh:      time.Hour,
		IdentityKey:     identityKey,
		PayloadFunc:     payloadFunc(),
		IdentityHandler: identityHandler(),
		Authenticator:   authenticator(userStore),
		Authorizer:      authorizator(),
		Unauthorized:    unauthorized(),
		TokenLookup:     "header: Authorization, query: token, cookie: access_token",
		TokenHeadName:   "Bearer",
		TimeFunc:        time.Now,
	})
}

func payloadFunc() func(data interface{}) gojwt.MapClaims {
	return func(data interface{}) gojwt.MapClaims {
		if v, ok := data.(*database.User); ok {
			return gojwt.MapClaims{
				"id":              v.ID.String(),
				"full_name":       v.FullName,
				"email":           v.Email,
				"user_role":       v.UserRole,
				"organization_id": v.OrganizationID.String(),
			}
		}
		return gojwt.MapClaims{}
	}
}

func identityHandler() func(c *gin.Context) interface{} {
	return func(c *gin.Context) interface{} {
		claims := jwt.ExtractClaims(c)
		return &database.User{
			ID:             uuid.MustParse(claims["id"].(string)),
			FullName:       claims["full_name"].(string),
			Email:          claims["email"].(string),
			UserRole:       claims["user_role"].(string),
			OrganizationID: uuid.MustParse(claims["organization_id"].(string)),
		}
	}
}

func authenticator(userStore database.UserStore) func(c *gin.Context) (interface{}, error) {
	return func(c *gin.Context) (interface{}, error) {
		var loginVals Login
		if err := c.ShouldBind(&loginVals); err != nil {
			return "", jwt.ErrMissingLoginValues
		}
		email := loginVals.Email
		password := loginVals.Password

		user, err := userStore.GetUserByEmail(email)
		if err != nil {
			return nil, jwt.ErrFailedAuthentication
		}

		match, err := user.PasswordHash.Matches(password)
		if err != nil || !match {
			return nil, jwt.ErrFailedAuthentication
		}

		return user, nil
	}
}

func authorizator() func(c *gin.Context, data any) bool {
	return func(c *gin.Context, data any) bool {
		if _, ok := data.(*database.User); ok {
			return true
		}
		return false
	}
}

func unauthorized() func(c *gin.Context, code int, message string) {
	return func(c *gin.Context, code int, message string) {
		c.JSON(code, gin.H{
			"code":    code,
			"message": message,
		})
	}
}
