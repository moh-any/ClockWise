package database

import (
	"database/sql"
	"errors"
	"fmt"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type Offer struct {
	ID          uuid.UUID `json:"id"`
	Status      string    `json:"status"`
	ShiftLength int       `json:"shift_length"`
	StartTime   time.Time `json:"start_time"`
	UpdatedTime time.Time `json:"update_time"`
}

type OfferStore interface {
	StoreOffer(emp_id uuid.UUID, offer *Offer) error
	GetAllOffersForEmployee(emp_id uuid.UUID) ([]Offer, error)
	GetOfferByID(offer_id uuid.UUID) (*Offer,error)
	UpdateOfferStatus(offer_id uuid.UUID, status string) error
}

type PostgresOfferStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

func NewPostgresOfferStore(db *sql.DB, logger *slog.Logger) *PostgresOfferStore {
	return &PostgresOfferStore{
		db:     db,
		Logger: logger,
	}
}

func (pgos *PostgresOfferStore) StoreOffer(emp_id uuid.UUID, offer *Offer) error {
	tx, err := pgos.db.Begin()
	if err != nil {
		return err
	}
	defer tx.Rollback()

	if offer.ID == uuid.Nil {
		offer.ID = uuid.New()
	}
	if offer.Status == "" {
		offer.Status = "in queue"
	}

	query := `INSERT INTO over_time_offers (id, employee_id, status, shift_length, start_time) 
		VALUES ($1, $2, $3, $4, $5)`

	_, err = tx.Exec(query, offer.ID, emp_id, offer.Status, offer.StartTime, offer.StartTime)

	if _, err = tx.Exec(query, offer.ID, emp_id, offer.Status, offer.StartTime, offer.StartTime); err != nil {
		return fmt.Errorf("failed to insert offer: %w", err)
	}

	return tx.Commit()
}

func (pgos *PostgresOfferStore) GetAllOffersForEmployee(emp_id uuid.UUID) ([]Offer, error) {
	query := `SELECT id, status, shift_length, start_time, updated_at
		FROM over_time_offers WHERE employee_id = $1 AND start_time > CURRENT_TIMESTAMP ORDER BY start_time DESC, offer DESC`

	rows, err := pgos.db.Query(query, emp_id)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var offers []Offer
	for rows.Next() {
		var offer Offer
		err := rows.Scan(
			&offer.ID,
			&offer.Status,
			&offer.ShiftLength,
			&offer.StartTime,
			&offer.UpdatedTime,
		)

		if err != nil {
			return nil, err
		}
		offers = append(offers, offer)
	}

	return offers, rows.Err()
}

func (pgos *PostgresOfferStore) UpdateOfferStatus(offer_id uuid.UUID, status string) error {
	if status != "accepted" && status != "declined" || status != "in queue" {
		return errors.New("specified status is not permissible")
	} 

	query := `UPDATE over_time_offers SET status=$1, updated_at=CURRENT_TIMESTAMP WHERE id=$2`
	res, err := pgos.db.Exec(query, status, offer_id)

	if err != nil {
		return err
	}

	rowsAffected, err := res.RowsAffected()

	if err != nil {
		return err
	}

	if rowsAffected == 0 {
		return sql.ErrNoRows
	}

	return nil
}

func (pgos *PostgresOfferStore) GetOfferByID(offer_id uuid.UUID) (*Offer,error) {
	return nil, nil
}
