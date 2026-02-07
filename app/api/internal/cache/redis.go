package cache

import (
	"context"
	"encoding/json"
	"time"

	"github.com/redis/go-redis/v9"
)

// CacheService wraps Redis client for JSON caching operations
type CacheService struct {
	client *redis.Client
	ctx    context.Context
}

// NewCacheService creates a new Redis cache service
// Returns nil if Redis is unavailable (for graceful degradation)
func NewCacheService(addr, password string) (*CacheService, error) {
	client := redis.NewClient(&redis.Options{
		Addr:         addr,
		Password:     password,
		DB:           0,
		DialTimeout:  5 * time.Second,
		ReadTimeout:  3 * time.Second,
		WriteTimeout: 3 * time.Second,
		PoolSize:     10,
	})

	ctx := context.Background()

	// Test connection
	if err := client.Ping(ctx).Err(); err != nil {
		return nil, err
	}

	return &CacheService{
		client: client,
		ctx:    ctx,
	}, nil
}

// Get retrieves and unmarshals a cached value
// Returns redis.Nil error if key doesn't exist (cache miss)
func (c *CacheService) Get(key string, dest interface{}) error {
	val, err := c.client.Get(c.ctx, key).Result()
	if err != nil {
		return err // redis.Nil for cache miss
	}
	return json.Unmarshal([]byte(val), dest)
}

// Set marshals and stores a value with TTL
func (c *CacheService) Set(key string, value interface{}, ttl time.Duration) error {
	data, err := json.Marshal(value)
	if err != nil {
		return err
	}
	return c.client.Set(c.ctx, key, data, ttl).Err()
}

// Delete removes one or more keys from cache
func (c *CacheService) Delete(keys ...string) error {
	if len(keys) == 0 {
		return nil
	}
	return c.client.Del(c.ctx, keys...).Err()
}

// Close closes the Redis connection
func (c *CacheService) Close() error {
	return c.client.Close()
}

// Health checks Redis connection health
func (c *CacheService) Health() error {
	return c.client.Ping(c.ctx).Err()
}
