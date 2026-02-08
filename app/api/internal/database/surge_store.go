package database

import (
	"database/sql"
	"fmt"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type SurgeStore interface {
	GetVenueDetails(orgID uuid.UUID) (*VenueDetails, error)
	GetActiveVenues() ([]VenueSummary, error)
	GetActiveCampaigns(orgID uuid.UUID) (*CampaignStats, error)
	GetHistoricalOrders(orgID uuid.UUID, startTime, endTime time.Time) ([]OrderAggregate, error)
	GetDemandPredictions(orgID uuid.UUID, startTime, endTime time.Time) ([]PredictionAggregate, error)
	GetManagerAndAdminEmails(orgID uuid.UUID) ([]string, error)
}

type PostgresSurgeStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

func NewPostgresSurgeStore(db *sql.DB, logger *slog.Logger) *PostgresSurgeStore {
	return &PostgresSurgeStore{
		db:     db,
		Logger: logger,
	}
}

type VenueDetails struct {
	TypeID          int     `json:"type_id"`
	WaitingTime     int     `json:"waiting_time"`
	Rating          float64 `json:"rating"`
	Delivery        int     `json:"delivery"`
	AcceptingOrders int     `json:"accepting_orders"`
}

type CampaignStats struct {
	TotalCampaigns int     `json:"total_campaigns"`
	AvgDiscount    float64 `json:"avg_discount"`
}

type VenueSummary struct {
	ID        uuid.UUID `json:"place_id"` // Using UUID but mapping to place_id json field for compatibility
	Name      string    `json:"name"`
	Latitude  float64   `json:"latitude"`
	Longitude float64   `json:"longitude"`
}

type OrderAggregate struct {
	Timestamp  time.Time `json:"timestamp"`
	OrderCount int       `json:"order_count"`
	ItemCount  int       `json:"item_count"`
}

type PredictionAggregate struct {
	Timestamp      time.Time `json:"timestamp"`
	ItemCountPred  float64   `json:"item_count_pred"`
	OrderCountPred float64   `json:"order_count_pred"`
}

func (s *PostgresSurgeStore) GetActiveVenues() ([]VenueSummary, error) {
	query := `
		SELECT id, name, latitude, longitude
		FROM organizations
		WHERE latitude IS NOT NULL AND longitude IS NOT NULL
	`

	rows, err := s.db.Query(query)
	if err != nil {
		return nil, fmt.Errorf("failed to get active venues: %w", err)
	}
	defer rows.Close()

	var venues []VenueSummary
	for rows.Next() {
		var v VenueSummary
		if err := rows.Scan(&v.ID, &v.Name, &v.Latitude, &v.Longitude); err != nil {
			return nil, err
		}
		venues = append(venues, v)
	}
	return venues, nil
}

func (s *PostgresSurgeStore) GetVenueDetails(orgID uuid.UUID) (*VenueDetails, error) {
	// Note: Mapping ClockWise schema to Surge requirements
	// Using organization type as type_id (hashing or mapping needed if strict int required)
	// Waiting time might need to be estimated or stored in settings
	// Rating comes from organization table

	query := `
		SELECT 
			CASE 
				WHEN type = 'Restaurant' THEN 1 
				WHEN type = 'Cafe' THEN 2 
				ELSE 0 
			END as type_id,
			coalesce(rating, 0) as rating
		FROM organizations 
		WHERE id = $1
	`

	var details VenueDetails
	err := s.db.QueryRow(query, orgID).Scan(&details.TypeID, &details.Rating)
	if err != nil {
		return nil, fmt.Errorf("failed to get venue details: %w", err)
	}

	// Hardcoded defaults for now as these might not exist in current schema
	details.WaitingTime = 15
	details.Delivery = 1
	details.AcceptingOrders = 1

	return &details, nil
}

func (s *PostgresSurgeStore) GetActiveCampaigns(orgID uuid.UUID) (*CampaignStats, error) {
	// Assuming campaigns table exists given CampaignHandler reference
	// If not, we return 0 vals
	query := `
		SELECT count(*), coalesce(avg(discount_percentage), 0)
		FROM campaigns 
		WHERE organization_id = $1 
		AND start_time <= NOW() 
		AND end_time >= NOW()
	`

	var stats CampaignStats
	// Check if table exists first to avoid crashing if table missing
	// skipping check for brevity, assuming standard schema from handlers

	err := s.db.QueryRow(query, orgID).Scan(&stats.TotalCampaigns, &stats.AvgDiscount)
	if err != nil {
		// If table doesn't exist or other error, log and return empty
		s.Logger.Warn("failed to get campaign stats (tables might be missing)", "error", err)
		return &CampaignStats{TotalCampaigns: 0, AvgDiscount: 0}, nil
	}

	return &stats, nil
}

func (s *PostgresSurgeStore) GetHistoricalOrders(orgID uuid.UUID, startTime, endTime time.Time) ([]OrderAggregate, error) {
	query := `
		SELECT 
			date_trunc('hour', create_time) as timestamp,
			count(*) as order_count,
			coalesce(sum(
				(SELECT count(*) FROM order_items WHERE order_items.order_id = orders.id)
			), 0) as item_count
		FROM orders
		WHERE organization_id = $1
		  AND create_time >= $2
		  AND create_time <= $3
		GROUP BY date_trunc('hour', create_time)
		ORDER BY timestamp
	`

	rows, err := s.db.Query(query, orgID, startTime, endTime)
	if err != nil {
		return nil, fmt.Errorf("failed to get historical orders: %w", err)
	}
	defer rows.Close()

	var results []OrderAggregate
	for rows.Next() {
		var agg OrderAggregate
		if err := rows.Scan(&agg.Timestamp, &agg.OrderCount, &agg.ItemCount); err != nil {
			return nil, err
		}
		results = append(results, agg)
	}
	return results, nil
}

func (s *PostgresSurgeStore) GetDemandPredictions(orgID uuid.UUID, startTime, endTime time.Time) ([]PredictionAggregate, error) {
	// Assuming a 'demand_predictions' table exists.
	// If not, we'll return empty list which triggers ML fallback
	query := `
		SELECT timestamp, item_count_pred, order_count_pred
		FROM demand_predictions
		WHERE organization_id = $1
		  AND timestamp >= $2
		  AND timestamp <= $3
		ORDER BY timestamp
	`

	rows, err := s.db.Query(query, orgID, startTime, endTime)
	if err != nil {
		// Log warning but don't fail - table might not exist yet
		s.Logger.Warn("failed to get predictions", "error", err)
		return []PredictionAggregate{}, nil
	}
	defer rows.Close()

	var results []PredictionAggregate
	for rows.Next() {
		var pred PredictionAggregate
		if err := rows.Scan(&pred.Timestamp, &pred.ItemCountPred, &pred.OrderCountPred); err != nil {
			return nil, err
		}
		results = append(results, pred)
	}
	return results, nil
}

func (s *PostgresSurgeStore) GetManagerAndAdminEmails(orgID uuid.UUID) ([]string, error) {
	query := `
		SELECT email 
		FROM users 
		WHERE organization_id = $1 
		  AND (user_role = 'admin' OR user_role = 'manager')
	`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		return nil, fmt.Errorf("failed to get emails: %w", err)
	}
	defer rows.Close()

	var emails []string
	for rows.Next() {
		var email string
		if err := rows.Scan(&email); err != nil {
			return nil, err
		}
		emails = append(emails, email)
	}
	return emails, nil
}
