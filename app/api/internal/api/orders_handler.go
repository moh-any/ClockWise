package api

import (
	"log/slog"
	"net/http"
	"strconv"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/clockwise/clockwise/backend/internal/middleware"
	"github.com/clockwise/clockwise/backend/internal/service"
	"github.com/gin-gonic/gin"
	"github.com/google/uuid"
)

type OrderHandler struct {
	OrderStore       database.OrderStore
	UploadCSVService service.UploadService
	Logger           *slog.Logger
}

func NewOrderHandler(orderStore database.OrderStore, uploadservice service.UploadService, Logger *slog.Logger) *OrderHandler {
	return &OrderHandler{
		OrderStore:       orderStore,
		UploadCSVService: uploadservice,
		Logger:           Logger,
	}
}

// GetAllOrders godoc
// @Summary      Get all orders
// @Description  Returns all orders for the organization
// @Tags         Orders
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of orders"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders [get]
func (oh *OrderHandler) GetAllOrders(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	oh.Logger.Info("getting all orders", "org_id", user.OrganizationID)

	orders, err := oh.OrderStore.GetAllOrders(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get all orders", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve orders"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Orders retrieved successfully",
		"data":    orders,
	})
}

// GetAllOrdersForLastWeek godoc
// @Summary      Get orders from last week
// @Description  Returns all orders from the last 7 days for the organization
// @Tags         Orders
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of orders from last week"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders/last-week [get]
func (oh *OrderHandler) GetAllOrdersForLastWeek(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	oh.Logger.Info("getting orders for last week", "org_id", user.OrganizationID)

	orders, err := oh.OrderStore.GetAllOrdersForLastWeek(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get orders for last week", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve orders"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Orders retrieved successfully",
		"data":    orders,
	})
}

// GetAllOrdersToday godoc
// @Summary      Get today's orders
// @Description  Returns all orders from today for the organization
// @Tags         Orders
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of today's orders"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders/today [get]
func (oh *OrderHandler) GetAllOrdersToday(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	oh.Logger.Info("getting today's orders", "org_id", user.OrganizationID)

	orders, err := oh.OrderStore.GetTodaysOrder(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get today's orders", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve orders"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Orders retrieved successfully",
		"data":    orders,
	})
}

// GetOrdersInsights godoc
// @Summary      Get orders insights
// @Description  Returns insights/analytics for orders
// @Tags         Orders
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "Order insights"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders/insights [get]
func (oh *OrderHandler) GetOrdersInsights(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access orders"})
		return
	}

	oh.Logger.Info("getting orders insights", "org_id", user.OrganizationID)

	insights, err := oh.OrderStore.GetOrdersInsights(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get orders insights", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve order insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Order insights retrieved successfully",
		"data":    insights,
	})
}

