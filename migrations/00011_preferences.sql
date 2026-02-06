-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS employees_preferences (
    employee_id UUID REFERENCES users(id),
    day VARCHAR(10) NOT NULL CHECK (day IN ('Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday')),
    preferred_start_time TIME,
    preferred_end_time TIME,
    available_start_time TIME,
    available_end_time TIME,
    PRIMARY KEY (employee_id,day)
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS employees_preferences;
-- +goose StatementEnd
