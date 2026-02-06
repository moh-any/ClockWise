
-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS users(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL, 
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    user_role VARCHAR(50), -- Main Role
    salary_per_hour DECIMAL(10,2) CHECK((user_role = 'admin' AND salary_per_hour IS NULL) OR (user_role != 'admin' AND salary_per_hour IS NOT NULL)), 
    max_hours_per_week INTEGER,
    preferred_hours_per_week INTEGER,
    max_consec_slots INTEGER,
    on_call BOOLEAN DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (organization_id, user_role) REFERENCES organizations_roles(organization_id,role)
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id),
    organization_id UUID,
    user_role VARCHAR(50),
    FOREIGN KEY (organization_id,user_role) REFERENCES organizations_roles(organization_id,role),
    PRIMARY KEY (user_id,organization_id,user_role)
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE users;
DROP TABLE user_roles;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd