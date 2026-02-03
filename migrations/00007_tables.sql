
-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS tables (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id) 
);

CREATE TABLE IF NOT EXISTS order_tables (
    table_id UUID REFERENCES tables(id), 
    order_id UUID REFERENCES orders(id)
);
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd
