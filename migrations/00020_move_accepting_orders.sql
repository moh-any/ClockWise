-- +goose Up
-- +goose StatementBegin
ALTER TABLE organizations_rules ADD COLUMN accepting_orders BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE organizations DROP COLUMN accepting_orders;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE organizations ADD COLUMN accepting_orders BOOLEAN NOT NULL DEFAULT true;
ALTER TABLE organizations_rules DROP COLUMN accepting_orders;
-- +goose StatementEnd
