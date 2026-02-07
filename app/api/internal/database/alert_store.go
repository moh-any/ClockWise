package database

import (
	"database/sql"
	"fmt"
	"log/slog"

	"github.com/google/uuid"
)

type Alert struct {
	Id           uuid.UUID `json:"id"`
	Organization uuid.UUID `json:"organization_id"`
	Severity     string    `json:"severity" binding:"required,oneof=critical moderate high"`
	Subject      string    `json:"subject"`
	Message      string    `json:"message"`
}

type AlertStore interface {
	StoreAlert(org_id uuid.UUID, alert *Alert) error
	GetAllAlerts(org_id uuid.UUID) ([]Alert, error)
	GetAllAlertsForLastWeek(org_id uuid.UUID) ([]Alert, error)
	GetAlertInsights(org_id uuid.UUID) ([]Insight, error)
}

type PostgresAlertStore struct {
	DB     *sql.DB
	Logger *slog.Logger
}

func NewPostgresAlertStore(DB *sql.DB, Logger *slog.Logger) *PostgresAlertStore {
	return &PostgresAlertStore{
		DB:     DB,
		Logger: Logger,
	}
}

func (psas *PostgresAlertStore) StoreAlert(org_id uuid.UUID, alert *Alert) error {
	return nil
}
func (psas *PostgresAlertStore) GetAllAlerts(org_id uuid.UUID) ([]Alert, error) {
	query := `
		SELECT id, organization_id, severity, subject, message
		FROM alerts
		WHERE organization_id = $1
		ORDER BY id DESC
	`

	rows, err := psas.DB.Query(query, org_id)
	if err != nil {
		psas.Logger.Error("Failed to query alerts", "error", err)
		return nil, err
	}
	defer rows.Close()

	var alerts []Alert
	for rows.Next() {
		var alert Alert
		err := rows.Scan(&alert.Id, &alert.Organization, &alert.Severity, &alert.Subject, &alert.Message)
		if err != nil {
			psas.Logger.Error("Failed to scan alert", "error", err)
			return nil, err
		}
		alerts = append(alerts, alert)
	}

	if err = rows.Err(); err != nil {
		psas.Logger.Error("Error iterating alerts", "error", err)
		return nil, err
	}

	return alerts, nil
}
func (psas *PostgresAlertStore) GetAllAlertsForLastWeek(org_id uuid.UUID) ([]Alert, error) {
	query := `
		SELECT id, organization_id, severity, subject, message
		FROM alerts
		WHERE organization_id = $1
		AND id IN (
			SELECT id FROM alerts
			WHERE organization_id = $1
			ORDER BY id DESC
			LIMIT (
				SELECT COUNT(*) * 7 / 
					GREATEST(EXTRACT(DAY FROM (NOW() - (SELECT MIN(id)::text::timestamp FROM alerts WHERE organization_id = $1))), 1)
				FROM alerts WHERE organization_id = $1
			)
		)
		ORDER BY id DESC
	`

	rows, err := psas.DB.Query(query, org_id)
	if err != nil {
		psas.Logger.Error("Failed to query alerts for last week", "error", err)
		return nil, err
	}
	defer rows.Close()

	var alerts []Alert
	for rows.Next() {
		var alert Alert
		err := rows.Scan(&alert.Id, &alert.Organization, &alert.Severity, &alert.Subject, &alert.Message)
		if err != nil {
			psas.Logger.Error("Failed to scan alert", "error", err)
			return nil, err
		}
		alerts = append(alerts, alert)
	}

	if err = rows.Err(); err != nil {
		psas.Logger.Error("Error iterating alerts for last week", "error", err)
		return nil, err
	}

	return alerts, nil
}
func (psas *PostgresAlertStore) GetAlertInsights(org_id uuid.UUID) ([]Insight, error) {
	var insights []Insight

	// Total alerts
	var totalAlerts int
	err := psas.DB.QueryRow(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1`, org_id).Scan(&totalAlerts)
	if err != nil {
		psas.Logger.Error("Failed to get total alerts", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{
		Title:     "Total Alerts",
		Statistic: fmt.Sprintf("%d", totalAlerts),
	})

	// Critical alerts count
	var criticalCount int
	err = psas.DB.QueryRow(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1 AND severity = 'critical'`, org_id).Scan(&criticalCount)
	if err != nil {
		psas.Logger.Error("Failed to get critical alerts", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{
		Title:     "Critical Alerts",
		Statistic: fmt.Sprintf("%d", criticalCount),
	})

	// High severity alerts count
	var highCount int
	err = psas.DB.QueryRow(`SELECT COUNT(*) FROM alerts WHERE organization_id = $1 AND severity = 'high'`, org_id).Scan(&highCount)
	if err != nil {
		psas.Logger.Error("Failed to get high severity alerts", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{
		Title:     "High Severity Alerts",
		Statistic: fmt.Sprintf("%d", highCount),
	})

	// Most common severity
	var mostCommonSeverity string
	err = psas.DB.QueryRow(`
		SELECT severity 
		FROM alerts 
		WHERE organization_id = $1 
		GROUP BY severity 
		ORDER BY COUNT(*) DESC 
		LIMIT 1
	`, org_id).Scan(&mostCommonSeverity)
	if err != nil && err != sql.ErrNoRows {
		psas.Logger.Error("Failed to get most common severity", "error", err)
		return nil, err
	}
	if mostCommonSeverity == "" {
		mostCommonSeverity = "N/A"
	}
	insights = append(insights, Insight{
		Title:     "Most Common Severity",
		Statistic: mostCommonSeverity,
	})

	return insights, nil
}
