-- +goose Up
-- +goose StatementBegin
DROP TABLE IF EXISTS organizations_managers CASCADE;
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS organizations_managers (
    organization_id UUID,
    manager_id UUID, 
    PRIMARY KEY (organization_id,manager_id), 
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (manager_id) REFERENCES users(id)   
);
-- +goose StatementEnd
