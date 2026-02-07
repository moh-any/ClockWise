package middleware

import (
	"net/http"
	"os"
	"time"

	jwt "github.com/appleboy/gin-jwt/v3"
	"github.com/appleboy/gin-jwt/v3/core"
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
		Realm:             "ClockWise",
		Key:               []byte(os.Getenv("JWT_SECRET")),
		Timeout:           time.Minute * 45,
		MaxRefresh:        time.Hour * 24 * 7,
		IdentityKey:       identityKey,
		PayloadFunc:       payloadFunc(),
		IdentityHandler:   identityHandler(),
		Authenticator:     authenticator(userStore),
		Authorizer:        authorizator(),
		Unauthorized:      unauthorized(),
		TokenLookup:       "header: Authorization, query: token, cookie: access_token",
		TokenHeadName:     "Bearer",
		TimeFunc:          time.Now,
		SendAuthorization: true,
		RefreshResponse:   refreshResponse(),
	})
}

func payloadFunc() func(data any) gojwt.MapClaims {
	return func(data any) gojwt.MapClaims {
		if v, ok := data.(*database.User); ok {
			return gojwt.MapClaims{
				"id":                       v.ID.String(),
				"full_name":                v.FullName,
				"email":                    v.Email,
				"user_role":                v.UserRole,
				"organization_id":          v.OrganizationID.String(),
				"salary_per_hour":          v.SalaryPerHour,
				"max_hours_per_week":       v.MaxHoursPerWeek,
				"preferred_hours_per_week": v.PreferredHoursPerWeek,
				"max_consec_slots":         v.MaxConsecSlots,
				"on_call":                  v.OnCall,
			}
		}
		return gojwt.MapClaims{}
	}
}

func identityHandler() func(c *gin.Context) any {
	return func(c *gin.Context) any {
		claims := jwt.ExtractClaims(c)

		// Extract optional float64 pointer
		var salaryPerHour *float64
		if salary, ok := claims["salary_per_hour"]; ok && salary != nil {
			if s, ok := salary.(float64); ok {
				salaryPerHour = &s
			}
		}

		// Extract optional int pointers
		var maxHoursPerWeek *int
		if v, ok := claims["max_hours_per_week"]; ok && v != nil {
			if f, ok := v.(int); ok {
				i := int(f)
				maxHoursPerWeek = &i
			}
		}

		var preferredHoursPerWeek *int
		if v, ok := claims["preferred_hours_per_week"]; ok && v != nil {
			if f, ok := v.(int); ok {
				i := int(f)
				preferredHoursPerWeek = &i
			}
		}

		var maxConsecSlots *int
		if v, ok := claims["max_consec_slots"]; ok && v != nil {
			if f, ok := v.(int); ok {
				i := int(f)
				maxConsecSlots = &i
			}
		}

		var OnCall *bool
		if v, ok := claims["on_call"]; ok && v != nil {
			if f, ok := v.(bool); ok {
				i := bool(f)
				OnCall = &i
			}
		}
		return &database.User{
			ID:                    uuid.MustParse(claims["id"].(string)),
			FullName:              claims["full_name"].(string),
			Email:                 claims["email"].(string),
			UserRole:              claims["user_role"].(string),
			OrganizationID:        uuid.MustParse(claims["organization_id"].(string)),
			SalaryPerHour:         salaryPerHour,
			MaxHoursPerWeek:       maxHoursPerWeek,
			PreferredHoursPerWeek: preferredHoursPerWeek,
			MaxConsecSlots:        maxConsecSlots,
			OnCall:                OnCall,
		}
	}
}

func authenticator(userStore database.UserStore) func(c *gin.Context) (any, error) {
	return func(c *gin.Context) (any, error) {
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
			"message": message,
		})
	}
}

func refreshResponse() func(c *gin.Context, token *core.Token) {
	return func(c *gin.Context, token *core.Token) {
		c.JSON(http.StatusOK, gin.H{
			"access_token":  token.AccessToken,
			"refresh_token": token.RefreshToken,
			"expires_at":    token.ExpiresAt,
		})
	}
}

// ValidateOrgAccess validates that the :org URL parameter matches the user's organization ID.
// Returns the user if valid, or sends an error response and returns nil if invalid.
func ValidateOrgAccess(c *gin.Context) *database.User {
	currentUser, exists := c.Get("user")
	if !exists {
		c.JSON(401, gin.H{"error": "Unauthorized"})
		return nil
	}
	user := currentUser.(*database.User)

	orgParam := c.Param("org")
	if orgParam == "" {
		// No org param in route, skip validation
		return user
	}

	orgID, err := uuid.Parse(orgParam)
	if err != nil {
		c.JSON(400, gin.H{"error": "Invalid organization ID"})
		return nil
	}

	if orgID != user.OrganizationID {
		c.JSON(403, gin.H{"error": "Access denied: You can only access your own organization"})
		return nil
	}

	return user
}
