package database

import (
	"database/sql"
	"fmt"
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
	OrderID            uuid.UUID `json:"order_id,omitempty"`
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
	GetAllItems(org_id uuid.UUID) ([]OrderItem, error)
	GetTodaysOrder(org_id uuid.UUID) ([]Order, error)
	GetOrdersInsights(org_id uuid.UUID) ([]Insight, error)
	GetDeliveryInsights(org_id uuid.UUID) ([]Insight, error)
	GetItemsInsights(org_id uuid.UUID) ([]Insight, error)
	StoreOrder(org_id uuid.UUID, order *Order) error
	StoreOrderItems(org_id uuid.UUID, order_id uuid.UUID, order *OrderItem) error
	StoreItems(org_id uuid.UUID, item *OrderItem) error
	GetAllDeliveries(org_id uuid.UUID) ([]OrderDelivery, error)
	GetAllDeliveriesForLastWeek(org_id uuid.UUID) ([]OrderDelivery, error)
	GetTodaysDeliveries(org_id uuid.UUID) ([]OrderDelivery, error)
	StoreDelivery(org_id uuid.UUID, delivery *OrderDelivery) error
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

func (pgos *PostgresOrderStore) GetAllOrdersForLastWeek(org_id uuid.UUID) ([]Order, error) {
	query := `
		SELECT id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating
		FROM orders
		WHERE organization_id = $1 AND create_time >= NOW() - INTERVAL '7 days'
		ORDER BY create_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get orders for last week", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanOrders(rows)
}

func (pgos *PostgresOrderStore) GetAllOrders(org_id uuid.UUID) ([]Order, error) {
	query := `
		SELECT id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating
		FROM orders
		WHERE organization_id = $1
		ORDER BY create_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get all orders", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanOrders(rows)
}

func (pgos *PostgresOrderStore) GetTodaysOrder(org_id uuid.UUID) ([]Order, error) {
	query := `
		SELECT id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating
		FROM orders
		WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE
		ORDER BY create_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get today's orders", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanOrders(rows)
}

func (pgos *PostgresOrderStore) GetOrdersInsights(org_id uuid.UUID) ([]Insight, error) {
	var insights []Insight

	// Number of orders for all time
	var totalOrders int
	err := pgos.DB.QueryRow(`SELECT COUNT(*) FROM orders WHERE organization_id = $1`, org_id).Scan(&totalOrders)
	if err != nil {
		pgos.Logger.Error("Failed to get total orders count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Total Orders (All Time)", Statistic: fmt.Sprintf("%d", totalOrders)})

	// Number of orders for last week
	var weeklyOrders int
	err = pgos.DB.QueryRow(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND create_time >= NOW() - INTERVAL '7 days'`, org_id).Scan(&weeklyOrders)
	if err != nil {
		pgos.Logger.Error("Failed to get weekly orders count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Orders (Last 7 Days)", Statistic: fmt.Sprintf("%d", weeklyOrders)})

	// Number of orders for today
	var todayOrders int
	err = pgos.DB.QueryRow(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE`, org_id).Scan(&todayOrders)
	if err != nil {
		pgos.Logger.Error("Failed to get today's orders count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Orders (Today)", Statistic: fmt.Sprintf("%d", todayOrders)})

	// Busiest Day for orders
	var busiestOrderDay sql.NullString
	err = pgos.DB.QueryRow(`
		SELECT TO_CHAR(create_time, 'Day') as day_name
		FROM orders
		WHERE organization_id = $1
		GROUP BY TO_CHAR(create_time, 'Day'), EXTRACT(DOW FROM create_time)
		ORDER BY COUNT(*) DESC
		LIMIT 1
	`, org_id).Scan(&busiestOrderDay)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get busiest order day", "error", err)
		return nil, err
	}
	if busiestOrderDay.Valid {
		insights = append(insights, Insight{Title: "Busiest Day (Orders)", Statistic: busiestOrderDay.String})
	} else {
		insights = append(insights, Insight{Title: "Busiest Day (Orders)", Statistic: "N/A"})
	}

	// Busiest Hour for orders
	var busiestOrderHour sql.NullInt64
	err = pgos.DB.QueryRow(`
		SELECT EXTRACT(HOUR FROM create_time)::int as hour
		FROM orders
		WHERE organization_id = $1
		GROUP BY EXTRACT(HOUR FROM create_time)
		ORDER BY COUNT(*) DESC
		LIMIT 1
	`, org_id).Scan(&busiestOrderHour)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get busiest order hour", "error", err)
		return nil, err
	}
	if busiestOrderHour.Valid {
		insights = append(insights, Insight{Title: "Busiest Hour (Orders)", Statistic: fmt.Sprintf("%d:00", busiestOrderHour.Int64)})
	} else {
		insights = append(insights, Insight{Title: "Busiest Hour (Orders)", Statistic: "N/A"})
	}

	return insights, nil
}

func (pgos *PostgresOrderStore) GetDeliveryInsights(org_id uuid.UUID) ([]Insight, error) {
	var insights []Insight

	// Number of deliveries for all time
	var totalDeliveries int
	err := pgos.DB.QueryRow(`
		SELECT COUNT(*) FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1
	`, org_id).Scan(&totalDeliveries)
	if err != nil {
		pgos.Logger.Error("Failed to get total deliveries count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Total Deliveries (All Time)", Statistic: fmt.Sprintf("%d", totalDeliveries)})

	// Number of deliveries for last week
	var weeklyDeliveries int
	err = pgos.DB.QueryRow(`
		SELECT COUNT(*) FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1 AND d.out_for_delivery_time >= NOW() - INTERVAL '7 days'
	`, org_id).Scan(&weeklyDeliveries)
	if err != nil {
		pgos.Logger.Error("Failed to get weekly deliveries count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Deliveries (Last 7 Days)", Statistic: fmt.Sprintf("%d", weeklyDeliveries)})

	// Number of deliveries for today
	var todayDeliveries int
	err = pgos.DB.QueryRow(`
		SELECT COUNT(*) FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1 AND DATE(d.out_for_delivery_time) = CURRENT_DATE
	`, org_id).Scan(&todayDeliveries)
	if err != nil {
		pgos.Logger.Error("Failed to get today's deliveries count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Deliveries (Today)", Statistic: fmt.Sprintf("%d", todayDeliveries)})

	// Busiest Day for deliveries
	var busiestDeliveryDay sql.NullString
	err = pgos.DB.QueryRow(`
		SELECT TO_CHAR(d.out_for_delivery_time, 'Day') as day_name
		FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1
		GROUP BY TO_CHAR(d.out_for_delivery_time, 'Day'), EXTRACT(DOW FROM d.out_for_delivery_time)
		ORDER BY COUNT(*) DESC
		LIMIT 1
	`, org_id).Scan(&busiestDeliveryDay)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get busiest delivery day", "error", err)
		return nil, err
	}
	if busiestDeliveryDay.Valid {
		insights = append(insights, Insight{Title: "Busiest Day (Deliveries)", Statistic: busiestDeliveryDay.String})
	} else {
		insights = append(insights, Insight{Title: "Busiest Day (Deliveries)", Statistic: "N/A"})
	}

	// Busiest Hour for deliveries
	var busiestDeliveryHour sql.NullInt64
	err = pgos.DB.QueryRow(`
		SELECT EXTRACT(HOUR FROM d.out_for_delivery_time)::int as hour
		FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1
		GROUP BY EXTRACT(HOUR FROM d.out_for_delivery_time)
		ORDER BY COUNT(*) DESC
		LIMIT 1
	`, org_id).Scan(&busiestDeliveryHour)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get busiest delivery hour", "error", err)
		return nil, err
	}
	if busiestDeliveryHour.Valid {
		insights = append(insights, Insight{Title: "Busiest Hour (Deliveries)", Statistic: fmt.Sprintf("%d:00", busiestDeliveryHour.Int64)})
	} else {
		insights = append(insights, Insight{Title: "Busiest Hour (Deliveries)", Statistic: "N/A"})
	}

	return insights, nil
}

func (pgos *PostgresOrderStore) StoreOrder(org_id uuid.UUID, order *Order) error {
	tx, err := pgos.DB.Begin()
	if err != nil {
		pgos.Logger.Error("Failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Insert the order
	query := `
		INSERT INTO orders (id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating)
		VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
	`
	_, err = tx.Exec(query, order.OrderID, order.UserID, org_id, order.CreateTime, order.OrderType, order.OrderStatus, order.TotalAmount, order.DiscountAmount, order.Rating)
	if err != nil {
		pgos.Logger.Error("Failed to insert order", "error", err)
		return err
	}

	// If order is a delivery, insert delivery record
	if order.OrderType == "delivery" {
		deliveryQuery := `
			INSERT INTO deliveries (order_id, driver_id, delivery_latitude, delivery_longitude, out_for_delivery_time, delivered_time, status)
			VALUES ($1, $2, $3, $4, $5, $6, $7)
		`
		_, err = tx.Exec(deliveryQuery,
			order.OrderID,
			order.DeliveryStatus.DriverID,
			order.DeliveryStatus.DeliveryLocation.Latitude,
			order.DeliveryStatus.DeliveryLocation.Longitude,
			order.DeliveryStatus.OutForDeliveryTime,
			order.DeliveryStatus.DeliveredTime,
			order.DeliveryStatus.DeliveryStatus,
		)
		if err != nil {
			pgos.Logger.Error("Failed to insert delivery", "error", err)
			return err
		}
	}

	if err = tx.Commit(); err != nil {
		pgos.Logger.Error("Failed to commit transaction", "error", err)
		return err
	}

	return nil
}

// Helper function to scan order rows
func (pgos *PostgresOrderStore) scanOrders(rows *sql.Rows) ([]Order, error) {
	var orders []Order

	for rows.Next() {
		var order Order
		err := rows.Scan(
			&order.OrderID,
			&order.UserID,
			&order.OrganizationID,
			&order.CreateTime,
			&order.OrderType,
			&order.OrderStatus,
			&order.TotalAmount,
			&order.DiscountAmount,
			&order.Rating,
		)
		if err != nil {
			pgos.Logger.Error("Failed to scan order row", "error", err)
			return nil, err
		}
		orders = append(orders, order)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return orders, nil
}

// GetAllDeliveries returns all deliveries for an organization
func (pgos *PostgresOrderStore) GetAllDeliveries(org_id uuid.UUID) ([]OrderDelivery, error) {
	query := `
		SELECT d.order_id, d.driver_id, d.delivery_latitude, d.delivery_longitude, d.out_for_delivery_time, d.delivered_time, d.status
		FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1
		ORDER BY d.out_for_delivery_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get all deliveries", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanDeliveries(rows)
}

// GetAllDeliveriesForLastWeek returns all deliveries for the last 7 days
func (pgos *PostgresOrderStore) GetAllDeliveriesForLastWeek(org_id uuid.UUID) ([]OrderDelivery, error) {
	query := `
		SELECT d.order_id, d.driver_id, d.delivery_latitude, d.delivery_longitude, d.out_for_delivery_time, d.delivered_time, d.status
		FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1 AND d.out_for_delivery_time >= NOW() - INTERVAL '7 days'
		ORDER BY d.out_for_delivery_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get deliveries for last week", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanDeliveries(rows)
}

// GetTodaysDeliveries returns all deliveries for today
func (pgos *PostgresOrderStore) GetTodaysDeliveries(org_id uuid.UUID) ([]OrderDelivery, error) {
	query := `
		SELECT d.order_id, d.driver_id, d.delivery_latitude, d.delivery_longitude, d.out_for_delivery_time, d.delivered_time, d.status
		FROM deliveries d
		JOIN orders o ON d.order_id = o.id
		WHERE o.organization_id = $1 AND DATE(d.out_for_delivery_time) = CURRENT_DATE
		ORDER BY d.out_for_delivery_time DESC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get today's deliveries", "error", err)
		return nil, err
	}
	defer rows.Close()

	return pgos.scanDeliveries(rows)
}

// Helper function to scan delivery rows
func (pgos *PostgresOrderStore) scanDeliveries(rows *sql.Rows) ([]OrderDelivery, error) {
	var deliveries []OrderDelivery

	for rows.Next() {
		var delivery OrderDelivery
		var deliveredTime sql.NullTime
		err := rows.Scan(
			&delivery.OrderID,
			&delivery.DriverID,
			&delivery.DeliveryLocation.Latitude,
			&delivery.DeliveryLocation.Longitude,
			&delivery.OutForDeliveryTime,
			&deliveredTime,
			&delivery.DeliveryStatus,
		)
		if err != nil {
			pgos.Logger.Error("Failed to scan delivery row", "error", err)
			return nil, err
		}
		if deliveredTime.Valid {
			delivery.DeliveredTime = deliveredTime.Time
		}
		deliveries = append(deliveries, delivery)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return deliveries, nil
}

// StoreDelivery inserts a new delivery record for an existing order
func (pgos *PostgresOrderStore) StoreDelivery(org_id uuid.UUID, delivery *OrderDelivery) error {
	// Verify the order exists and belongs to the organization
	var exists bool
	err := pgos.DB.QueryRow(`
		SELECT EXISTS(SELECT 1 FROM orders WHERE id = $1 AND organization_id = $2)
	`, delivery.OrderID, org_id).Scan(&exists)
	if err != nil {
		pgos.Logger.Error("Failed to verify order exists", "error", err)
		return err
	}
	if !exists {
		pgos.Logger.Error("Order not found or does not belong to organization", "order_id", delivery.OrderID, "org_id", org_id)
		return fmt.Errorf("order not found or does not belong to organization")
	}

	query := `
		INSERT INTO deliveries (order_id, driver_id, delivery_latitude, delivery_longitude, out_for_delivery_time, delivered_time, status)
		VALUES ($1, $2, $3, $4, $5, $6, $7)
	`
	_, err = pgos.DB.Exec(query,
		delivery.OrderID,
		delivery.DriverID,
		delivery.DeliveryLocation.Latitude,
		delivery.DeliveryLocation.Longitude,
		delivery.OutForDeliveryTime,
		delivery.DeliveredTime,
		delivery.DeliveryStatus,
	)
	if err != nil {
		pgos.Logger.Error("Failed to insert delivery", "error", err)
		return err
	}

	return nil
}

// StoreOrderItems inserts or links an order item to an order
func (pgos *PostgresOrderStore) StoreOrderItems(org_id uuid.UUID, order_id uuid.UUID, orderItem *OrderItem) error {
	// Verify the order exists and belongs to the organization
	var exists bool
	err := pgos.DB.QueryRow(`
		SELECT EXISTS(SELECT 1 FROM orders WHERE id = $1 AND organization_id = $2)
	`, order_id, org_id).Scan(&exists)
	if err != nil {
		pgos.Logger.Error("Failed to verify order exists", "error", err)
		return err
	}
	if !exists {
		pgos.Logger.Error("Order not found or does not belong to organization", "order_id", order_id, "org_id", org_id)
		return fmt.Errorf("order not found or does not belong to organization")
	}

	tx, err := pgos.DB.Begin()
	if err != nil {
		pgos.Logger.Error("Failed to begin transaction", "error", err)
		return err
	}
	defer tx.Rollback()

	// Check if item already exists for this organization, if not create it
	var itemID uuid.UUID
	err = tx.QueryRow(`
		SELECT id FROM items WHERE organization_id = $1 AND name = $2
	`, org_id, orderItem.Name).Scan(&itemID)

	if err == sql.ErrNoRows {
		// Item doesn't exist, create it
		err = tx.QueryRow(`
			INSERT INTO items (organization_id, name, needed_num_to_prepare, price)
			VALUES ($1, $2, $3, $4)
			RETURNING id
		`, org_id, orderItem.Name, orderItem.NeededNumEmployeesToPrepare, orderItem.Price).Scan(&itemID)
		if err != nil {
			pgos.Logger.Error("Failed to insert item", "error", err)
			return err
		}
	} else if err != nil {
		pgos.Logger.Error("Failed to check if item exists", "error", err)
		return err
	}

	// Link the item to the order in order_items table
	_, err = tx.Exec(`
		INSERT INTO order_items (order_id, item_id)
		VALUES ($1, $2)
		ON CONFLICT (order_id, item_id) DO NOTHING
	`, order_id, itemID)
	if err != nil {
		pgos.Logger.Error("Failed to insert order_item link", "error", err)
		return err
	}

	if err = tx.Commit(); err != nil {
		pgos.Logger.Error("Failed to commit transaction", "error", err)
		return err
	}

	return nil
}

// StoreItems inserts an item into the items table for an organization
func (pgos *PostgresOrderStore) StoreItems(org_id uuid.UUID, item *OrderItem) error {
	// Check if item already exists for this organization
	var exists bool
	err := pgos.DB.QueryRow(`
		SELECT EXISTS(SELECT 1 FROM items WHERE organization_id = $1 AND name = $2)
	`, org_id, item.Name).Scan(&exists)
	if err != nil {
		pgos.Logger.Error("Failed to check if item exists", "error", err)
		return err
	}
	if exists {
		pgos.Logger.Warn("Item already exists for organization", "name", item.Name, "org_id", org_id)
		return fmt.Errorf("item with name '%s' already exists", item.Name)
	}

	query := `
		INSERT INTO items (organization_id, name, needed_num_to_prepare, price)
		VALUES ($1, $2, $3, $4)
	`
	_, err = pgos.DB.Exec(query, org_id, item.Name, item.NeededNumEmployeesToPrepare, item.Price)
	if err != nil {
		pgos.Logger.Error("Failed to insert item", "error", err)
		return err
	}

	pgos.Logger.Info("Item stored successfully", "name", item.Name, "org_id", org_id)
	return nil
}

// GetAllItems returns all items for an organization
func (pgos *PostgresOrderStore) GetAllItems(org_id uuid.UUID) ([]OrderItem, error) {
	query := `
		SELECT name, needed_num_to_prepare, price
		FROM items
		WHERE organization_id = $1
		ORDER BY name ASC
	`

	rows, err := pgos.DB.Query(query, org_id)
	if err != nil {
		pgos.Logger.Error("Failed to get all items", "error", err)
		return nil, err
	}
	defer rows.Close()

	var items []OrderItem
	for rows.Next() {
		var item OrderItem
		err := rows.Scan(&item.Name, &item.NeededNumEmployeesToPrepare, &item.Price)
		if err != nil {
			pgos.Logger.Error("Failed to scan item row", "error", err)
			return nil, err
		}
		items = append(items, item)
	}

	if err := rows.Err(); err != nil {
		return nil, err
	}

	return items, nil
}

// GetItemsInsights returns insights about items for an organization
func (pgos *PostgresOrderStore) GetItemsInsights(org_id uuid.UUID) ([]Insight, error) {
	var insights []Insight

	// Total number of items
	var totalItems int
	err := pgos.DB.QueryRow(`SELECT COUNT(*) FROM items WHERE organization_id = $1`, org_id).Scan(&totalItems)
	if err != nil {
		pgos.Logger.Error("Failed to get total items count", "error", err)
		return nil, err
	}
	insights = append(insights, Insight{Title: "Total Items", Statistic: fmt.Sprintf("%d", totalItems)})

	// Average item price
	var avgPrice sql.NullFloat64
	err = pgos.DB.QueryRow(`SELECT AVG(price) FROM items WHERE organization_id = $1`, org_id).Scan(&avgPrice)
	if err != nil {
		pgos.Logger.Error("Failed to get average item price", "error", err)
		return nil, err
	}
	if avgPrice.Valid {
		insights = append(insights, Insight{Title: "Average Item Price", Statistic: fmt.Sprintf("$%.2f", avgPrice.Float64)})
	} else {
		insights = append(insights, Insight{Title: "Average Item Price", Statistic: "N/A"})
	}

	// Most expensive item
	var mostExpensiveItem sql.NullString
	var mostExpensivePrice sql.NullFloat64
	err = pgos.DB.QueryRow(`
		SELECT name, price FROM items 
		WHERE organization_id = $1 
		ORDER BY price DESC 
		LIMIT 1
	`, org_id).Scan(&mostExpensiveItem, &mostExpensivePrice)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get most expensive item", "error", err)
		return nil, err
	}
	if mostExpensiveItem.Valid {
		insights = append(insights, Insight{Title: "Most Expensive Item", Statistic: fmt.Sprintf("%s ($%.2f)", mostExpensiveItem.String, mostExpensivePrice.Float64)})
	} else {
		insights = append(insights, Insight{Title: "Most Expensive Item", Statistic: "N/A"})
	}

	// Most ordered item (by count in order_items)
	var mostOrderedItem sql.NullString
	var mostOrderedCount sql.NullInt64
	err = pgos.DB.QueryRow(`
		SELECT i.name, COUNT(oi.item_id) as order_count
		FROM items i
		JOIN order_items oi ON i.id = oi.item_id
		WHERE i.organization_id = $1
		GROUP BY i.id, i.name
		ORDER BY order_count DESC
		LIMIT 1
	`, org_id).Scan(&mostOrderedItem, &mostOrderedCount)
	if err != nil && err != sql.ErrNoRows {
		pgos.Logger.Error("Failed to get most ordered item", "error", err)
		return nil, err
	}
	if mostOrderedItem.Valid {
		insights = append(insights, Insight{Title: "Most Ordered Item", Statistic: fmt.Sprintf("%s (%d orders)", mostOrderedItem.String, mostOrderedCount.Int64)})
	} else {
		insights = append(insights, Insight{Title: "Most Ordered Item", Statistic: "N/A"})
	}

	// Average employees needed to prepare items
	var avgEmployees sql.NullFloat64
	err = pgos.DB.QueryRow(`SELECT AVG(needed_num_to_prepare) FROM items WHERE organization_id = $1`, org_id).Scan(&avgEmployees)
	if err != nil {
		pgos.Logger.Error("Failed to get average employees needed", "error", err)
		return nil, err
	}
	if avgEmployees.Valid {
		insights = append(insights, Insight{Title: "Avg. Employees to Prepare", Statistic: fmt.Sprintf("%.1f", avgEmployees.Float64)})
	} else {
		insights = append(insights, Insight{Title: "Avg. Employees to Prepare", Statistic: "N/A"})
	}

	return insights, nil
}
