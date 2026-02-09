-- +goose Up 
-- +goose StatementBegin
ALTER TABLE schedules DROP COLUMN day;
ALTER TABLE schedules ADD COLUMN day VARCHAR(10) NOT NULL;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
-- +goose StatementEnd
