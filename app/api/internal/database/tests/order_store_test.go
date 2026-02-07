package database

import (
	"fmt"
	"regexp"
	"testing"
	"time"

	"github.com/DATA-DOG/go-sqlmock"
	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
	"github.com/stretchr/testify/assert"
)

func TestGetAllOrders(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)

	orgID := uuid.New()
	orderID1 := uuid.New()
	orderID2 := uuid.New()
	userID := uuid.New()
	now := time.Now()

	// Queries used in GetAllOrders
	qSelectOrders := regexp.QuoteMeta(`SELECT id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating FROM orders WHERE organization_id = $1 ORDER BY create_time DESC`)
	qSelectItems := regexp.QuoteMeta(`SELECT order_id, item_id, quantity, total_price FROM order_items WHERE order_id IN ($1, $2)`)
	qSelectDeliveries := regexp.QuoteMeta(`SELECT order_id, driver_id, delivery_latitude, delivery_longitude, out_for_delivery_time, delivered_time, status FROM deliveries WHERE order_id IN ($1, $2)`)

	t.Run("Success_WithItemsAndDeliveries", func(t *testing.T) {
		// 1. Mock Orders Query
		rowsOrders := sqlmock.NewRows([]string{"id", "user_id", "organization_id", "create_time", "order_type", "order_status", "total_amount", "discount_amount", "rating"}).
			AddRow(orderID1, userID, orgID, now, "dine in", "closed", 50.0, 0.0, 5.0).
			AddRow(orderID2, userID, orgID, now, "delivery", "closed", 30.0, 5.0, 4.0)
		mock.ExpectQuery(qSelectOrders).WithArgs(orgID).WillReturnRows(rowsOrders)

		// 2. Mock Items Query (populateOrderItems)
		rowsItems := sqlmock.NewRows([]string{"order_id", "item_id", "quantity", "total_price"}).
			AddRow(orderID1, uuid.New(), 2, 20.0).
			AddRow(orderID2, uuid.New(), 1, 15.0)
		mock.ExpectQuery(qSelectItems).WithArgs(orderID1, orderID2).WillReturnRows(rowsItems)

		// 3. Mock Deliveries Query (populateDeliveries)
		// Note: Only order 2 is a delivery type, but the query fetches for all IDs in the list to be safe or based on logic.
		// The store implementation builds IN clause for ALL retrieved orders.
		rowsDeliveries := sqlmock.NewRows([]string{"order_id", "driver_id", "delivery_latitude", "delivery_longitude", "out_for_delivery_time", "delivered_time", "status"}).
			AddRow(orderID2, uuid.New(), 10.0, 20.0, now, now.Add(time.Hour), "delivered")
		mock.ExpectQuery(qSelectDeliveries).WithArgs(orderID1, orderID2).WillReturnRows(rowsDeliveries)

		orders, err := store.GetAllOrders(orgID)

		assert.NoError(t, err)
		assert.Len(t, orders, 2)

		// Check Order 1
		assert.Equal(t, orderID1, orders[0].OrderID)
		assert.Len(t, orders[0].OrderItems, 1)
		assert.Nil(t, orders[0].DeliveryStatus) // Dine in, no delivery record returned

		// Check Order 2
		assert.Equal(t, orderID2, orders[1].OrderID)
		assert.Len(t, orders[1].OrderItems, 1)
		assert.NotNil(t, orders[1].DeliveryStatus)
		assert.Equal(t, "delivered", orders[1].DeliveryStatus.DeliveryStatus)

		AssertExpectations(t, mock)
	})

	t.Run("DBError_Orders", func(t *testing.T) {
		mock.ExpectQuery(qSelectOrders).WithArgs(orgID).WillReturnError(fmt.Errorf("db error"))
		orders, err := store.GetAllOrders(orgID)
		assert.Error(t, err)
		assert.Nil(t, orders)
		AssertExpectations(t, mock)
	})
}

