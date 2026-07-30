-- Seed data for ParkEase

-- Locations
INSERT INTO locations (id, name, address, total_capacity, location_type) VALUES
(1, 'Downtown Garage', '123 Main Street, City Center, 10001', 500, 'garage'),
(2, 'Riverside Lot', '45 River Road, Waterfront District, 10005', 200, 'open_lot'),
(3, 'Airport Express Park', '789 Terminal Way, Airport Zone, 10099', 800, 'covered_structure');

-- Parking Zones
INSERT INTO parking_zones (id, location_id, zone_name, zone_type, capacity, hourly_rate, daily_max) VALUES
-- Downtown Garage
(1, 1, 'Standard Parking', 'standard', 460, 2.00, 18.00),
(2, 1, 'EV Charging', 'ev', 20, 3.00, 25.00),
(3, 1, 'Disabled', 'disabled', 15, 2.00, 18.00),
(4, 1, 'Valet', 'valet', 5, 5.00, 28.00),
-- Riverside Lot
(5, 2, 'Standard Parking', 'standard', 170, 1.50, 12.00),
(6, 2, 'Motorcycle', 'motorcycle', 20, 0.75, 6.00),
(7, 2, 'Disabled', 'disabled', 8, 1.50, 12.00),
(8, 2, 'Oversized Vehicle', 'oversized', 2, 3.00, 20.00),
-- Airport Express Park
(9, 3, 'Standard Parking', 'standard', 600, 0.00, 15.00),
(10, 3, 'Premium', 'premium', 150, 0.00, 22.00),
(11, 3, 'Disabled', 'disabled', 25, 0.00, 15.00),
(12, 3, 'Oversized Vehicle', 'oversized', 25, 0.00, 20.00);

-- Operating Hours (all locations 24/7)
INSERT INTO operating_hours (location_id, day_of_week, open_time, close_time, is_24h)
SELECT l.id, d.day, '00:00', '23:59', TRUE
FROM locations l
CROSS JOIN generate_series(0, 6) AS d(day);

-- Availability (next 30 days, seeded with full capacity)
INSERT INTO availability (location_id, zone_id, date, available_spaces)
SELECT pz.location_id, pz.id, d::date, pz.capacity
FROM parking_zones pz
CROSS JOIN generate_series(CURRENT_DATE, CURRENT_DATE + INTERVAL '30 days', '1 day') AS d
ON CONFLICT (zone_id, date) DO NOTHING;

-- Sample reservations
INSERT INTO reservations (location_id, zone_id, customer_name, customer_email, license_plate, vehicle_type, start_time, end_time, status) VALUES
(1, 1, 'John Smith', 'john@example.com', 'ABC-1234', 'standard', CURRENT_TIMESTAMP + INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '1 day 8 hours', 'confirmed'),
(1, 2, 'Jane Doe', 'jane@example.com', 'EV-5678', 'ev', CURRENT_TIMESTAMP + INTERVAL '2 days', CURRENT_TIMESTAMP + INTERVAL '2 days 4 hours', 'confirmed'),
(2, 5, 'Bob Wilson', 'bob@example.com', 'XYZ-9999', 'standard', CURRENT_TIMESTAMP + INTERVAL '1 day', CURRENT_TIMESTAMP + INTERVAL '1 day 6 hours', 'confirmed'),
(3, 9, 'Alice Brown', 'alice@example.com', 'TRV-4321', 'standard', CURRENT_TIMESTAMP + INTERVAL '3 days', CURRENT_TIMESTAMP + INTERVAL '10 days', 'confirmed');
