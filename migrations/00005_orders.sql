
-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    organization_id NOT NULL,
    request_date TIMESTAMP NOT NULL,   
    order_location_status VARCHAR(20) CHECK (order_location_status IN ("delivery","takeaway","dine in"))
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS orders; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd
