package database

import (
	"database/sql"
	"log/slog"
)

type DemandStore interface {

}

type PostgresDemandStore struct {
	DB     *sql.DB
	Logger *slog.Logger
}

func NewPostgresDemandStore(DB *sql.DB, Logger *slog.Logger) *PostgresDemandStore {
	return &PostgresDemandStore{
		DB:     DB,
		Logger: Logger,
	}
}
