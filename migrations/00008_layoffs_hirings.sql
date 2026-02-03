-- +goose Up 
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS layoffs_hirings (

);
-- +goose StatementEnd


-- +goose Down 
-- +goose StatementBegin
DROP TABLE IF EXISTS layoffs_hirings; 
-- +goose StatementEnd
