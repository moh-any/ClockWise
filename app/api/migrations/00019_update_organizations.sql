-- +goose Up
-- +goose StatementBegin
ALTER TABLE organizations ADD COLUMN type VARCHAR(50) CHECK (type IN ('restaurant','cafe','bar','lounge','pub'));
ALTER TABLE organizations ADD COLUMN phone VARCHAR(20) UNIQUE NOT NULL;

ALTER TABLE organizations_rules ADD COLUMN receiving_phone BOOLEAN DEFAULT true;
ALTER TABLE organizations_rules ADD COLUMN delivery BOOLEAN DEFAULT true;
ALTER TABLE organizations_rules ADD COLUMN waiting_time INTEGER NOT NULL;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE organizations DROP COLUMN type;
ALTER TABLE organizations DROP COLUMN phone;

ALTER TABLE organizations_rules DROP COLUMN receiving_phone;
ALTER TABLE organizations_rules DROP COLUMN delivery;
ALTER TABLE organizations_rules DROP COLUMN waiting_time;
-- +goose StatementEnd