func TestStoreOrder(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)

	orgID := uuid.New()
	orderID := uuid.New()
	itemID := uuid.New()
	driverID := uuid.New()
	now := time.Now()

	t.Run("Success_DeliveryOrder", func(t *testing.T) {
		order := &database.Order{
			OrderID:        orderID,
			UserID:         uuid.New(),
			OrganizationID: orgID,
			CreateTime:     now,
			OrderType:      "delivery",
			OrderStatus:    "closed",
			TotalAmount:    func() *float64 { f := 50.0; return &f }(),
			DiscountAmount: func() *float64 { f := 0.0; return &f }(),
			Rating:         func() *float64 { f := 5.0; return &f }(),
			OrderItems: []database.OrderItem{
				{ItemID: itemID, Quantity: func() *int { i := 2; return &i }(), TotalPrice: func() *float64 { i := 50.0; return &i }()},
			},
			DeliveryStatus: &database.OrderDelivery{
				DriverID:           driverID,
				DeliveryLocation:   database.Location{Latitude: func() *float64 { f := 1.0; return &f }(), Longitude: func() *float64 { f := 2.0; return &f }()},
				OutForDeliveryTime: now,
				DeliveredTime:      now.Add(1 * time.Hour),
				DeliveryStatus:     "delivered",
			},
		}

		mock.ExpectBegin()

		// 1. Insert Order
		qInsertOrder := regexp.QuoteMeta(`INSERT INTO orders (id, user_id, organization_id, create_time, order_type, order_status, total_amount, discount_amount, rating) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)`)
		mock.ExpectExec(qInsertOrder).
			WithArgs(order.OrderID, order.UserID, orgID, order.CreateTime, order.OrderType, order.OrderStatus, order.TotalAmount, order.DiscountAmount, order.Rating).
			WillReturnResult(sqlmock.NewResult(1, 1))

		// 2. Insert Delivery
		qInsertDelivery := regexp.QuoteMeta(`INSERT INTO deliveries (order_id, driver_id, delivery_latitude, delivery_longitude, out_for_delivery_time, delivered_time, status) VALUES ($1, $2, $3, $4, $5, $6, $7)`)
		mock.ExpectExec(qInsertDelivery).
			WithArgs(order.OrderID, order.DeliveryStatus.DriverID, order.DeliveryStatus.DeliveryLocation.Latitude, order.DeliveryStatus.DeliveryLocation.Longitude, order.DeliveryStatus.OutForDeliveryTime, order.DeliveryStatus.DeliveredTime, order.DeliveryStatus.DeliveryStatus).
			WillReturnResult(sqlmock.NewResult(1, 1))

		mock.ExpectCommit()

		// 3. StoreOrderItems (Called after commit in implementation)
		// Check order exists
		mock.ExpectQuery(regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM orders WHERE id = $1 AND organization_id = $2)`)).
			WithArgs(orderID, orgID).WillReturnRows(NewRow(true))

		// Check item exists
		mock.ExpectQuery(regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM items WHERE id = $1 AND organization_id = $2)`)).
			WithArgs(itemID, orgID).WillReturnRows(NewRow(true))

		// Upsert Item
		qUpsertItem := regexp.QuoteMeta(`INSERT INTO order_items (order_id, item_id, quantity, total_price) VALUES ($1, $2, $3, $4) ON CONFLICT (order_id, item_id) DO UPDATE SET quantity = order_items.quantity + EXCLUDED.quantity, total_price = order_items.total_price + EXCLUDED.total_price`)
		mock.ExpectExec(qUpsertItem).
			WithArgs(orderID, itemID, 2, order.OrderItems[0].TotalPrice).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.StoreOrder(orgID, order)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("Failure_TransactionRollback", func(t *testing.T) {
		order := &database.Order{
			OrderID: orderID,
			UserID:  uuid.New(),
			// ... minimal fields
		}

		mock.ExpectBegin()
		mock.ExpectExec(regexp.QuoteMeta(`INSERT INTO orders`)).WillReturnError(fmt.Errorf("insert failed"))
		mock.ExpectRollback()

		err := store.StoreOrder(orgID, order)
		assert.Error(t, err)
		AssertExpectations(t, mock)
	})
}

