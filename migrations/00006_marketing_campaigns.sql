-- +goose Up 
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS marketing_campaigns (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    status VARCHAR(10) CHECK (status IN ('active','inactive')),
    start_date DATE NOT NULL,
    end_date DATE NOT NULL, 
    social_media_platform VARCHAR(20),
    type TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS campaigns_items (
    campaign_id UUID REFERENCES marketing_campaigns(id),
    item_id UUID REFERENCES items(id),
    discount_amount DECIMAL(10,2) NOT NULL,
    PRIMARY KEY(campaign_id, item_id)
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS marketing_campaigns, campaigns_items CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd