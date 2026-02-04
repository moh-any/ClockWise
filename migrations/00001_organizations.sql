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
    min_needed_per_shift INTEGER NOT NULL,
    items_per_role_per_hour INTEGER NOT NULL,
    need_for_demand BOOLEAN NOT NULL CHECK ((role = 'manager' AND need_for_demand = false) OR (role != 'manager')),
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
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
DROP TABLE organizations, organizations_roles, organizations_rules, organizations_operating_hours CASCADE;
DROP EXTENSION IF EXISTS "uuid-ossp";
-- +goose StatementEnd