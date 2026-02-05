-- +goose Up 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS users_shifts (
    user_id UUID REFERENCES users(id), 
    shift_manager UUID REFERENCES users(id),
    shift_start_time TIMESTAMP,
    shift_end_time TIMESTAMP,
    PRIMARY KEY (user_id, shift_start_time, shift_end_time)
);
-- +goose StatementEnd


-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS users_shifts;
-- +goose StatementEnd