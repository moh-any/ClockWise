-- +goose Up
-- +goose StatementBegin
DROP TABLE IF EXISTS alerts CASCADE;
-- +goose StatementEnd

-- +goose Down 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    organization_id UUID REFERENCES organizations(id), 
    severity VARCHAR(10) CHECK (severity IN ('moderate','high','critical')),
    subject TEXT NOT NULL, 
    message TEXT NOT NULL
);
-- +goose StatementEnd