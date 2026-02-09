package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"log/slog"
	"net/http"
	"os"
	"strings"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type ScheduleHandler struct {
	UserStore           database.UserStore
	ScheduleStore       database.ScheduleStore
	OrgStore            database.OrgStore
	RulesStore          database.RulesStore
	UserRolesStore      database.UserRolesStore
	OperatingHoursStore database.OperatingHoursStore
	OrderStore          database.OrderStore
	CampaignStore       database.CampaignStore
	DemandStore         database.DemandStore
	RoleStore           database.RolesStore
	PreferenceStore     database.PreferencesStore
	Logger              *slog.Logger
}

type SchedulePredictRequest struct {
	Place         Place         `json:"place"`
	ScheduleInput ScheduleInput `json:"schedule_input"`
}

type ScheduleInput struct {
	Roles               []database.OrganizationRole `json:"roles"`
	Employees           []Employee                  `json:"employees"`
	SchedulerConfig     SchedulerConfig             `json:"scheduler_config"`
	DemandPredictions   []database.PredictionDay    `json:"demand_predictions"`
	PredictionStartDate time.Time                   `json:"prediction_start_date"`
}

type Employee struct {
	EmployeeID            uuid.UUID                `json:"employee_id"`
	RoleNames             []string                 `json:"role_ids"`
	AvailableDays         []string                 `json:"available_days"`
	Preferred_Days        []string                 `json:"preferred_days"`
	AvailableHours        map[string]EmployeeHours `json:"available_hours"`
	PreferredHours        map[string]EmployeeHours `json:"preferred_hours"`
	HourlyWage            *float64                 `json:"hourly_wage"`
	MaxHoursPerWeek       *float64                 `json:"max_hours_per_week"`
	MaxConsecSlots        *int                     `json:"max_consec_slots"`
	PreferredHoursPerWeek *float64                 `json:"pref_hours"`
}

type SchedulerConfig struct {
	SlotLenHour         *float64 `json:"slot_len_hour"`
	MinRestSlots        *int     `json:"min_rest_slots"`
	MinShiftLengthSlots *int     `json:"min_shift_length_slots"`
	MeetAllDemands      *bool    `json:"meet_all_demand"`
}

type EmployeeHours struct {
	From string `json:"from"`
	To   string `json:"to"`
}

type GenerateScheduleResponse struct {
	ScheduleOutput     map[string][]map[string][]string `json:"schedule_output"`
	ScheduleStatus     string                           `json:"schedule_status"`
	ScheduleMessage    string                           `json:"schedule_message"`
	ObjectiveValue     *float64                         `json:"objective_value"`
	ManagementInsights ManagementInsights               `json:"management_insights"`
}

type ManagementInsights struct {
	HasSolution           bool             `json:"has_solution"`
	PeakPeriods           []map[string]any `json:"peak_periods"`
	CapacityAnalysis      map[string]any   `json:"capacity_analysis,omitempty"`
	EmployeeUtilization   []map[string]any `json:"employee_utilization,omitempty"`
	RoleDemand            map[string]any   `json:"role_demand,omitempty"`
	HiringRecommendations []map[string]any `json:"hiring_recommendations,omitempty"`
	CoverageGaps          []map[string]any `json:"coverage_gaps,omitempty"`
	CostAnalysis          map[string]any   `json:"cost_analysis,omitempty"`
	WorkloadDistribution  map[string]any   `json:"workload_distribution,omitempty"`
	FeasibilityAnalysis   []map[string]any `json:"feasibility_analysis,omitempty"`
}

