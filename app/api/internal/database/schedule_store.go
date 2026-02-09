package database

import (
	"database/sql"
	"log/slog"
	"time"

	"github.com/google/uuid"
	"github.com/lib/pq"
)

// Schedule represents a single employee's schedule entry
type ScheduleEntry struct {
	Date       time.Time `json:"schedule_date"`
	Day        string    `json:"day"`
	StartTime  string    `json:"start_time"`
	EndTime    string    `json:"end_time"`
	EmployeeID uuid.UUID `json:"employee_id"`
}

// Schedule represents grouped schedule with employees in same time slot
type Schedule struct {
	Date      time.Time `json:"schedule_date"`
	Day       string    `json:"day"`
	StartTime string    `json:"start_time"`
	EndTime   string    `json:"end_time"`
	Employees []string  `json:"employees"` // employee IDs
}

type ScheduleStore interface {
	StoreScheduleForUser(org_id uuid.UUID, user_id uuid.UUID, Schedule *Schedule) error
	GetFullScheduleForSevenDays(org_id uuid.UUID) ([]Schedule, error)
	GetScheduleForEmployeeForSevenDays(org_id uuid.UUID, user_id uuid.UUID) ([]Schedule, error)
}

type PostgresScheduleStore struct {
	UserStore UserStore
	DB        *sql.DB
	Logger    *slog.Logger
}

func NewPostgresScheduleStore(userStore UserStore, DB *sql.DB, Logger *slog.Logger) *PostgresScheduleStore {
	return &PostgresScheduleStore{
		UserStore: userStore,
		DB:        DB,
		Logger:    Logger,
	}
}

// StoreScheduleForUser stores schedule entries for a user
// Each time slot in the Schedule results in a separate row in the database
func (s *PostgresScheduleStore) StoreScheduleForUser(org_id uuid.UUID, user_id uuid.UUID, schedule *Schedule) error {
	// Verify user belongs to the organization
	var exists bool
	checkQuery := `SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND organization_id = $2)`
	err := s.DB.QueryRow(checkQuery, user_id, org_id).Scan(&exists)
	if err != nil {
		s.Logger.Error("failed to verify user organization", "error", err, "user_id", user_id, "org_id", org_id)
		return err
	}
	if !exists {
		s.Logger.Warn("user does not belong to organization", "user_id", user_id, "org_id", org_id)
		return sql.ErrNoRows
	}

	// Insert schedule entry for this user
	query := `
		INSERT INTO schedules (schedule_date, day, start_hour, end_hour, employee_id)
		VALUES ($1, $2, $3, $4, $5)
		ON CONFLICT (schedule_date, start_hour, end_hour, employee_id) DO NOTHING
	`

	_, err = s.DB.Exec(query,
		schedule.Date,
		schedule.Day,
		schedule.StartTime,
		schedule.EndTime,
		user_id,
	)
	if err != nil {
		s.Logger.Error("failed to store schedule", "error", err, "user_id", user_id)
		return err
	}

	s.Logger.Info("schedule stored", "user_id", user_id, "date", schedule.Date)
	return nil
}

// GetFullScheduleForSevenDays retrieves all schedules for the organization for 7 days
// Groups employees who have the same date and time slot together
func (s *PostgresScheduleStore) GetFullScheduleForSevenDays(org_id uuid.UUID) ([]Schedule, error) {
	query := `
		SELECT 
			s.schedule_date,
			s.day,
			s.start_hour,
			s.end_hour,
			ARRAY_AGG(s.employee_id::TEXT) as employees
		FROM schedules s
		INNER JOIN users u ON s.employee_id = u.id
		WHERE u.organization_id = $1
			AND s.schedule_date >= CURRENT_DATE
			AND s.schedule_date < CURRENT_DATE + INTERVAL '7 days'
		GROUP BY s.schedule_date, s.day, s.start_hour, s.end_hour
		ORDER BY s.schedule_date, s.start_hour
	`

	rows, err := s.DB.Query(query, org_id)
	if err != nil {
		s.Logger.Error("failed to get full schedule", "error", err, "org_id", org_id)
		return nil, err
	}
	defer rows.Close()

	var schedules []Schedule
	for rows.Next() {
		var schedule Schedule
		var employees pq.StringArray

		err := rows.Scan(
			&schedule.Date,
			&schedule.Day,
			&schedule.StartTime,
			&schedule.EndTime,
			&employees,
		)
		if err != nil {
			s.Logger.Error("failed to scan schedule row", "error", err)
			return nil, err
		}

		schedule.Employees = []string(employees)
		var names []string
		for _, empID := range schedule.Employees {
			employeeID, _ := uuid.Parse(empID)
			emp, err := s.UserStore.GetUserByID(employeeID)
			if err != nil {
				s.Logger.Error("failed to retrieve user id", "user", emp)
				continue
			}
			names = append(names, emp.FullName)
		}
		schedule.Employees = names
		schedules = append(schedules, schedule)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	s.Logger.Info("retrieved full schedule", "org_id", org_id, "count", len(schedules))
	return schedules, nil
}

// GetScheduleForEmployeeForSevenDays retrieves schedule for a specific employee for 7 days
func (s *PostgresScheduleStore) GetScheduleForEmployeeForSevenDays(org_id uuid.UUID, user_id uuid.UUID) ([]Schedule, error) {
	// Verify user belongs to the organization
	var exists bool
	checkQuery := `SELECT EXISTS(SELECT 1 FROM users WHERE id = $1 AND organization_id = $2)`
	err := s.DB.QueryRow(checkQuery, user_id, org_id).Scan(&exists)
	if err != nil {
		s.Logger.Error("failed to verify user organization", "error", err, "user_id", user_id, "org_id", org_id)
		return nil, err
	}
	if !exists {
		s.Logger.Warn("user does not belong to organization", "user_id", user_id, "org_id", org_id)
		return nil, sql.ErrNoRows
	}

	query := `
		SELECT 
			schedule_date,
			day,
			start_hour,
			end_hour,
			employee_id
		FROM schedules
		WHERE employee_id = $1
			AND schedule_date >= CURRENT_DATE
			AND schedule_date < CURRENT_DATE + INTERVAL '7 days'
		ORDER BY schedule_date, start_hour
	`

	rows, err := s.DB.Query(query, user_id)
	if err != nil {
		s.Logger.Error("failed to get employee schedule", "error", err, "user_id", user_id)
		return nil, err
	}
	defer rows.Close()

	var schedules []Schedule
	for rows.Next() {
		var schedule Schedule
		var employeeID uuid.UUID

		err := rows.Scan(
			&schedule.Date,
			&schedule.Day,
			&schedule.StartTime,
			&schedule.EndTime,
			&employeeID,
		)
		if err != nil {
			s.Logger.Error("failed to scan schedule row", "error", err)
			return nil, err
		}
		schedules = append(schedules, schedule)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	s.Logger.Info("retrieved employee schedule", "user_id", user_id, "count", len(schedules))
	return schedules, nil
}
