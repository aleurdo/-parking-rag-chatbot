-- ParkEase Parking Booking Database Schema

CREATE TABLE IF NOT EXISTS locations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    address VARCHAR(255) NOT NULL,
    total_capacity INTEGER NOT NULL,
    location_type VARCHAR(50) NOT NULL DEFAULT 'garage',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS parking_zones (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    zone_name VARCHAR(50) NOT NULL,
    zone_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    capacity INTEGER NOT NULL,
    hourly_rate DECIMAL(6,2),
    daily_max DECIMAL(6,2)
);

CREATE TABLE IF NOT EXISTS operating_hours (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    day_of_week INTEGER NOT NULL CHECK (day_of_week BETWEEN 0 AND 6),
    open_time TIME NOT NULL,
    close_time TIME NOT NULL,
    is_24h BOOLEAN DEFAULT FALSE
);

CREATE TABLE IF NOT EXISTS reservations (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    zone_id INTEGER REFERENCES parking_zones(id),
    customer_name VARCHAR(100) NOT NULL,
    customer_email VARCHAR(255) NOT NULL,
    license_plate VARCHAR(20) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP,
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS availability (
    id SERIAL PRIMARY KEY,
    location_id INTEGER REFERENCES locations(id),
    zone_id INTEGER REFERENCES parking_zones(id),
    date DATE NOT NULL,
    available_spaces INTEGER NOT NULL,
    UNIQUE(zone_id, date)
);

CREATE TABLE IF NOT EXISTS admin_requests (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending',
    customer_name VARCHAR(100) NOT NULL,
    car_number VARCHAR(20) NOT NULL,
    location VARCHAR(100) NOT NULL,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL DEFAULT 'standard',
    admin_note TEXT,
    recorded BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    decided_at TIMESTAMP
);

CREATE INDEX idx_reservations_location ON reservations(location_id);
CREATE INDEX idx_reservations_start ON reservations(start_time);
CREATE INDEX idx_reservations_status ON reservations(status);
CREATE INDEX idx_availability_date ON availability(date);
CREATE INDEX idx_admin_requests_status ON admin_requests(status);
CREATE INDEX idx_admin_requests_session ON admin_requests(session_id);
