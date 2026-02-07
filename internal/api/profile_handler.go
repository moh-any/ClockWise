package api

import (
	"log/slog"
	"net/http"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
)

type ProfileHandler struct {
	UserStore database.UserStore
	Logger    *slog.Logger
}

func NewProfileHandler(userStore database.UserStore, Logger *slog.Logger) *ProfileHandler {
	return &ProfileHandler{
		UserStore: userStore,
		Logger:    Logger,
	}
}

type ChangePasswordRequest struct {
	OldPassword string `json:"old_password" binding:"required"`
	NewPassword string `json:"new_password" binding:"required,min=8"`
}

// GetProfileHandler godoc
// @Summary      Get user profile
// @Description  Returns the current user's profile information
// @Tags         Profile
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Success      200 {object} database.UserProfile "User profile"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      404 {object} map[string]string "Profile not found"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /profile [get]
func (ph *ProfileHandler) GetProfileHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	ph.Logger.Info("getting profile for user", "user_id", user.ID)

	profile, err := ph.UserStore.GetProfile(user.ID)
	if err != nil {
		ph.Logger.Error("failed to get profile", "error", err, "user_id", user.ID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Profile not found"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Profile retrieved successfully",
		"data":    profile,
	})
}

// ChangePasswordHandler godoc
// @Summary      Change password
// @Description  Changes the current user's password
// @Tags         Profile
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        request body ChangePasswordRequest true "Password change request"
// @Success      200 {object} map[string]string "Password changed successfully"
// @Failure      400 {object} map[string]string "Invalid request body"
// @Failure      401 {object} map[string]string "Unauthorized or incorrect old password"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /profile/password [put]
func (ph *ProfileHandler) ChangePasswordHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	var req ChangePasswordRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		ph.Logger.Warn("invalid change password request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request body"})
		return
	}

	ph.Logger.Info("changing password for user", "user_id", user.ID)

	// Get the full user to verify old password
	fullUser, err := ph.UserStore.GetUserByID(user.ID)
	if err != nil {
		ph.Logger.Error("failed to get user", "error", err, "user_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify user"})
		return
	}

	// Verify old password
	match, err := fullUser.PasswordHash.Matches(req.OldPassword)
	if err != nil || !match {
		ph.Logger.Warn("incorrect old password", "user_id", user.ID)
		c.JSON(http.StatusUnauthorized, gin.H{"error": "Incorrect old password"})
		return
	}

	// Hash the new password
	newHash, err := database.Hash(req.NewPassword)
	if err != nil {
		ph.Logger.Error("failed to hash new password", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to process new password"})
		return
	}

	// Update the password
	err = ph.UserStore.ChangePassword(user.ID, newHash)
	if err != nil {
		ph.Logger.Error("failed to change password", "error", err, "user_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to change password"})
		return
	}

	ph.Logger.Info("password changed successfully", "user_id", user.ID)
	c.JSON(http.StatusOK, gin.H{"message": "Password changed successfully"})
}
