USE delivery_db;

-- Insert orders data
INSERT INTO orders (customer_id, order_date, status, total_amount)
VALUES
    (1, '2026-09-01', 'Delivered', 12500.00),
    (2, '2026-09-02', 'Delivered', 350.00),
    (3, '2026-09-03', 'In Transit', 2200.00),
    (4, '2026-09-04', 'Processing', 4500.00),
    (5, '2026-09-05', 'Delivered', 750.00),
    (6, '2026-09-06', 'In Transit', 2800.00),
    (7, '2026-09-07', 'Processing', 650.00),
    (8, '2026-09-08', 'Delivered', 3500.00),
    (9, '2026-09-09', 'Delivered', 80.00),
    (10, '2026-09-10', 'In Transit', 250.00);
