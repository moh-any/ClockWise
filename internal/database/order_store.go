package database

import (
	"database/sql"
	"log/slog"
	"time"

	"github.com/google/uuid"
)

type Order struct {
	OrderID        uuid.UUID     `json:"order_id"`
	UserID         uuid.UUID     `json:"user_id"`
	OrganizationID uuid.UUID     `json:"organization_id"`
	CreateTime     time.Time     `json:"create_time"`
	OrderType      string        `json:"order_type"`
	OrderStatus    string        `json:"order_status"`
	TotalAmount    *float64      `json:"total_amount"`
	DiscountAmount *float64      `json:"discount_amount"`
	Rating         *float64      `json:"rating,omitempty"`
	OrderItems     []OrderItem   `json:"order_items"`
	DeliveryStatus OrderDelivery `json:"delivery_status"`
}

type OrderItem struct {
	Name                        string   `json:"name"`
	NeededNumEmployeesToPrepare int      `json:"needed_employees"`
	Price                       *float64 `json:"price"`
}

type OrderDelivery struct {
	DriverID           uuid.UUID `json:"driver_id"`
	DeliveryLocation   Location  `json:"location"`
	OutForDeliveryTime time.Time `json:"out_for_delivery_time"`
	DeliveredTime      time.Time `json:"delivered_time"`
	DeliveryStatus     string    `json:"status"`
}

type Location struct {
	Latitude  *float64 `json:"latitude,omitempty"`
	Longitude *float64 `json:"longitude,omitempty"`
}

type OrderStore interface {
	GetAllOrdersForLastWeek(org_id uuid.UUID) ([]Order, error)
	GetAllOrders(org_id uuid.UUID) ([]Order, error)
	GetTodayOrder(org_id uuid.UUID) ([]Order, error)
	GetOrdersInsights(org_id uuid.UUID) ([]Insight, error)
	StoreOrder(org_id uuid.UUID, order *Order) error
}

type PostgresOrderStore struct {
	Logger *slog.Logger
	DB     *sql.DB
}

func NewPostgresOrderStore(db *sql.DB, logger *slog.Logger) *PostgresOrderStore {
	return &PostgresOrderStore{
		DB:     db,
		Logger: logger,
	}
}
