package database

import (
	"database/sql"
	"log/slog"

	"github.com/google/uuid"
)

type Order struct {
}

type OrderItem struct {
}

type OrderStore interface {
	GetAllOrdersForLastWeek(org_id uuid.UUID) ([]Order, error)
	GetAllOrders(org_id uuid.UUID) ([]Order, error)
	GetOrderInsights(org_id uuid.UUID) ([]Order,error)
}

type PostgresOrderStore struct {
	Logger *slog.Logger
	DB     *sql.DB
}
