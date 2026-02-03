-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS organizations(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    address TEXT,
    email VARCHAR(100) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organizations_roles (
    organization_id UUID,
    role VARCHAR(50),
    PRIMARY KEY (organization_id,role),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)  
);

CREATE TABLE IF NOT EXISTS organizations_managers (
    organization_id UUID,
    manager_id UUID, 
    PRIMARY KEY (organization_id,manager_id), 
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    FOREIGN KEY (manager_id) REFERENCES users(id)   
)

-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE organizations, organizations_roles CASCADE, organizations_managers CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd