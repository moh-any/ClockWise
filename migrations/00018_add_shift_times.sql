-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS organization_shift_times(
    organization_id UUID REFERENCES organizations(id),
    start_time TIME,
    end_time TIME, 
    PRIMARY KEY (organization_id,start_time,end_time)
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS organization_shift_times;
-- +goose StatementEnd