-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS preferences (
    employee_id UUID PRIMARY KEY REFERENCES users(id),
    organization_id UUID NOT NULL REFERENCES organizations(id), 
    preferred_start_time TIME NOT NULL,
    preferred_end_time TIME NOT NULL,
    available_start_time TIME NOT NULL,
    available_end_time TIME NOT NULL,
    preferred_days_per_week INT NOT NULL CHECK (preferred_days_per_week >= 1 AND preferred_days_per_week <= 7),
    available_days_per_week INT NOT NULL CHECK (available_days_per_week >= 1 AND available_days_per_week <= 7),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS preferences;
-- +goose StatementEnd
