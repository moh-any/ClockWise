-- +goose Up
-- +goose StatementBegin
-- Drop the old constraint that doesn't match the day_name format from ML service
ALTER TABLE demand DROP CONSTRAINT IF EXISTS demand_check;

-- Add new constraint that validates day matches the actual day of week (case-insensitive, trimmed)
ALTER TABLE demand ADD CONSTRAINT demand_check 
  CHECK (
    LOWER(TRIM(day)) = LOWER(TRIM(TO_CHAR(demand_date, 'Day')))
  );
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
ALTER TABLE demand DROP CONSTRAINT IF EXISTS demand_check;

-- Restore original constraint
ALTER TABLE demand ADD CONSTRAINT demand_check 
  CHECK (day = TRIM(TO_CHAR(demand_date, 'Day')));
-- +goose StatementEnd
