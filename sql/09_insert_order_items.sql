USE delivery_db;

-- Insert order item data. Run after 04_insert_products.sql and 05_insert_orders.sql.
INSERT INTO order_items (order_id, product_id, quantity)
VALUES
    (1, 1, 1),
    (2, 2, 1),
    (3, 4, 1),
    (4, 6, 1),
    (5, 9, 1),
    (6, 7, 1),
    (7, 3, 1),
    (8, 5, 1),
    (9, 8, 1),
    (10, 10, 1);
