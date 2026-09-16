USE delivery_db;

-- ============================================================
-- JOIN queries
-- Purpose: combine data across tables to answer real questions
-- ============================================================


-- 1. Order summary: which customer placed each order, and when
-- INNER JOIN because every order must have a customer
SELECT
    o.order_id,
    c.name         AS customer_name,
    c.city,
    o.order_date,
    o.status,
    o.total_amount
FROM orders o
INNER JOIN customers c
    ON o.customer_id = c.customer_id
ORDER BY o.order_date;


-- 2. Full order breakdown: which products, and how many, per order
-- Three-table INNER JOIN: orders -> order_items -> products
SELECT
    o.order_id,
    c.name          AS customer_name,
    p.product_name,
    p.category,
    oi.quantity,
    p.price,
    (oi.quantity * p.price) AS line_total
FROM orders o
INNER JOIN customers c   ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p     ON oi.product_id = p.product_id
ORDER BY o.order_id;


-- 3. Delivery details: order, driver, and vehicle in one view
-- INNER JOIN across deliveries -> orders -> drivers -> vehicles
SELECT
    d.delivery_id,
    o.order_id,
    c.name          AS customer_name,
    dr.name         AS driver_name,
    v.registration_number,
    v.vehicle_type,
    d.delivery_date,
    d.status        AS delivery_status
FROM deliveries d
INNER JOIN orders o    ON d.order_id = o.order_id
INNER JOIN customers c ON o.customer_id = c.customer_id
INNER JOIN drivers dr  ON d.driver_id = dr.driver_id
INNER JOIN vehicles v  ON d.vehicle_id = v.vehicle_id
ORDER BY d.delivery_date;


-- 4. Customers who have NOT placed any orders yet
-- LEFT JOIN + WHERE ... IS NULL is the standard pattern for "find the gap"
SELECT
    c.customer_id,
    c.name,
    c.email
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
WHERE o.order_id IS NULL;


-- 5. Products that have never appeared in an order
-- Same LEFT JOIN pattern, applied to products/order_items instead
SELECT
    p.product_id,
    p.product_name,
    p.category
FROM products p
LEFT JOIN order_items oi
    ON p.product_id = oi.product_id
WHERE oi.order_item_id IS NULL;


-- 6. Delivery count per driver, including drivers with zero deliveries
-- LEFT JOIN + GROUP BY: every driver appears, even ones never assigned
SELECT
    dr.driver_id,
    dr.name,
    COUNT(d.delivery_id) AS total_deliveries
FROM drivers dr
LEFT JOIN deliveries d
    ON dr.driver_id = d.driver_id
GROUP BY dr.driver_id, dr.name
ORDER BY total_deliveries DESC;