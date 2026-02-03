package server

import (
	"fmt"
	"net/http"
	"os"
	"strconv"
	"time"

	_ "github.com/joho/godotenv/autoload"

	"BitShift/internal/database"
	"BitShift/migrations"
)

type Server struct {
	port      int
	db        database.Service
	userStore database.UserStore
	orgStore  database.OrgStore
}

func NewServer() *http.Server {
	port, _ := strconv.Atoi(os.Getenv("PORT"))

	// Create database service
	dbService := database.New()

	// Run migrations on startup
	err := database.MigrateFS(dbService.GetDB(), ".", migrations.FS)
	if err != nil {
		panic(fmt.Sprintf("failed to run database migrations: %s", err))
	}

	userStore := database.NewPostgresUserStore(dbService.GetDB())
	orgStore := database.NewPostgresOrgStore(dbService.GetDB())

	NewServer := &Server{
		port:      port,
		db:        dbService,
		userStore: userStore,
		orgStore:  orgStore,
	}

	// Declare Server config
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", NewServer.port),
		Handler:      NewServer.RegisterRoutes(),
		IdleTimeout:  time.Minute,
		ReadTimeout:  10 * time.Second,
		WriteTimeout: 30 * time.Second,
	}

	return server
}
