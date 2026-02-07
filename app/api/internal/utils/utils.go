package utils

import (
	"crypto/rand"
	"encoding/hex"
)

// GenerateRandomPassword creates a secure random hex string
func GenerateRandomPassword(length int) (string, error) {
	bytes := make([]byte, length)
	if _, err := rand.Read(bytes); err != nil {
		return "", err
	}
	return hex.EncodeToString(bytes), nil
}
