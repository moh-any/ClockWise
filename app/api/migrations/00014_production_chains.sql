-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS production_chain (
    organization_id UUID, 
    chain_name VARCHAR(20),
    role VARCHAR(50),
    contrib_factor DECIMAL(10,2) DEFAULT 1.0,
    PRIMARY KEY(organization_id,chain_name,role),
    FOREIGN KEY (organization_id,role) REFERENCES organizations_roles(organization_id,role)
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE IF EXISTS production_chain;
-- +goose StatementEnd