// UploadAllPastOrdersCSV godoc
// @Summary      Upload past orders CSV
// @Description  Upload a CSV file containing past orders data
// @Tags         Orders
// @Accept       multipart/form-data
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        file formData file true "CSV file with orders data"
// @Success      200 {object} map[string]interface{} "Upload successful with parsed data"
// @Failure      400 {object} map[string]string "Bad request"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders/upload [post]
func (oh *OrderHandler) UploadAllPastOrdersCSV(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload orders"})
		return
	}

	oh.Logger.Info("uploading past orders CSV", "org_id", user.OrganizationID)

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		oh.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	// Parse the CSV file
	csvData, err := oh.UploadCSVService.ParseCSV(file)
	if err != nil {
		oh.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: user_id, create_time, order_type, order_status, total_amount, discount_amount, rating
	requiredColumns := []string{"order_id", "user_id", "create_time", "order_type", "order_status", "total_amount", "discount_amount"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			oh.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Store each order from CSV
	var successCount, errorCount int
	for i, row := range csvData.Rows {
		orderID, err := uuid.Parse(row["order_id"])
		if err != nil {
			oh.Logger.Warn("invalid order_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse user_id
		userID, err := uuid.Parse(row["user_id"])
		if err != nil {
			oh.Logger.Warn("invalid user_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse create_time
		createTime, err := time.Parse(time.RFC3339, row["create_time"])
		if err != nil {
			// Try alternative format
			createTime, err = time.Parse("2006-01-02 15:04:05", row["create_time"])
			if err != nil {
				oh.Logger.Warn("invalid create_time in row", "row", i, "error", err)
				errorCount++
				continue
			}
		}

		// Parse total_amount
		totalAmount, err := strconv.ParseFloat(row["total_amount"], 64)
		if err != nil {
			oh.Logger.Warn("invalid total_amount in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse discount_amount
		discountAmount, err := strconv.ParseFloat(row["discount_amount"], 64)
		if err != nil {
			oh.Logger.Warn("invalid discount_amount in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse rating (optional)
		var rating *float64
		if row["rating"] != "" {
			r, err := strconv.ParseFloat(row["rating"], 64)
			if err == nil {
				rating = &r
			}
		}

		order := &database.Order{
			OrderID:        orderID,
			UserID:         userID,
			OrganizationID: user.OrganizationID,
			CreateTime:     createTime,
			OrderType:      row["order_type"],
			OrderStatus:    row["order_status"],
			TotalAmount:    &totalAmount,
			DiscountAmount: &discountAmount,
			Rating:         rating,
		}

		err = oh.OrderStore.StoreOrder(user.OrganizationID, order)
		if err != nil {
			oh.Logger.Error("failed to store order", "row", i, "error", err)
			errorCount++
			continue
		}
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Orders CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

// UploadOrderItemsCSV godoc
// @Summary      Upload order items CSV
// @Description  Upload a CSV file containing order items data
// @Tags         Orders
// @Accept       multipart/form-data
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        file formData file true "CSV file with order items data"
// @Success      200 {object} map[string]interface{} "Upload successful with parsed data"
// @Failure      400 {object} map[string]string "Bad request"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/orders/items/upload [post]
func (oh *OrderHandler) UploadOrderItemsCSV(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload order items"})
		return
	}

	oh.Logger.Info("uploading order items CSV", "org_id", user.OrganizationID)

	// Verify that orders and items exist before allowing order_items upload
	existingOrders, err := oh.OrderStore.GetAllOrders(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to check existing orders", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify existing orders"})
		return
	}
	if len(existingOrders) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "You must import at least one order before uploading order items"})
		return
	}

	existingItems, err := oh.OrderStore.GetAllItems(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to check existing items", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify existing items"})
		return
	}
	if len(existingItems) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "You must import at least one item before uploading order items"})
		return
	}

	// TODO Add existing items and orders to Redis Cache

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		oh.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	// Parse the CSV file
	csvData, err := oh.UploadCSVService.ParseCSV(file)
	if err != nil {
		oh.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: order_id, item_id, quantity, total_price
	requiredColumns := []string{"order_id", "item_id", "quantity", "total_price"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			oh.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Store each order item link from CSV
	var successCount, errorCount int
	for i, row := range csvData.Rows {
		// Parse order_id
		orderID, err := uuid.Parse(row["order_id"])
		if err != nil {
			oh.Logger.Warn("invalid order_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse item_id
		itemID, err := uuid.Parse(row["item_id"])
		if err != nil {
			oh.Logger.Warn("invalid item_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse quantity
		quantity, err := strconv.Atoi(row["quantity"])
		if err != nil {
			oh.Logger.Warn("invalid quantity in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse total_price
		totalPrice, err := strconv.ParseFloat(row["total_price"], 32)
		if err != nil {
			oh.Logger.Warn("invalid total_price in row", "row", i, "error", err)
			errorCount++
			continue
		}

		orderItem := &database.OrderItem{
			ItemID:     itemID,
			Quantity:   &quantity,
			TotalPrice: &totalPrice,
		}

		err = oh.OrderStore.StoreOrderItems(user.OrganizationID, orderID, orderItem)
		if err != nil {
			oh.Logger.Error("failed to store order item", "row", i, "error", err)
			errorCount++
			continue
		}
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Order items CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

// GetAllDeliveries godoc
// @Summary      Get all deliveries
// @Description  Returns all deliveries for the organization
// @Tags         Deliveries
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of deliveries"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/deliveries [get]
func (oh *OrderHandler) GetAllDeliveries(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access deliveries"})
		return
	}

	oh.Logger.Info("getting all deliveries", "org_id", user.OrganizationID)

	deliveries, err := oh.OrderStore.GetAllDeliveries(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get all deliveries", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve deliveries"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Deliveries retrieved successfully",
		"data":    deliveries,
	})
}

// GetAllDeliveriesForLastWeek godoc
// @Summary      Get deliveries from last week
// @Description  Returns all deliveries from the last 7 days for the organization
// @Tags         Deliveries
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of deliveries from last week"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/deliveries/last-week [get]
func (oh *OrderHandler) GetAllDeliveriesForLastWeek(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access deliveries"})
		return
	}

	oh.Logger.Info("getting deliveries for last week", "org_id", user.OrganizationID)

	deliveries, err := oh.OrderStore.GetAllDeliveriesForLastWeek(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get deliveries for last week", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve deliveries"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Deliveries retrieved successfully",
		"data":    deliveries,
	})
}

// GetAllDeliveriesToday godoc
// @Summary      Get today's deliveries
// @Description  Returns all deliveries from today for the organization
// @Tags         Deliveries
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of today's deliveries"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/deliveries/today [get]
func (oh *OrderHandler) GetAllDeliveriesToday(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access deliveries"})
		return
	}

	oh.Logger.Info("getting today's deliveries", "org_id", user.OrganizationID)

	deliveries, err := oh.OrderStore.GetTodaysDeliveries(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get today's deliveries", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve deliveries"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Deliveries retrieved successfully",
		"data":    deliveries,
	})
}

// GetDeliveryInsights godoc
// @Summary      Get delivery insights
// @Description  Returns insights/analytics for deliveries
// @Tags         Deliveries
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "Delivery insights"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/deliveries/insights [get]
func (oh *OrderHandler) GetDeliveryInsights(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access deliveries"})
		return
	}

	oh.Logger.Info("getting delivery insights", "org_id", user.OrganizationID)

	insights, err := oh.OrderStore.GetDeliveryInsights(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get delivery insights", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve delivery insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Delivery insights retrieved successfully",
		"data":    insights,
	})
}

// UploadAllPastDeliveriesCSV godoc
// @Summary      Upload past deliveries CSV
// @Description  Upload a CSV file containing past deliveries data
// @Tags         Deliveries
// @Accept       multipart/form-data
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        file formData file true "CSV file with deliveries data"
// @Success      200 {object} map[string]interface{} "Upload successful with parsed data"
// @Failure      400 {object} map[string]string "Bad request"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/deliveries/upload [post]
func (oh *OrderHandler) UploadAllPastDeliveriesCSV(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload deliveries"})
		return
	}

	oh.Logger.Info("uploading past deliveries CSV", "org_id", user.OrganizationID)

	// Verify that orders exist before allowing deliveries upload
	existingOrders, err := oh.OrderStore.GetAllOrders(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to check existing orders", "error", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to verify existing orders"})
		return
	}
	if len(existingOrders) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "You must import at least one order before uploading deliveries"})
		return
	}

	// TODO Add to cache

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		oh.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	// Parse the CSV file
	csvData, err := oh.UploadCSVService.ParseCSV(file)
	if err != nil {
		oh.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: order_id, driver_id, delivery_latitude, delivery_longitude, out_for_delivery_time, delivered_time, status
	requiredColumns := []string{"order_id", "driver_id", "out_for_delivery_time", "status"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			oh.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Store each delivery from CSV
	var successCount, errorCount int
	for i, row := range csvData.Rows {
		// Parse order_id
		orderID, err := uuid.Parse(row["order_id"])
		if err != nil {
			oh.Logger.Warn("invalid order_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse driver_id
		driverID, err := uuid.Parse(row["driver_id"])
		if err != nil {
			oh.Logger.Warn("invalid driver_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse out_for_delivery_time
		outForDeliveryTime, err := time.Parse(time.RFC3339, row["out_for_delivery_time"])
		if err != nil {
			outForDeliveryTime, err = time.Parse("2006-01-02 15:04:05", row["out_for_delivery_time"])
			if err != nil {
				oh.Logger.Warn("invalid out_for_delivery_time in row", "row", i, "error", err)
				errorCount++
				continue
			}
		}

		// Parse delivered_time (optional)
		var deliveredTime time.Time
		if row["delivered_time"] != "" {
			deliveredTime, err = time.Parse(time.RFC3339, row["delivered_time"])
			if err != nil {
				deliveredTime, _ = time.Parse("2006-01-02 15:04:05", row["delivered_time"])
			}
		}

		// Parse latitude (optional)
		var latitude *float64
		if row["delivery_latitude"] != "" {
			if lat, err := strconv.ParseFloat(row["delivery_latitude"], 64); err == nil {
				latitude = &lat
			}
		}

		// Parse longitude (optional)
		var longitude *float64
		if row["delivery_longitude"] != "" {
			if lon, err := strconv.ParseFloat(row["delivery_longitude"], 64); err == nil {
				longitude = &lon
			}
		}

		delivery := &database.OrderDelivery{
			OrderID:            orderID,
			DriverID:           driverID,
			OutForDeliveryTime: outForDeliveryTime,
			DeliveredTime:      deliveredTime,
			DeliveryStatus:     row["status"],
			DeliveryLocation: database.Location{
				Latitude:  latitude,
				Longitude: longitude,
			},
		}

		err = oh.OrderStore.StoreDelivery(user.OrganizationID, delivery)
		if err != nil {
			oh.Logger.Error("failed to store delivery", "row", i, "error", err)
			errorCount++
			continue
		}
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Deliveries CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

// GetItemsInsights godoc
// @Summary      Get items insights
// @Description  Returns insights/analytics for items
// @Tags         Items
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "Item insights"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/items/insights [get]
func (oh *OrderHandler) GetItemsInsights(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access items"})
		return
	}

	oh.Logger.Info("getting items insights", "org_id", user.OrganizationID)

	insights, err := oh.OrderStore.GetItemsInsights(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get items insights", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve item insights"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Item insights retrieved successfully",
		"data":    insights,
	})
}

// UploadItemsCSV godoc
// @Summary      Upload items CSV
// @Description  Upload a CSV file containing items data
// @Tags         Items
// @Accept       multipart/form-data
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Param        file formData file true "CSV file with items data"
// @Success      200 {object} map[string]interface{} "Upload successful"
// @Failure      400 {object} map[string]string "Bad request"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/items/upload [post]
func (oh *OrderHandler) UploadItemsCSV(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can upload items"})
		return
	}

	oh.Logger.Info("uploading items CSV", "org_id", user.OrganizationID)

	// Get the file from the request
	file, _, err := c.Request.FormFile("file")
	if err != nil {
		oh.Logger.Error("failed to get file from request", "error", err)
		c.JSON(http.StatusBadRequest, gin.H{"error": "Failed to get file from request"})
		return
	}
	defer file.Close()

	// Parse the CSV file
	csvData, err := oh.UploadCSVService.ParseCSV(file)
	if err != nil {
		oh.Logger.Error("failed to parse CSV", "error", err)
		if err == service.ErrEmptyFile {
			c.JSON(http.StatusBadRequest, gin.H{"error": "CSV file is empty"})
			return
		}
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid CSV format"})
		return
	}

	// Expected columns: name, needed_employees, price
	requiredColumns := []string{"item_id", "name", "needed_employees", "price"}
	for _, col := range requiredColumns {
		found := false
		for _, header := range csvData.Headers {
			if header == col {
				found = true
				break
			}
		}
		if !found {
			oh.Logger.Warn("missing required column", "column", col)
			c.JSON(http.StatusBadRequest, gin.H{"error": "Missing required column: " + col})
			return
		}
	}

	// Store each item from CSV
	var successCount, errorCount int
	for i, row := range csvData.Rows {
		itemID, err := uuid.Parse(row["item_id"])
		if err != nil {
			oh.Logger.Warn("invalid item_id in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse needed_employees
		neededEmployees, err := strconv.Atoi(row["needed_employees"])
		if err != nil {
			oh.Logger.Warn("invalid needed_employees in row", "row", i, "error", err)
			errorCount++
			continue
		}

		// Parse price
		price, err := strconv.ParseFloat(row["price"], 64)
		if err != nil {
			oh.Logger.Warn("invalid price in row", "row", i, "error", err)
			errorCount++
			continue
		}

		item := &database.Item{
			ItemID:                      itemID,
			Name:                        row["name"],
			NeededNumEmployeesToPrepare: &neededEmployees,
			Price:                       &price,
		}

		err = oh.OrderStore.StoreItems(user.OrganizationID, item)
		if err != nil {
			oh.Logger.Error("failed to store item", "row", i, "error", err)
			errorCount++
			continue
		}
		successCount++
	}

	c.JSON(http.StatusOK, gin.H{
		"message":       "Items CSV uploaded successfully",
		"total_rows":    csvData.Total,
		"success_count": successCount,
		"error_count":   errorCount,
	})
}

// GetAllItems godoc
// @Summary      Get all items
// @Description  Returns all items for the organization
// @Tags         Items
// @Accept       json
// @Produce      json
// @Security     BearerAuth
// @Param        org path string true "Organization ID"
// @Success      200 {object} map[string]interface{} "List of items"
// @Failure      401 {object} map[string]string "Unauthorized"
// @Failure      500 {object} map[string]string "Internal server error"
// @Router       /{org}/items [get]
func (oh *OrderHandler) GetAllItems(c *gin.Context) {
	user := middleware.ValidateOrgAccess(c)
	if user == nil {
		return
	}

	if user.UserRole != "admin" && user.UserRole != "manager" {
		c.JSON(http.StatusForbidden, gin.H{"error": "Only admins and managers can access items"})
		return
	}

	oh.Logger.Info("getting all items", "org_id", user.OrganizationID)

	items, err := oh.OrderStore.GetAllItems(user.OrganizationID)
	if err != nil {
		oh.Logger.Error("failed to get all items", "error", err, "org_id", user.OrganizationID)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to retrieve items"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"message": "Items retrieved successfully",
		"data":    items,
	})
}
