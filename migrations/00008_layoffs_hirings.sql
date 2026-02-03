-- +goose Up 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS layoffs_hirings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4()
);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS layoffs_hirings; 
-- +goose StatementEnd
