package database

import (
	"database/sql"
	"encoding/json"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type DemandPredictResponse struct {
	RestaurantName   string          `json:"restaurant_name"`
	PredictionPerion string          `json:"prediction_period"`
	Days             []PredictionDay `json:"days"`
}

type PredictionDay struct {
	Day   string           `json:"day_name"`
	Date  time.Time        `json:"date"` // Only Date change time format
	Hours []PredictionHour `json:"hours"`
}
type PredictionHour struct {
	HourNo     int `json:"hour"`
	OrderCount int `json:"order_count"`
	ItemCount  int `json:"item_count"`
}

// Custom UnmarshalJSON to handle date parsing from string format (2024-02-01)
func (pd *PredictionDay) UnmarshalJSON(data []byte) error {
	type Alias PredictionDay
	aux := &struct {
		Date string `json:"date"`
		*Alias
	}{
		Alias: (*Alias)(pd),
	}

	if err := json.Unmarshal(data, &aux); err != nil {
		return err
	}

	if aux.Date != "" {
		parsedTime, err := time.Parse("2006-01-02", aux.Date)
		if err != nil {
			// Try RFC3339 format as fallback
			parsedTime, err = time.Parse(time.RFC3339, aux.Date)
			if err != nil {
				return err
			}
		}
		pd.Date = parsedTime
	}

	return nil
}

type DemandStore interface {
	StoreDemandHeatMap(org_id uuid.UUID, demand DemandPredictResponse) error
	GetLatestDemandHeatMap(org_id uuid.UUID) (*DemandPredictResponse, error)
}

type PostgresDemandStore struct {
	DB     *sql.DB
	Logger *slog.Logger
}

func NewPostgresDemandStore(DB *sql.DB, Logger *slog.Logger) *PostgresDemandStore {
	return &PostgresDemandStore{
		DB:     DB,
		Logger: Logger,
	}
}

func (pgds *PostgresDemandStore) StoreDemandHeatMap(org_id uuid.UUID, demand DemandPredictResponse) error {
	pgds.Logger.Info("storing demand heatmap",
		"organization_id", org_id,
		"prediction_period", demand.PredictionPerion,
		"days_count", len(demand.Days))

	tx, err := pgds.DB.Begin()
	if err != nil {
		pgds.Logger.Error("failed to begin transaction", "error", err, "organization_id", org_id)
		return err
	}
	defer tx.Rollback()

	// Delete existing demand data for the organization (keep only latest 7 days)
	deleteQuery := `DELETE FROM demand WHERE organization_id = $1`
	_, err = tx.Exec(deleteQuery, org_id)
	if err != nil {
		pgds.Logger.Error("failed to delete existing demand data", "error", err, "organization_id", org_id)
		return err
	}

	// Insert new demand predictions
	insertQuery := `INSERT INTO demand (organization_id, demand_date, day, hour, order_count, item_count) 
		VALUES ($1, $2, $3, $4, $5, $6)`

	for _, day := range demand.Days {
		for _, hour := range day.Hours {
			_, err = tx.Exec(insertQuery,
				org_id,
				day.Date,
				day.Day,
				hour.HourNo,
				hour.OrderCount,
				hour.ItemCount,
			)
			if err != nil {
				pgds.Logger.Error("failed to insert demand data",
					"error", err,
					"organization_id", org_id,
					"date", day.Date,
					"hour", hour.HourNo)
				return err
			}
		}
	}

	if err := tx.Commit(); err != nil {
		pgds.Logger.Error("failed to commit transaction", "error", err, "organization_id", org_id)
		return err
	}

	pgds.Logger.Info("demand heatmap stored",
		"organization_id", org_id,
		"days_count", len(demand.Days))
	return nil
}

func (pgds *PostgresDemandStore) GetLatestDemandHeatMap(org_id uuid.UUID) (*DemandPredictResponse, error) {
	// Query to get demand for the last 7 days
	query := `SELECT demand_date, day, hour, order_count, item_count 
		FROM demand 
		WHERE organization_id = $1 
		AND demand_date >= CURRENT_DATE 
		AND demand_date < CURRENT_DATE + INTERVAL '7 days'
		ORDER BY demand_date, hour`

	rows, err := pgds.DB.Query(query, org_id)
	if err != nil {
		pgds.Logger.Error("failed to query demand data", "error", err, "organization_id", org_id)
		return nil, err
	}
	defer rows.Close()

	// Map to group hours by date
	dayMap := make(map[string]*PredictionDay)
	var dates []string

	for rows.Next() {
		var demandDate time.Time
		var dayName string
		var hour, orderCount, itemCount int

		if err := rows.Scan(&demandDate, &dayName, &hour, &orderCount, &itemCount); err != nil {
			pgds.Logger.Error("failed to scan demand row", "error", err)
			return nil, err
		}

		dateKey := demandDate.Format("2006-01-02")

		if _, exists := dayMap[dateKey]; !exists {
			dayMap[dateKey] = &PredictionDay{
				Day:   dayName,
				Date:  demandDate,
				Hours: []PredictionHour{},
			}
			dates = append(dates, dateKey)
		}

		dayMap[dateKey].Hours = append(dayMap[dateKey].Hours, PredictionHour{
			HourNo:     hour,
			OrderCount: orderCount,
			ItemCount:  itemCount,
		})
	}

	if err := rows.Err(); err != nil {
		pgds.Logger.Error("error iterating demand rows", "error", err)
		return nil, err
	}

	// No data found
	if len(dayMap) == 0 {
		return nil, nil
	}

	// Build response with days in order
	var days []PredictionDay
	for _, dateKey := range dates {
		days = append(days, *dayMap[dateKey])
	}

	// Get the first and last date for the prediction period
	firstDate := days[0].Date.Format("2006-01-02")
	lastDate := days[len(days)-1].Date.Format("2006-01-02")

	response := &DemandPredictResponse{
		RestaurantName:   "", // Organization name not stored in demand table
		PredictionPerion: firstDate + " to " + lastDate,
		Days:             days,
	}

	pgds.Logger.Info("demand heatmap retrieved",
		"organization_id", org_id,
		"days_count", len(days))

	return response, nil
}
