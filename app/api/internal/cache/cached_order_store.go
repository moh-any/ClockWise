package cache

import (
	"fmt"
	"time"

	"github.com/clockwise/clockwise/backend/internal/database"
	"github.com/google/uuid"
)

const (
	// Aggregated insights (counts, sums, busiest days)
	// Cache for short duration to keep dashboards relatively fresh
	OrderInsightsCacheTTL = 2 * time.Minute
)

type CachedOrderStore struct {
	store database.OrderStore
	cache *CacheService
}

func NewCachedOrderStore(store database.OrderStore, cache *CacheService) database.OrderStore {
	return &CachedOrderStore{
		store: store,
		cache: cache,
	}
}

// --- Read Operations (Lists) - DO NOT CACHE ---

func (cos *CachedOrderStore) GetAllOrdersForLastWeek(org_id uuid.UUID) ([]database.Order, error) {
	return cos.store.GetAllOrdersForLastWeek(org_id)
}

func (cos *CachedOrderStore) GetAllOrders(org_id uuid.UUID) ([]database.Order, error) {
	return cos.store.GetAllOrders(org_id)
}

func (cos *CachedOrderStore) GetTodaysOrder(org_id uuid.UUID) ([]database.Order, error) {
	return cos.store.GetTodaysOrder(org_id)
}

func (cos *CachedOrderStore) GetAllItems(org_id uuid.UUID) ([]database.Item, error) {
	return cos.store.GetAllItems(org_id)
}

func (cos *CachedOrderStore) GetAllDeliveries(org_id uuid.UUID) ([]database.OrderDelivery, error) {
	return cos.store.GetAllDeliveries(org_id)
}

func (cos *CachedOrderStore) GetAllDeliveriesForLastWeek(org_id uuid.UUID) ([]database.OrderDelivery, error) {
	return cos.store.GetAllDeliveriesForLastWeek(org_id)
}

func (cos *CachedOrderStore) GetTodaysDeliveries(org_id uuid.UUID) ([]database.OrderDelivery, error) {
	return cos.store.GetTodaysDeliveries(org_id)
}

// --- Read Operations (Computed/Aggregated) - CACHE ---

// GetOrdersInsights
// Cache key: org:{uuid}:insights:orders
func (cos *CachedOrderStore) GetOrdersInsights(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:insights:orders", org_id)

	var insights []database.Insight
	if err := cos.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cos.store.GetOrdersInsights(org_id)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, insights, OrderInsightsCacheTTL)
	return insights, nil
}

// GetDeliveryInsights
// Cache key: org:{uuid}:insights:deliveries
func (cos *CachedOrderStore) GetDeliveryInsights(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:insights:deliveries", org_id)

	var insights []database.Insight
	if err := cos.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cos.store.GetDeliveryInsights(org_id)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, insights, OrderInsightsCacheTTL)
	return insights, nil
}

// GetItemsInsights
// Cache key: org:{uuid}:insights:items
func (cos *CachedOrderStore) GetItemsInsights(org_id uuid.UUID) ([]database.Insight, error) {
	key := fmt.Sprintf("org:%s:insights:items", org_id)

	var insights []database.Insight
	if err := cos.cache.Get(key, &insights); err == nil {
		return insights, nil
	}

	insights, err := cos.store.GetItemsInsights(org_id)
	if err != nil {
		return nil, err
	}

	_ = cos.cache.Set(key, insights, OrderInsightsCacheTTL)
	return insights, nil
}

// --- Write Operations - INVALIDATE ---

// StoreOrder invalidates orders, items (stats), and optionally deliveries insights
func (cos *CachedOrderStore) StoreOrder(org_id uuid.UUID, order *database.Order) error {
	err := cos.store.StoreOrder(org_id, order)
	if err != nil {
		return err
	}

	keys := []string{
		fmt.Sprintf("org:%s:insights:orders", org_id),
		fmt.Sprintf("org:%s:insights:items", org_id), // Counts/most ordered might change
	}

	if order.OrderType == "delivery" {
		keys = append(keys, fmt.Sprintf("org:%s:insights:deliveries", org_id))
	}

	_ = cos.cache.Delete(keys...)
	return nil
}

// StoreDelivery invalidates delivery insights
func (cos *CachedOrderStore) StoreDelivery(org_id uuid.UUID, delivery *database.OrderDelivery) error {
	err := cos.store.StoreDelivery(org_id, delivery)
	if err != nil {
		return err
	}

	// Verify org_id via order lookup is complex here, so we assume caller provides correct org_id
	// or we accept imperfect invalidation. Since org_id is passed:
	_ = cos.cache.Delete(fmt.Sprintf("org:%s:insights:deliveries", org_id))
	return nil
}

// StoreOrderItems invalidates orders and items insights
func (cos *CachedOrderStore) StoreOrderItems(org_id uuid.UUID, order_id uuid.UUID, orderItem *database.OrderItem) error {
	err := cos.store.StoreOrderItems(org_id, order_id, orderItem)
	if err != nil {
		return err
	}

	_ = cos.cache.Delete(
		fmt.Sprintf("org:%s:insights:orders", org_id),
		fmt.Sprintf("org:%s:insights:items", org_id),
	)
	return nil
}

// StoreItems invalidates items insights
func (cos *CachedOrderStore) StoreItems(org_id uuid.UUID, item *database.Item) error {
	err := cos.store.StoreItems(org_id, item)
	if err != nil {
		return err
	}

	_ = cos.cache.Delete(fmt.Sprintf("org:%s:insights:items", org_id))
	return nil
}
