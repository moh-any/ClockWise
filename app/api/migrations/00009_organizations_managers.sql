-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS organizations_managers (
    organization_id UUID,
    manager_id UUID, 
    PRIMARY KEY (organization_id,manager_id), 
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (manager_id) REFERENCES users(id) ON DELETE CASCADE  
);

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE organizations_managers CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd