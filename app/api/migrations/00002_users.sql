-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS users(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    full_name VARCHAR(255) NOT NULL, 
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    organization_id UUID REFERENCES organizations(id),
    user_role VARCHAR(50) CHECK (user_role IN ('admin','manager','employee')),
    salary_per_hour DECIMAL(10,2) CHECK((user_role = 'admin' AND salary_per_hour IS NULL) OR (user_role != 'admin' AND salary_per_hour IS NOT NULL)), 
    max_hours_per_week INTEGER NOT NULL DEFAULT 45,
    preferred_hours_per_week INTEGER NOT NULL DEFAULT 40,
    max_consec_slots INTEGER NOT NULL DEFAULT 8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_roles (
    user_id UUID REFERENCES users(id),
    organization_id UUID,
    user_role VARCHAR(50),
    FOREIGN KEY (organization_id,user_role) REFERENCES organizations_roles(organization_id,role),
    PRIMARY KEY (user_id,organization_id,user_role)
);

CREATE OR REPLACE FUNCTION insert_manager_roles()
RETURNS TRIGGER AS $$
BEGIN    
    INSERT INTO user_roles (user_id,organization_id,user_role)
    VALUES (NEW.id,NEW.organization_id, 'manager');
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_insert_manager_role
AFTER INSERT ON users
FOR EACH ROW
WHEN (NEW.user_role = 'manager')
EXECUTE FUNCTION insert_manager_roles();
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE users;
DROP TABLE user_roles;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd