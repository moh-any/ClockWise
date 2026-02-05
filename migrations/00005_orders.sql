-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    request_date TIMESTAMP NOT NULL,   
    order_location_status VARCHAR(20) CHECK (order_location_status IN ('delivery','takeaway','dine in'))
);

CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(50) NOT NULL,
    needed_num_to_prepare INTEGER NOT NULL,
    price DECIMAL(10,2) INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id UUID REFERENCES orders(id),
    item_id UUID REFERENCES items(id),
    PRIMARY KEY (order_id, item_id)
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS orders, items, orders_items CASCADE; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd
