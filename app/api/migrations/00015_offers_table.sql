-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS over_time_offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES users(id),
    status VARCHAR(100) CHECK (status IN ('accepted','declined','in queue')),
    shift_length INTEGER CHECK (shift_length >= 0),
    start_time TIMESTAMP CHECK (start_time >= CURRENT_TIMESTAMP),
    updated_time TIMESTAMP NOT NULL
);
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS over_time_offers;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd