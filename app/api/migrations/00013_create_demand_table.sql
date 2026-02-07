-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS demand (
    organization_id UUID REFERENCES organizations(id),
    demand_date DATE,
    day VARCHAR(10) CHECK (day = TRIM(TO_CHAR(demand_date, 'Day'))),
    hour INTEGER CHECK(hour >= 0 AND hour <= 23),
    order_count INTEGER CHECK(order_count >= 0),
    item_count INTEGER CHECK(item_count >= 0),
    PRIMARY KEY (organization_id, demand_date, day, hour)
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS demand;
-- +goose StatementEnd
