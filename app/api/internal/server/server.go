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
	"github.com/clockwise/clockwise/backend/internal/cache"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/clockwise/clockwise/backend/migrations"
)

type Server struct {
	port int
	db   database.Service

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
	campaignHandler    *api.CampaignHandler
	alertHandler       *api.AlertHandler

	userStore        database.UserStore
	orgStore         database.OrgStore
	requestStore     database.RequestStore
	preferencesStore database.PreferencesStore
	rulesStore       database.RulesStore
	rolesStore       database.RolesStore
	orderStore       database.OrderStore
	campaignStore    database.CampaignStore
	demandStore      database.DemandStore
	alertStore       database.AlertStore

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

	// Initialize Redis cache service with graceful fallback
	redisAddr := os.Getenv("REDIS_ADDR")
	redisPwd := os.Getenv("REDIS_PASSWORD")

	cacheService, err := cache.NewCacheService(redisAddr, redisPwd)
	if err != nil {
		Logger.Warn("Redis unavailable, running without cache", "error", err, "addr", redisAddr)
		cacheService = nil
	} else {
		Logger.Info("Redis cache initialized successfully", "addr", redisAddr)
	}

	// Create base stores (PostgreSQL implementations)
	baseUserStore := database.NewPostgresUserStore(dbService.GetDB(), Logger)
	baseOrgStore := database.NewPostgresOrgStore(dbService.GetDB(), Logger)
	baseRequestStore := database.NewPostgresRequestStore(dbService.GetDB(), Logger)
	basePreferencesStore := database.NewPostgresPreferencesStore(dbService.GetDB(), Logger)
	baseRulesStore := database.NewPostgresRulesStore(dbService.GetDB(), Logger)
	baseRolesStore := database.NewPostgresRolesStore(dbService.GetDB(), Logger)
	baseUserRolesStore := database.NewPostgresUserRolesStore(dbService.GetDB(), Logger)
	baseOperatingHoursStore := database.NewPostgresOperatingHoursStore(dbService.GetDB(), Logger)
	baseInsightStore := &database.PostgresInsightStore{DB: dbService.GetDB(), Logger: Logger}
	baseOrderStore := &database.PostgresOrderStore{DB: dbService.GetDB(), Logger: Logger}
	baseCampaignStore := database.NewPostgresCampaignStore(dbService.GetDB(), Logger)
	baseDemandStore := database.NewPostgresDemandStore(dbService.GetDB(), Logger)
	baseAlertStore := database.NewPostgresAlertStore(dbService.GetDB(), Logger)

	// Wrap stores with caching if Redis is available
	var userStore database.UserStore
	var orgStore database.OrgStore
	var requestStore database.RequestStore
	var preferencesStore database.PreferencesStore
	var rulesStore database.RulesStore
	var rolesStore database.RolesStore
	var userRolesStore database.UserRolesStore
	var operatingHoursStore database.OperatingHoursStore
	var insightStore database.InsightStore
	var orderStore database.OrderStore
	var campaignStore database.CampaignStore
	var demandStore database.DemandStore
	var alertStore database.AlertStore

	if cacheService != nil {
		// Wrap with caching layer
		userStore = cache.NewCachedUserStore(baseUserStore, cacheService)
		orgStore = cache.NewCachedOrgStore(baseOrgStore, cacheService)
		requestStore = cache.NewCachedRequestStore(baseRequestStore, cacheService)
		preferencesStore = cache.NewCachedPreferencesStore(basePreferencesStore, cacheService)
		rulesStore = cache.NewCachedRulesStore(baseRulesStore, cacheService)
		rolesStore = cache.NewCachedRolesStore(baseRolesStore, cacheService)
		userRolesStore = cache.NewCachedUserRolesStore(baseUserRolesStore, cacheService)
		operatingHoursStore = cache.NewCachedOperatingHoursStore(baseOperatingHoursStore, cacheService)
		insightStore = cache.NewCachedInsightStore(baseInsightStore, cacheService)
		orderStore = cache.NewCachedOrderStore(baseOrderStore, cacheService)
		campaignStore = cache.NewCachedCampaignStore(baseCampaignStore, cacheService)
		demandStore = cache.NewCachedDemandStore(baseDemandStore, cacheService)
		alertStore = cache.NewCachedAlertStore(baseAlertStore, cacheService)
		Logger.Info("All stores wrapped with Redis caching layer")
	} else {
		// Use base stores directly (no caching)
		userStore = baseUserStore
		orgStore = baseOrgStore
		requestStore = baseRequestStore
		preferencesStore = basePreferencesStore
		rulesStore = baseRulesStore
		rolesStore = baseRolesStore
		userRolesStore = baseUserRolesStore
		operatingHoursStore = baseOperatingHoursStore
		insightStore = baseInsightStore
		orderStore = baseOrderStore
		campaignStore = baseCampaignStore
		demandStore = baseDemandStore
		alertStore = baseAlertStore
		Logger.Warn("Running without cache layer - all requests will hit PostgreSQL directly")
	}

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
	dashboardHandler := api.NewDashboardHandler(
		orgStore,
		rulesStore,
		operatingHoursStore,
		orderStore,
		campaignStore,
		demandStore,
		Logger,
	)
	scheduleHandler := api.NewScheduleHandler(Logger)
	campaignHandler := api.NewCampaignHandler(campaignStore, uploadService, Logger)
	alertHandler := api.NewAlertHandler(alertStore, Logger)

	NewServer := &Server{
		port: port,
		db:   dbService,

		userStore:        userStore,
		orgStore:         orgStore,
		requestStore:     requestStore,
		preferencesStore: preferencesStore,
		rulesStore:       rulesStore,
		rolesStore:       rolesStore,
		campaignStore:    campaignStore,
		demandStore:      demandStore,
		alertStore:       alertStore,

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
		campaignHandler:    campaignHandler,
		alertHandler:       alertHandler,

		Logger: Logger,
	}

	// Declare Server config
	server := &http.Server{
		Addr:         fmt.Sprintf(":%d", NewServer.port),
		Handler:      NewServer.RegisterRoutes(),
		IdleTimeout:  time.Minute,
		ReadTimeout:  20 * time.Second,
		WriteTimeout: 60 * time.Second,
	}

	return server
}
