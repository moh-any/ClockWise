
-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS tables (
    organization_id UUID REFERENCES organizations(id),
    table_no INTEGER,
    number_of_people INTEGER NOT NULL,
    PRIMARY KEY (organization_id, table_no)
);

CREATE TABLE IF NOT EXISTS order_tables (
    order_id UUID REFERENCES orders(id),
    organization_id UUID, 
    table_no INTEGER, 
    number_of_people INTEGER NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL, 
    PRIMARY KEY (order_id,organization_id,table_no),
    FOREIGN KEY (organization_id,table_no) REFERENCES tables(organization_id,table_no)
);
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS tables, order_tables CASCADE; 
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd
