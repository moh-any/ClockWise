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
	port            int
	db              database.Service
	orgHandler      *api.OrgHandler
	staffingHandler *api.StaffingHandler
	employeeHandler *api.EmployeeHandler
	insightHandler  *api.InsightHandler
	userStore       database.UserStore
	orgStore        database.OrgStore
	requestStore    database.RequestStore
	Logger          *slog.Logger
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
	requestStore := database.NewPostgresRequestStore(dbService.GetDB(), Logger)
	insightStore := &database.PostgresInsightStore{DB: dbService.GetDB()}

	emailService := service.NewSMTPEmailService(Logger)
	uploadService := service.NewCSVUploadService(Logger)

	orgHandler := api.NewOrgHandler(orgStore, userStore, emailService, Logger)
	staffingHandler := api.NewStaffingHandler(userStore, orgStore, uploadService, emailService, Logger)
	employeeHandler := api.NewEmployeeHandler(userStore, requestStore, Logger)
	insightHandler := api.NewInsightHandler(insightStore,Logger) 

	NewServer := &Server{
		port:            port,
		db:              dbService,
		userStore:       userStore,
		orgStore:        orgStore,
		requestStore:    requestStore,
		orgHandler:      orgHandler,
		staffingHandler: staffingHandler,
		employeeHandler: employeeHandler,
		insightHandler:  insightHandler,
		Logger:          Logger,
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
