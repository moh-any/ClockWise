package database

import "database/sql"

type InsightStore interface {
	GetInsightsForAdmin() error
	GetInsightsForManager() error
	GetInsightsForEmployee() error
}

type PostgresInsightStore struct {
	DB *sql.DB
}

