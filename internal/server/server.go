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
	port               int
	db                 database.Service
	orgHandler         *api.OrgHandler
	staffingHandler    *api.StaffingHandler
	employeeHandler    *api.EmployeeHandler
	insightHandler     *api.InsightHandler
	preferencesHandler *api.PreferencesHandler
	rulesHandler       *api.RulesHandler
	rolesHandler       *api.RolesHandler
	profileHandler     *api.ProfileHandler
	orderHandler       *api.OrderHandler
	dashboardHandler   *api.DashboardHandler
	scheduleHandler    *api.ScheduleHandler
	userStore          database.UserStore
	orgStore           database.OrgStore
	requestStore       database.RequestStore
	preferencesStore   database.PreferencesStore
	rulesStore         database.RulesStore
	rolesStore         database.RolesStore
	orderStore         database.OrderStore

	Logger *slog.Logger
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

	// Stores for database retrieval
	userStore := database.NewPostgresUserStore(dbService.GetDB(), Logger)
	orgStore := database.NewPostgresOrgStore(dbService.GetDB(), Logger)
	requestStore := database.NewPostgresRequestStore(dbService.GetDB(), Logger)
	preferencesStore := database.NewPostgresPreferencesStore(dbService.GetDB(), Logger)
	rulesStore := database.NewPostgresRulesStore(dbService.GetDB(), Logger)
	rolesStore := database.NewPostgresRolesStore(dbService.GetDB(), Logger)
	userRolesStore := database.NewPostgresUserRolesStore(dbService.GetDB(), Logger)
	operatingHoursStore := database.NewPostgresOperatingHoursStore(dbService.GetDB(), Logger)
	insightStore := &database.PostgresInsightStore{DB: dbService.GetDB(), Logger: Logger}
	orderStore := &database.PostgresOrderStore{DB: dbService.GetDB(), Logger: Logger}

	// Services
	emailService := service.NewSMTPEmailService(Logger)
	uploadService := service.NewCSVUploadService(Logger)

	// Handlers for Endpoints
	orgHandler := api.NewOrgHandler(orgStore, userStore, userRolesStore, rolesStore, emailService, Logger)
	staffingHandler := api.NewStaffingHandler(userStore, orgStore, uploadService, emailService, Logger)
	employeeHandler := api.NewEmployeeHandler(userStore, emailService, requestStore, orgStore, Logger)
	preferencesHandler := api.NewPreferencesHandler(preferencesStore, userRolesStore, userStore, rolesStore, Logger)
	rulesHandler := api.NewRulesHandler(rulesStore, operatingHoursStore, Logger)
	rolesHandler := api.NewRolesHandler(rolesStore, Logger)
	insightHandler := api.NewInsightHandler(insightStore, Logger)
	profileHandler := api.NewProfileHandler(userStore, Logger)
	orderHandler := api.NewOrderHandler(orderStore, uploadService, Logger)
	dashboardHandler := api.NewDashboardHandler(Logger)
	scheduleHandler := api.NewScheduleHandler(Logger)

	NewServer := &Server{
		port:               port,
		db:                 dbService,
		userStore:          userStore,
		orgStore:           orgStore,
		requestStore:       requestStore,
		preferencesStore:   preferencesStore,
		rulesStore:         rulesStore,
		rolesStore:         rolesStore,
		orgHandler:         orgHandler,
		staffingHandler:    staffingHandler,
		employeeHandler:    employeeHandler,
		preferencesHandler: preferencesHandler,
		rulesHandler:       rulesHandler,
		rolesHandler:       rolesHandler,
		insightHandler:     insightHandler,
		profileHandler:     profileHandler,
		orderHandler:       orderHandler,
		dashboardHandler:   dashboardHandler,
		scheduleHandler:    scheduleHandler,
		Logger:             Logger,
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
