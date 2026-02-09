-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS over_time_offers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    employee_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    status VARCHAR(100) CHECK (status IN ('accepted','declined','in queue')),
    shift_length INTEGER NOT NULL CHECK (shift_length >= 0),
    start_time TIMESTAMP NOT NULL CHECK (start_time >= CURRENT_TIMESTAMP),
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE OR REPLACE FUNCTION auto_decline()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE over_time_offers SET status='declined' AND updated_at= CURRENT_TIMESTAMP WHERE status != 'accepted' AND start_time <= CURRENT_TIMESTAMP;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_auto_decline
AFTER INSERT OR UPDATE ON over_time_offers
FOR EACH STATEMENT
EXECUTE FUNCTION auto_decline();


-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS over_time_offers;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd