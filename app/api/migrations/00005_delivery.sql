-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS deliveries (
    order_id UUID PRIMARY KEY REFERENCES orders(id), 
    driver_id UUID,
    delivery_latitude DECIMAL(10,7),
    delivery_longitude DECIMAL(10,7),
    out_for_delivery_time TIMESTAMP NOT NULL,
    delivered_time TIMESTAMP,
    status VARCHAR(20) CHECK (status IN ('delivered','out for delivery','not delivered'))
);
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS deliveries; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd