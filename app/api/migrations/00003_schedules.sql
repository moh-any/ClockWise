-- +goose Up 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS schedules (
    schedule_date DATE,
    day VARCHAR(10) NOT NULL CHECK (day = TRIM(TO_CHAR(schedule_date, 'Day'))),
    start_hour TIME NOT NULL,
    end_hour TIME NOT NULL,
    employee_id UUID REFERENCES users(id),
    PRIMARY KEY(schedule_date,start_hour,end_hour,employee_id) 
);
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS schedules; 
-- +goose StatementEnd
