USE delivery_db;

-- Insert deliveries data. Run after 05_insert_orders.sql, 06_insert_drivers.sql, and 07_insert_vehicles.sql.
INSERT INTO deliveries (order_id, driver_id, vehicle_id, delivery_date, status)
VALUES
    (1, 1, 1, '2026-09-02', 'Delivered'),
    (2, 2, 3, '2026-09-03', 'Delivered'),
    (3, 3, 2, '2026-09-04', 'In Transit'),
    (4, 4, 4, NULL, 'Processing'),
    (5, 5, 5, '2026-09-06', 'Delivered'),
    (6, 1, 1, '2026-09-07', 'In Transit'),
    (7, 2, 3, NULL, 'Processing'),
    (8, 3, 2, '2026-09-09', 'Delivered'),
    (9, 4, 4, '2026-09-10', 'Delivered'),
    (10, 5, 5, '2026-09-11', 'In Transit');
