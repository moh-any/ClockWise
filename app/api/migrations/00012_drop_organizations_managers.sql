-- +goose Up
-- +goose StatementBegin
DROP TABLE IF EXISTS organizations_managers CASCADE;
-- +goose StatementEnd
