-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS organizations(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    address TEXT,
    email VARCHAR(100) UNIQUE NOT NULL,
    hex_code1 VARCHAR(6) NOT NULL,
    hex_code2 VARCHAR(6) NOT NULL,
    hex_code3 VARCHAR(6) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organizations_roles (
    organization_id UUID,
    role VARCHAR(50),
    min_needed_per_shift INTEGER CHECK ((need_for_demand = true AND min_needed_per_shift>=0 ) OR (role = 'manager' AND min_needed_per_shift = 1) OR (role = 'admin' AND min_needed_per_shift = 0)),
    items_per_role_per_hour INTEGER CHECK ((need_for_demand = true AND items_per_role_per_hour>=0) OR need_for_demand = false AND items_per_role_per_hour IS NULL),
    need_for_demand BOOLEAN NOT NULL CHECK ((role = 'manager' OR role = 'admin' AND need_for_demand = false) OR (role != 'manager' AND role != 'admin')),
    PRIMARY KEY (organization_id,role),
    FOREIGN KEY (organization_id) REFERENCES organizations(id)
);

CREATE TABLE IF NOT EXISTS organizations_rules (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    shift_max_hours INTEGER NOT NULL, 
    shift_min_hours INTEGER NOT NULL, 
    max_weekly_hours INTEGER NOT NULL, 
    min_weekly_hours INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations_operating_hours (
    organization_id UUID REFERENCES organizations(id),
    weekday CHAR CHECK (weekday IN ('sunday','monday','tuesday','wednesday','thursday','friday','saturday')),
    opening_time TIMESTAMP NOT NULL,
    closing_time TIMESTAMP NOT NULL,
    PRIMARY KEY (organization_id, weekday) 
);

CREATE OR REPLACE FUNCTION insert_default_organization_roles()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand)
    VALUES (NEW.id, 'admin', 0, NULL, false);
    
    INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand)
    VALUES (NEW.id, 'manager', 1, NULL, false);
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_insert_default_roles
AFTER INSERT ON organizations
FOR EACH ROW
EXECUTE FUNCTION insert_default_organization_roles();
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TRIGGER IF EXISTS trigger_insert_default_roles ON organizations;
DROP FUNCTION IF EXISTS insert_default_organization_roles();
DROP TABLE organizations, organizations_roles, organizations_rules, organizations_operating_hours CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd