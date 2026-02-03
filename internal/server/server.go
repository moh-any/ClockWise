package server

import (
	"fmt"
	"log/slog"
	"net/http"
	"os"
	"strconv"
	"time"

	_ "github.com/joho/godotenv/autoload"

	"github.com/clockwise/clockwise/backend/internal/api"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/clockwise/clockwise/backend/migrations"
)

type Server struct {
	port        int
	db          database.Service
	orgHandler  *api.OrgHandler
	userHandler *api.UserHandler
	userStore   database.UserStore
	orgStore    database.OrgStore
	Logger      *slog.Logger
}

func NewServer(Logger *slog.Logger) *http.Server {
	port, _ := strconv.Atoi(os.Getenv("PORT"))

	// Create database service
	dbService := database.New()

	// Run migrations on startup
	err := database.MigrateFS(dbService.GetDB(), ".", migrations.FS)

	if err != nil {
		panic(fmt.Sprintf("failed to run database migrations: %s", err))
	}

	userStore := database.NewPostgresUserStore(dbService.GetDB(), Logger)
	orgStore := database.NewPostgresOrgStore(dbService.GetDB(), Logger)

	emailService := service.NewSMTPEmailService(Logger)

	orgHandler := api.NewOrgHandler(orgStore, userStore, emailService, Logger)
	userHandler := api.NewUserHandler(userStore, Logger)

	NewServer := &Server{
		port:        port,
		db:          dbService,
		userStore:   userStore,
		orgStore:    orgStore,
		orgHandler:  orgHandler,
		userHandler: userHandler,
		Logger:      Logger,
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
