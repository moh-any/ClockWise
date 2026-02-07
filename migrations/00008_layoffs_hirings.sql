-- +goose Up 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS layoffs_hirings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL,
    user_name VARCHAR(255),
    user_email VARCHAR(255),
    organization_id UUID REFERENCES organizations(id),
    action VARCHAR(20) NOT NULL CHECK (action IN ('layoff', 'hiring')),
    reason TEXT,
    action_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS layoffs_hirings; 
-- +goose StatementEnd