func TestGetOrdersInsights(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)
	orgID := uuid.New()

	// Queries
	qTotal := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1`)
	qWeekly := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND create_time >= NOW() - INTERVAL '7 days'`)
	qToday := regexp.QuoteMeta(`SELECT COUNT(*) FROM orders WHERE organization_id = $1 AND DATE(create_time) = CURRENT_DATE`)
	qBusiestDay := regexp.QuoteMeta(`SELECT TO_CHAR(create_time, 'Day') as day_name FROM orders WHERE organization_id = $1 GROUP BY TO_CHAR(create_time, 'Day'), EXTRACT(DOW FROM create_time) ORDER BY COUNT(*) DESC LIMIT 1`)
	qBusiestHour := regexp.QuoteMeta(`SELECT EXTRACT(HOUR FROM create_time)::int as hour FROM orders WHERE organization_id = $1 GROUP BY EXTRACT(HOUR FROM create_time) ORDER BY COUNT(*) DESC LIMIT 1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(qTotal).WithArgs(orgID).WillReturnRows(NewRow(100))
		mock.ExpectQuery(qWeekly).WithArgs(orgID).WillReturnRows(NewRow(20))
		mock.ExpectQuery(qToday).WithArgs(orgID).WillReturnRows(NewRow(5))

		mock.ExpectQuery(qBusiestDay).WithArgs(orgID).WillReturnRows(NewRow("Friday"))
		mock.ExpectQuery(qBusiestHour).WithArgs(orgID).WillReturnRows(NewRow(18))

		insights, err := store.GetOrdersInsights(orgID)

		assert.NoError(t, err)
		assert.Len(t, insights, 5)
		assert.Equal(t, "Total Orders (All Time)", insights[0].Title)
		assert.Equal(t, "100", insights[0].Statistic)
		assert.Equal(t, "Busiest Day (Orders)", insights[3].Title)
		assert.Equal(t, "Friday", insights[3].Statistic)
		assert.Equal(t, "Busiest Hour (Orders)", insights[4].Title)
		assert.Equal(t, "18:00", insights[4].Statistic)

		AssertExpectations(t, mock)
	})
}

func TestStoreItems(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)
	orgID := uuid.New()

	item := &database.Item{
		ItemID:                      uuid.New(),
		Name:                        "Burger",
		NeededNumEmployeesToPrepare: func() *int { i := 2; return &i }(),
		Price:                       func() *float64 { f := 10.5; return &f }(),
	}

	qCheck := regexp.QuoteMeta(`SELECT EXISTS(SELECT 1 FROM items WHERE organization_id = $1 AND name = $2)`)
	qInsert := regexp.QuoteMeta(`INSERT INTO items (id,organization_id, name, needed_num_to_prepare, price) VALUES ($1, $2, $3, $4, $5)`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(qCheck).WithArgs(orgID, item.Name).WillReturnRows(NewRow(false))
		mock.ExpectExec(qInsert).
			WithArgs(item.ItemID, orgID, item.Name, item.NeededNumEmployeesToPrepare, item.Price).
			WillReturnResult(sqlmock.NewResult(1, 1))

		err := store.StoreItems(orgID, item)
		assert.NoError(t, err)
		AssertExpectations(t, mock)
	})

	t.Run("Failure_Duplicate", func(t *testing.T) {
		mock.ExpectQuery(qCheck).WithArgs(orgID, item.Name).WillReturnRows(NewRow(true))

		err := store.StoreItems(orgID, item)
		assert.Error(t, err)
		assert.Contains(t, err.Error(), "already exists")
		AssertExpectations(t, mock)
	})
}

func TestGetAllItems(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)
	orgID := uuid.New()

	q := regexp.QuoteMeta(`SELECT id, name, needed_num_to_prepare, price FROM items WHERE organization_id = $1 ORDER BY name ASC`)

	t.Run("Success", func(t *testing.T) {
		rows := sqlmock.NewRows([]string{"id", "name", "needed_num_to_prepare", "price"}).
			AddRow(uuid.New(), "Burger", 2, 10.0).
			AddRow(uuid.New(), "Fries", 1, 5.0)

		mock.ExpectQuery(q).WithArgs(orgID).WillReturnRows(rows)

		items, err := store.GetAllItems(orgID)
		assert.NoError(t, err)
		assert.Len(t, items, 2)
		assert.Equal(t, "Burger", items[0].Name)
		AssertExpectations(t, mock)
	})
}

func TestGetItemsInsights(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)
	orgID := uuid.New()

	qCount := regexp.QuoteMeta(`SELECT COUNT(*) FROM items WHERE organization_id = $1`)
	qAvgPrice := regexp.QuoteMeta(`SELECT AVG(price) FROM items WHERE organization_id = $1`)
	qMostExpensive := regexp.QuoteMeta(`SELECT name, price FROM items WHERE organization_id = $1 ORDER BY price DESC LIMIT 1`)
	qMostOrdered := regexp.QuoteMeta(`SELECT i.name, COUNT(oi.item_id) as order_count FROM items i JOIN order_items oi ON i.id = oi.item_id WHERE i.organization_id = $1 GROUP BY i.id, i.name ORDER BY order_count DESC LIMIT 1`)
	qAvgEmployees := regexp.QuoteMeta(`SELECT AVG(needed_num_to_prepare) FROM items WHERE organization_id = $1`)

	t.Run("Success", func(t *testing.T) {
		mock.ExpectQuery(qCount).WithArgs(orgID).WillReturnRows(NewRow(50))
		mock.ExpectQuery(qAvgPrice).WithArgs(orgID).WillReturnRows(NewRow(12.5))

		mock.ExpectQuery(qMostExpensive).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"name", "price"}).AddRow("Steak", 50.0),
		)

		mock.ExpectQuery(qMostOrdered).WithArgs(orgID).WillReturnRows(
			sqlmock.NewRows([]string{"name", "order_count"}).AddRow("Fries", 200),
		)

		mock.ExpectQuery(qAvgEmployees).WithArgs(orgID).WillReturnRows(NewRow(1.5))

		insights, err := store.GetItemsInsights(orgID)
		assert.NoError(t, err)
		assert.Len(t, insights, 5)

		assert.Equal(t, "Total Items", insights[0].Title)
		assert.Equal(t, "50", insights[0].Statistic)

		assert.Equal(t, "Most Expensive Item", insights[2].Title)
		assert.Contains(t, insights[2].Statistic, "Steak")

		assert.Equal(t, "Most Ordered Item", insights[3].Title)
		assert.Contains(t, insights[3].Statistic, "Fries")

		AssertExpectations(t, mock)
	})
}

func TestGetAllDeliveries(t *testing.T) {
	db, mock := NewTestDB(t)
	logger := NewTestLogger()
	store := database.NewPostgresOrderStore(db, logger)
	orgID := uuid.New()

	q := regexp.QuoteMeta(`SELECT d.order_id, d.driver_id, d.delivery_latitude, d.delivery_longitude, d.out_for_delivery_time, d.delivered_time, d.status FROM deliveries d JOIN orders o ON d.order_id = o.id WHERE o.organization_id = $1 ORDER BY d.out_for_delivery_time DESC`)

	t.Run("Success", func(t *testing.T) {
		now := time.Now()
		rows := sqlmock.NewRows([]string{"order_id", "driver_id", "delivery_latitude", "delivery_longitude", "out_for_delivery_time", "delivered_time", "status"}).
			AddRow(uuid.New(), uuid.New(), 1.0, 1.0, now, now.Add(time.Hour), "delivered")

		mock.ExpectQuery(q).WithArgs(orgID).WillReturnRows(rows)

		deliveries, err := store.GetAllDeliveries(orgID)
		assert.NoError(t, err)
		assert.Len(t, deliveries, 1)
		assert.Equal(t, "delivered", deliveries[0].DeliveryStatus)
		AssertExpectations(t, mock)
	})
}
