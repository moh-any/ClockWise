
-- +goose Up
-- +goose StatementBegin
ALTER TABLE users ADD COLUMN on_call BOOLEAN DEFAULT false;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE users DROP COLUMN on_call;
-- +goose StatementEnd