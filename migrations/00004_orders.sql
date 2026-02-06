-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp"; 
CREATE TABLE IF NOT EXISTS orders (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    organization_id UUID NOT NULL REFERENCES organizations(id),
    create_time TIMESTAMP NOT NULL,   
    order_type VARCHAR(10) NOT NULL CHECK (order_type IN ('delivery','takeaway','dine in')),
    order_status VARCHAR(10) NOT NULL CHECK (order_status IN ('closed','cancelled')),
    total_amount DECIMAL(10,2) NOT NULL CHECK (total_amount >= 0),
    discount_amount DECIMAL(10,2) NOT NULL CHECK (discount_amount >= 0 AND total_amount - discount_amount >= 0),
    rating DECIMAL(10,2) 
);

CREATE TABLE IF NOT EXISTS items (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID NOT NULL REFERENCES organizations(id),
    name VARCHAR(50) NOT NULL,
    needed_num_to_prepare INTEGER NOT NULL,
    price DECIMAL(10,2) NOT NULL CHECK (price >= 0.0)
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id UUID REFERENCES orders(id),
    item_id UUID REFERENCES items(id),
    quantity INTEGER NOT NULL CHECK(quantity >= 1), 
    total_price DECIMAL(10,2) NOT NULL CHECK(total_price >= 0.0),
    PRIMARY KEY (order_id, item_id)
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS orders, items, order_items CASCADE; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd
