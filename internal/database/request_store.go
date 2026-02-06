package database

import (
	"database/sql"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type Request struct {
	ID          uuid.UUID `json:"request_id"`
	EmployeeID  uuid.UUID `json:"employee_id"`
	Type        string    `json:"type"`
	Message     string    `json:"message"`
	SubmittedAt time.Time `json:"submitted_at"`
	UpdatedAt   time.Time `json:"updated_at"`
	Status      string    `json:"status"`
}

type RequestWithEmployee struct {
	Request
	EmployeeName  string `json:"employee_name"`
	EmployeeEmail string `json:"employee_email"`
}

type RequestStore interface {
	CreateRequest(req *Request) error
	GetRequestByID(id uuid.UUID) (*Request, error)
	GetRequestsByEmployee(employeeID uuid.UUID) ([]*Request, error)
	GetRequestsByOrganization(orgID uuid.UUID) ([]*RequestWithEmployee, error)
	UpdateRequestStatus(id uuid.UUID, status string) error
}

type PostgresRequestStore struct {
	db     *sql.DB
	Logger *slog.Logger
}

func NewPostgresRequestStore(db *sql.DB, logger *slog.Logger) *PostgresRequestStore {
	return &PostgresRequestStore{
		db:     db,
		Logger: logger,
	}
}

func (s *PostgresRequestStore) CreateRequest(req *Request) error {
	if req.ID == uuid.Nil {
		req.ID = uuid.New()
	}
	req.SubmittedAt = time.Now()
	req.UpdatedAt = time.Now()
	if req.Status == "" {
		req.Status = "in queue"
	}

	query := `INSERT INTO requests (request_id, employee_id, type, message, submitted_at, updated_at, status) 
		VALUES ($1, $2, $3, $4, $5, $6, $7)`

	_, err := s.db.Exec(query, req.ID, req.EmployeeID, req.Type, req.Message, req.SubmittedAt, req.UpdatedAt, req.Status)
	return err
}

func (s *PostgresRequestStore) GetRequestByID(id uuid.UUID) (*Request, error) {
	var req Request
	query := `SELECT request_id, employee_id, type, message, submitted_at, updated_at, status 
		FROM requests WHERE request_id=$1`

	err := s.db.QueryRow(query, id).Scan(
		&req.ID,
		&req.EmployeeID,
		&req.Type,
		&req.Message,
		&req.SubmittedAt,
		&req.UpdatedAt,
		&req.Status,
	)
	if err != nil {
		return nil, err
	}
	return &req, nil
}

func (s *PostgresRequestStore) GetRequestsByEmployee(employeeID uuid.UUID) ([]*Request, error) {
	query := `SELECT request_id, employee_id, type, message, submitted_at, updated_at, status 
		FROM requests WHERE employee_id=$1 ORDER BY submitted_at DESC`

	rows, err := s.db.Query(query, employeeID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var requests []*Request
	for rows.Next() {
		var req Request
		err := rows.Scan(
			&req.ID,
			&req.EmployeeID,
			&req.Type,
			&req.Message,
			&req.SubmittedAt,
			&req.UpdatedAt,
			&req.Status,
		)
		if err != nil {
			return nil, err
		}
		requests = append(requests, &req)
	}

	return requests, rows.Err()
}

func (s *PostgresRequestStore) GetRequestsByOrganization(orgID uuid.UUID) ([]*RequestWithEmployee, error) {
	query := `SELECT r.request_id, r.employee_id, r.type, r.message, r.submitted_at, r.updated_at, r.status,
			u.full_name, u.email
		FROM requests r
		JOIN users u ON r.employee_id = u.id
		WHERE u.organization_id=$1' 
		ORDER BY r.submitted_at DESC`

	rows, err := s.db.Query(query, orgID)
	if err != nil {
		return nil, err
	}
	defer rows.Close()

	var requests []*RequestWithEmployee
	for rows.Next() {
		var req RequestWithEmployee
		err := rows.Scan(
			&req.ID,
			&req.EmployeeID,
			&req.Type,
			&req.Message,
			&req.SubmittedAt,
			&req.UpdatedAt,
			&req.Status,
			&req.EmployeeName,
			&req.EmployeeEmail,
		)
		if err != nil {
			return nil, err
		}
		requests = append(requests, &req)
	}

	return requests, rows.Err()
}

func (s *PostgresRequestStore) UpdateRequestStatus(id uuid.UUID, status string) error {
	query := `UPDATE requests SET status=$1, updated_at=CURRENT_TIMESTAMP WHERE request_id=$2`
	res, err := s.db.Exec(query, status, id)
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
