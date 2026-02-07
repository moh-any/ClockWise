-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY,
    organization_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL, 
    status VARCHAR(10) CHECK (status IN ('active','inactive')),
    start_time_date TIMESTAMP NOT NULL,
    end_time_date TIMESTAMP NOT NULL, 
    discount_percent DECIMAL(10,2)
);

CREATE TABLE IF NOT EXISTS campaigns_items (
    campaign_id UUID REFERENCES marketing_campaigns(id),
    item_id UUID REFERENCES items(id),
    PRIMARY KEY(campaign_id, item_id)
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS marketing_campaigns, campaigns_items CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd