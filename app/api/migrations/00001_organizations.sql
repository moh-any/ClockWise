-- +goose Up
-- +goose StatementBegin
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE TABLE IF NOT EXISTS organizations(
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) UNIQUE NOT NULL,
    address TEXT,
    latitude DECIMAL(10,7) CHECK ((latitude IS NOT NULL AND longitude IS NOT NULL) OR (latitude IS NULL AND longitude IS NULL)),
    longitude DECIMAL(10,7) CHECK ((latitude IS NOT NULL AND longitude IS NOT NULL) OR (latitude IS NULL AND longitude IS NULL)),
    email VARCHAR(100) UNIQUE NOT NULL,
    hex_code1 VARCHAR(6) NOT NULL,
    hex_code2 VARCHAR(6) NOT NULL,
    hex_code3 VARCHAR(6) NOT NULL,
    rating DECIMAL(10,2), 
    accepting_orders BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS organizations_roles (
    organization_id UUID,
    role VARCHAR(50),
    min_needed_per_shift INTEGER 3,
    items_per_role_per_hour INTEGER DEFAULT 10,
    need_for_demand BOOLEAN NOT NULL DEFAULT true,
    independent BOOLEAN DEFAULT false,
    PRIMARY KEY (organization_id, role),
    FOREIGN KEY (organization_id) REFERENCES organizations(id),
    CHECK ((role != 'manager' AND role != 'admin' AND min_needed_per_shift >= 0) OR 
           (role = 'manager' AND min_needed_per_shift = 1) OR 
           (role = 'admin' AND min_needed_per_shift = 0)),
    CHECK ((need_for_demand = true AND items_per_role_per_hour >= 0) OR 
           (need_for_demand = false AND items_per_role_per_hour IS NULL)),
    CHECK (((role = 'manager' OR role = 'admin') AND need_for_demand = false) OR 
           (role != 'manager' AND role != 'admin')),
    CHECK ((role = 'manager' AND independent = true) OR 
           (role = 'admin' AND independent = true) OR 
           ((role != 'manager' AND role != 'admin') AND independent IS NOT NULL))
);

CREATE TABLE IF NOT EXISTS organizations_rules (
    organization_id UUID PRIMARY KEY REFERENCES organizations(id),
    shift_max_hours INTEGER NOT NULL, 
    shift_min_hours INTEGER NOT NULL, 
    max_weekly_hours INTEGER NOT NULL, 
    min_weekly_hours INTEGER NOT NULL, 
    fixed_shifts BOOLEAN NOT NULL,
    number_of_shifts_per_day INTEGER CHECK ((fixed_shifts = true AND number_of_shifts_per_day IS NOT NULL) OR (fixed_shifts = false AND number_of_shifts_per_day IS NULL)),
    meet_all_demand BOOLEAN NOT NULL DEFAULT false,
    min_rest_slots INTEGER NOT NULL,
    slot_len_hour  DECIMAL(10,2) NOT NULL,
    min_shift_length_slots INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS organizations_operating_hours (
    organization_id UUID REFERENCES organizations(id),
    weekday VARCHAR(10) CHECK (weekday IN ('sunday','monday','tuesday','wednesday','thursday','friday','saturday')),
    opening_time TIME NOT NULL,
    closing_time TIME NOT NULL,
    PRIMARY KEY (organization_id, weekday) 
);

CREATE OR REPLACE FUNCTION insert_default_organization_roles()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent)
    VALUES (NEW.id, 'admin', 0, NULL, false, true);
    
    INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent)
    VALUES (NEW.id, 'manager', 1, NULL, false, true);
    
    INSERT INTO organizations_roles (organization_id, role, min_needed_per_shift, items_per_role_per_hour, need_for_demand, independent)
    VALUES (NEW.id, 'employee', 1, 0, true, false);

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