func NewScheduleHandler(userStore database.UserStore, scheduleStore database.ScheduleStore, logger *slog.Logger,
	orgStore database.OrgStore,
	rulesStore database.RulesStore,
	userRolesStore database.UserRolesStore,
	operatingHoursStore database.OperatingHoursStore,
	orderStore database.OrderStore,
	campaignStore database.CampaignStore,
	demandStore database.DemandStore,
	roleStore database.RolesStore,
	preferenceStore database.PreferencesStore,
) *ScheduleHandler {
	return &ScheduleHandler{
		UserStore:           userStore,
		ScheduleStore:       scheduleStore,
		OrgStore:            orgStore,
		RulesStore:          rulesStore,
		UserRolesStore:      userRolesStore,
		OperatingHoursStore: operatingHoursStore,
		OrderStore:          orderStore,
		CampaignStore:       campaignStore,
		DemandStore:         demandStore,
		RoleStore:           roleStore,
		PreferenceStore:     preferenceStore,
		Logger:              logger,
	}
}

func (sh *ScheduleHandler) PredictScheduleHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	sh.Logger.Info("requesting schedule from external api", "org_id", user.OrganizationID)

	organization, err := sh.OrgStore.GetOrganizationByID(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization details"})
		return
	}

	organization_rules, err := sh.RulesStore.GetRulesByOrganizationID(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization rules details"})
		return
	}

	operating_hours, err := sh.OperatingHoursStore.GetOperatingHours(user.OrganizationID)

	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization operating hours details"})
		return
	}

	Place := Place{
		ID:                 organization.ID,
		Name:               organization.Name,
		Type:               organization.Type,
		Latitude:           organization.Location.Latitude,
		Longitude:          organization.Location.Longitude,
		WaitingTime:        organization_rules.WaitingTime,
		ReceivingPhone:     organization_rules.ReceivingPhone,
		Delivery:           organization_rules.Delivery,
		OpeningHours:       operating_hours,
		FixedShifts:        organization_rules.FixedShifts,
		NumberShiftsPerDay: organization_rules.NumberOfShiftsPerDay,
		ShiftTimes:         organization_rules.ShiftTimes,
		Rating:             organization.Rating,
		AcceptingOrders:    organization_rules.AcceptingOrders,
	}

	schedulerConfig := SchedulerConfig{
		MinRestSlots:        &organization_rules.MinRestSlots,
		SlotLenHour:         &organization_rules.SlotLenHour,
		MinShiftLengthSlots: &organization_rules.MinShiftLengthSlots,
		MeetAllDemands:      &organization_rules.MeetAllDemand,
	}

	demands, err := sh.DemandStore.GetLatestDemandHeatMap(organization.ID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization latest demands, please generate demand first"})
		return
	}

	roles, err := sh.RoleStore.GetRolesByOrganizationID(user.OrganizationID)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get organization latest demands, please get roles from organization"})
		return
	}

	employees, err := sh.UserStore.GetUsersByOrganization(user.OrganizationID)

	if err != nil {
		sh.Logger.Debug("failed to retrieve employees for organization", "err", err.Error())
		c.JSON(http.StatusInternalServerError, gin.H{"error": "failed to get employees from organization"})
		return
	}

	var Employees []Employee

	for _, employee := range employees {
		// Exclude Admin
		if employee.UserRole == "admin" {
			continue
		}

		// Get preferences for this employee
		prefs, err := sh.PreferenceStore.GetPreferencesByEmployeeID(employee.ID)
		sh.Logger.Info("got prefs for employee", "employee_id", employee.ID)
		if err != nil {
			sh.Logger.Warn("failed to get preferences for employee", "employee_id", employee.ID, "error", err)
			// Continue without preferences for this employee
			prefs = []database.EmployeePreference{}
		}

		// User Roles
		userRoles, err := sh.UserRolesStore.GetUserRoles(employee.ID, user.OrganizationID)
		if err != nil {
			sh.Logger.Info("failed to get user roles for employees", "employee_id", employee.ID, "error", err)
			continue
		}

		if len(userRoles) == 0 {
			sh.Logger.Error("no user roles found", "user", employee.ID)
		}

		// Build available/preferred days and hours maps
		availableDays := []string{}
		preferredDays := []string{}
		availableHours := make(map[string]EmployeeHours)
		preferredHours := make(map[string]EmployeeHours)

		for _, pref := range prefs {
			dayLower := pref.Day

			// Available hours
			if pref.AvailableStartTime != nil && pref.AvailableEndTime != nil {
				availableDays = append(availableDays, dayLower)
				availableHours[dayLower] = EmployeeHours{
					From: *pref.AvailableStartTime,
					To:   *pref.AvailableEndTime,
				}
			}

			// Preferred hours
			if pref.PreferredStartTime != nil && pref.PreferredEndTime != nil {
				preferredDays = append(preferredDays, dayLower)
				preferredHours[dayLower] = EmployeeHours{
					From: *pref.PreferredStartTime,
					To:   *pref.PreferredEndTime,
				}
			}
		}

		// Convert hours per week from int to float64 if needed
		var maxHoursPerWeek *float64
		if employee.MaxHoursPerWeek != nil {
			val := float64(*employee.MaxHoursPerWeek)
			maxHoursPerWeek = &val
		}

		var preferredHoursPerWeek *float64
		if employee.PreferredHoursPerWeek != nil {
			val := float64(*employee.PreferredHoursPerWeek)
			preferredHoursPerWeek = &val
		}

		// Build Employee struct
		emp := Employee{
			EmployeeID:            employee.ID,
			RoleNames:             userRoles,
			AvailableDays:         availableDays,
			Preferred_Days:        preferredDays,
			AvailableHours:        availableHours,
			PreferredHours:        preferredHours,
			HourlyWage:            employee.SalaryPerHour,
			MaxHoursPerWeek:       maxHoursPerWeek,
			MaxConsecSlots:        employee.MaxConsecSlots,
			PreferredHoursPerWeek: preferredHoursPerWeek,
		}

		Employees = append(Employees, emp)
	}

	scheduleInput := ScheduleInput{
		SchedulerConfig:     schedulerConfig,
		DemandPredictions:   demands.Days,
		PredictionStartDate: time.Now(),
		Roles:               roles,
		Employees:           Employees,
	}

	request := SchedulePredictRequest{
		Place:         Place,
		ScheduleInput: scheduleInput,
	}

	// Call external ML API
	mlURL := os.Getenv("ML_URL")
	if mlURL == "" {
		mlURL = "http://cw-ml-service:8000"
	}

	// Make an api call to the demand model http://cw-ml-service:8000/predict/schedule
	client := &http.Client{}

	// JSON
	jsonPayload, err := json.Marshal(request)
	if err != nil {
		sh.Logger.Error("failed to marshal request", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to prepare request payload"})
		return
	}

	sh.Logger.Debug("json body in request", "json", string(jsonPayload))

	req, err := http.NewRequest("POST", fmt.Sprintf("%v%v", os.Getenv("ML_URL"), "/predict/schedule"), bytes.NewBuffer(jsonPayload))
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create request"})
		return
	}

	req.Header.Add("Content-Type", "application/json")

	resp, err := client.Do(req)
	if err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": err.Error()})
		return
	}
	defer resp.Body.Close()

	sh.Logger.Info("request to ML API", "req", jsonPayload)
	// Validate response status code first
	if resp.StatusCode != http.StatusOK {
		sh.Logger.Error("ML API returned error", "status_code", resp.StatusCode)
		body, _ := io.ReadAll(resp.Body)
		c.JSON(resp.StatusCode, gin.H{"error": "ML service returned an error", "details": string(body)})
		return
	}

	// Process Response with custom UnmarshalJSON for date parsing
	var scheduleResponse GenerateScheduleResponse
	decoder := json.NewDecoder(resp.Body)

	if err := decoder.Decode(&scheduleResponse); err != nil {
		sh.Logger.Error("failed to decode ML response", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to decode ML response"})
		return
	}

	// Store in Schedule Store
	err = sh.storeScheduleOutput(user.OrganizationID, scheduleResponse.ScheduleOutput)
	if err != nil {
		sh.Logger.Error("failed to store schedule", "error", err)
		c.AbortWithStatusJSON(http.StatusInternalServerError, gin.H{"error": "error storing schedule"})
		return
	}
	
	for day, timeSlots := range scheduleResponse.ScheduleOutput {
		for i, slotMap := range timeSlots {
			for timeRange := range slotMap {
				var names []string
				for _, empID := range slotMap[timeRange] {
					employeeID, _ := uuid.Parse(empID)
					emp, err := sh.UserStore.GetUserByID(employeeID)
					if err != nil {
						sh.Logger.Error("failed to retrieve user id", "user", emp)
						continue
					}
					names = append(names, emp.FullName)
				}
				scheduleResponse.ScheduleOutput[day][i][timeRange] = names
			}
		}
	}
	// Return the successfully decoded response
	c.JSON(http.StatusOK, gin.H{
		"message":             "schedule prediction retrieved successfully from API",
		"schedule_status":     scheduleResponse.ScheduleStatus,
		"schedule_message":    scheduleResponse.ScheduleMessage,
		"management_insights": scheduleResponse.ManagementInsights,
		"objective_value":     scheduleResponse.ObjectiveValue,
		"schedule_output":     scheduleResponse.ScheduleOutput,
	})

}

// return schedule for manager and employee
func (sh *ScheduleHandler) GetCurrentUserScheduleHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole == "admin" {
		sh.Logger.Warn("forbidden schedule access", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied. Admin don't have schedules"})
		return
	}

	// Get schedule for the current user
	schedules, err := sh.ScheduleStore.GetScheduleForEmployeeForSevenDays(user.OrganizationID, user.ID)
	if err != nil {
		sh.Logger.Error("failed to get current user schedule", "error", err, "user_id", user.ID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve schedule"})
		return
	}

	sh.Logger.Info("current user schedule retrieved", "user_id", user.ID, "count", len(schedules))
	c.JSON(http.StatusOK, gin.H{
		"message": "Schedule retrieved successfully",
		"data":    schedules,
	})
}

// If admin or manager return full schedule for all users, if employee do not allow to access
func (sh *ScheduleHandler) GetScheduleHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	// Only admin and manager can view full organization schedule
	if user.UserRole != "admin" && user.UserRole != "manager" {
		sh.Logger.Warn("forbidden schedule access", "user_id", user.ID, "role", user.UserRole)
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied. Only admins and managers can view full schedules"})
		return
	}

	// Get full schedule for the organization
	schedules, err := sh.ScheduleStore.GetFullScheduleForSevenDays(user.OrganizationID)
	if err != nil {
		sh.Logger.Error("failed to get organization schedule", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve schedule"})
		return
	}

	sh.Logger.Info("organization schedule retrieved", "org_id", user.OrganizationID, "count", len(schedules))
	c.JSON(http.StatusOK, gin.H{
		"message": "Schedule retrieved successfully",
		"data":    schedules,
	})
}

// Manager or Admin access employee schedule
func (sh *ScheduleHandler) GetEmployeeScheduleHandler(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	employeeIDStr := c.Param("id")
	employeeID, err := uuid.Parse(employeeIDStr)
	if err != nil {
		sh.Logger.Warn("invalid employee ID", "id", employeeIDStr)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid employee ID"})
		return
	}

	// Verify employee exists and belongs to same organization
	employee, err := sh.UserStore.GetUserByID(employeeID)
	if err != nil {
		sh.Logger.Error("failed to get employee", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusNotFound, gin.H{"error": "Employee not found"})
		return
	}

	if employee.OrganizationID != user.OrganizationID {
		sh.Logger.Warn("attempted to access employee from different organization")
		c.JSON(http.StatusForbidden, gin.H{"error": "Access denied"})
		return
	}

	// Get employee's schedule for the next 7 days
	schedules, err := sh.ScheduleStore.GetScheduleForEmployeeForSevenDays(user.OrganizationID, employeeID)
	if err != nil {
		sh.Logger.Error("failed to get employee schedule", "error", err, "employee_id", employeeID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve employee schedule"})
		return
	}

	sh.Logger.Info("employee schedule retrieved", "employee_id", employeeID, "count", len(schedules))
	c.JSON(http.StatusOK, gin.H{
		"message": "Employee schedule retrieved successfully",
		"data":    schedules,
	})
}

// storeScheduleOutput parses the ML model schedule output and stores each entry in the database
// schedule_output format: { "monday": [{"10:00-14:00": ["emp_001", "emp_002"]}, ...], ... }
func (sh *ScheduleHandler) storeScheduleOutput(orgID uuid.UUID, scheduleOutput map[string][]map[string][]string) error {
	// Map day names to their next occurrence date
	dayToDate := sh.getNextSevenDayDates()

	for dayName, timeSlots := range scheduleOutput {
		dayLower := strings.ToLower(dayName)
		scheduleDate, ok := dayToDate[dayLower]
		if !ok {
			sh.Logger.Warn("unknown day name in schedule output", "day", dayName)
			continue
		}

		for _, slotMap := range timeSlots {
			for timeRange, employeeIDs := range slotMap {
				// Parse time range "10:00-14:00"
				startTime, endTime, err := sh.parseTimeRange(timeRange, scheduleDate)
				if err != nil {
					sh.Logger.Error("failed to parse time range", "error", err, "time_range", timeRange)
					continue
				}

				// Store schedule for each employee
				for _, empIDStr := range employeeIDs {
					empID, err := uuid.Parse(empIDStr)
					if err != nil {
						sh.Logger.Warn("invalid employee ID in schedule output", "employee_id", empIDStr)
						continue
					}

					schedule := &database.Schedule{
						Date:      scheduleDate,
						Day:       dayLower,
						StartTime: startTime,
						EndTime:   endTime,
					}

					err = sh.ScheduleStore.StoreScheduleForUser(orgID, empID, schedule)
					if err != nil {
						sh.Logger.Error("failed to store schedule entry",
							"error", err,
							"employee_id", empID,
							"date", scheduleDate,
							"time_range", timeRange)
					}
				}
			}
		}
	}

	sh.Logger.Info("schedule output stored", "org_id", orgID)
	return nil
}

// getNextSevenDayDates returns a map of day names to their next occurrence date
func (sh *ScheduleHandler) getNextSevenDayDates() map[string]time.Time {
	dayToDate := make(map[string]time.Time)
	now := time.Now()

	for i := 0; i < 7; i++ {
		date := now.AddDate(0, 0, i)
		dayName := strings.ToLower(date.Weekday().String())
		dayToDate[dayName] = time.Date(date.Year(), date.Month(), date.Day(), 0, 0, 0, 0, date.Location())
	}

	return dayToDate
}

// parseTimeRange parses a time range string like "10:00-14:00" into start and end times
func (sh *ScheduleHandler) parseTimeRange(timeRange string, baseDate time.Time) (time.Time, time.Time, error) {
	parts := strings.Split(timeRange, "-")
	if len(parts) != 2 {
		return time.Time{}, time.Time{}, fmt.Errorf("invalid time range format: %s", timeRange)
	}

	startStr := strings.TrimSpace(parts[0])
	endStr := strings.TrimSpace(parts[1])

	startTime, err := sh.parseTimeString(startStr, baseDate)
	if err != nil {
		return time.Time{}, time.Time{}, fmt.Errorf("invalid start time: %w", err)
	}

	endTime, err := sh.parseTimeString(endStr, baseDate)
	if err != nil {
		return time.Time{}, time.Time{}, fmt.Errorf("invalid end time: %w", err)
	}

	return startTime, endTime, nil
}

// parseTimeString parses a time string like "10:00" into a time.Time with the base date
func (sh *ScheduleHandler) parseTimeString(timeStr string, baseDate time.Time) (time.Time, error) {
	parts := strings.Split(timeStr, ":")
	if len(parts) != 2 {
		return time.Time{}, fmt.Errorf("invalid time format: %s", timeStr)
	}

	hour := 0
	minute := 0
	_, err := fmt.Sscanf(timeStr, "%d:%d", &hour, &minute)
	if err != nil {
		return time.Time{}, err
	}

	return time.Date(baseDate.Year(), baseDate.Month(), baseDate.Day(), hour, minute, 0, 0, baseDate.Location()), nil
}
