USE delivery_db;

-- ============================================================
-- Analytics queries
-- Purpose: aggregate data (totals, averages, counts by group)
-- to answer business questions about sales and deliveries.
-- Run after 01-09 (all tables created and seeded).
-- ============================================================


-- ############################################################
-- PART 1: TOTALS
-- ############################################################

-- 1.1 Headline numbers: orders, revenue, and order-size range
-- No GROUP BY, so the whole table collapses into one row
SELECT
    COUNT(*)                     AS total_orders,
    SUM(total_amount)            AS total_revenue,
    ROUND(AVG(total_amount), 2)  AS avg_order_value,
    MIN(total_amount)            AS smallest_order,
    MAX(total_amount)            AS largest_order
FROM orders;


-- 1.2 Orders and revenue by order status
-- Shows how much money is delivered vs. still in the pipeline
SELECT
    status,
    COUNT(*)          AS order_count,
    SUM(total_amount) AS total_value
FROM orders
GROUP BY status
ORDER BY total_value DESC;


-- 1.3 Revenue by product category (from order line items)
-- line_total = quantity * price, so this stays correct even when
-- an order eventually contains several products.
SELECT
    p.category,
    SUM(oi.quantity)            AS units_sold,
    SUM(oi.quantity * p.price)  AS category_revenue
FROM order_items oi
INNER JOIN products p
    ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- 1.4 Revenue by product, best sellers first
SELECT
    p.product_id,
    p.product_name,
    p.category,
    SUM(oi.quantity)            AS units_sold,
    SUM(oi.quantity * p.price)  AS product_revenue
FROM order_items oi
INNER JOIN products p
    ON oi.product_id = p.product_id
GROUP BY p.product_id, p.product_name, p.category
ORDER BY product_revenue DESC;


-- 1.5 Total spend per customer (LEFT JOIN so customers with no orders show 0)
SELECT
    c.customer_id,
    c.name,
    c.city,
    COUNT(o.order_id)                 AS orders_placed,
    COALESCE(SUM(o.total_amount), 0)  AS total_spent
FROM customers c
LEFT JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.city
ORDER BY total_spent DESC;


-- 1.6 Daily revenue
SELECT
    order_date,
    COUNT(*)          AS orders,
    SUM(total_amount) AS daily_revenue
FROM orders
GROUP BY order_date
ORDER BY order_date;


-- ############################################################
-- PART 2: AVERAGES
-- ############################################################

-- 2.1 Average order value by customer city
SELECT
    c.city,
    COUNT(o.order_id)              AS orders,
    ROUND(AVG(o.total_amount), 2)  AS avg_order_value
FROM orders o
INNER JOIN customers c
    ON o.customer_id = c.customer_id
GROUP BY c.city
ORDER BY avg_order_value DESC;


-- 2.2 Average order value by order status
SELECT
    status,
    ROUND(AVG(total_amount), 2) AS avg_order_value
FROM orders
GROUP BY status
ORDER BY avg_order_value DESC;


-- 2.3 Price statistics by product category
SELECT
    category,
    COUNT(*)              AS products,
    ROUND(AVG(price), 2)  AS avg_price,
    MIN(price)            AS cheapest,
    MAX(price)            AS most_expensive
FROM products
GROUP BY category
ORDER BY avg_price DESC;


-- 2.4 Delivery time overall (days from order date to delivery date)
-- Filtered to 'Delivered' because only those have a final delivery_date.
SELECT
    COUNT(*)                                                AS delivered_orders,
    ROUND(AVG(DATEDIFF(d.delivery_date, o.order_date)), 2)  AS avg_days_to_deliver,
    MIN(DATEDIFF(d.delivery_date, o.order_date))            AS fastest_days,
    MAX(DATEDIFF(d.delivery_date, o.order_date))            AS slowest_days
FROM deliveries d
INNER JOIN orders o
    ON d.order_id = o.order_id
WHERE d.status = 'Delivered';


-- 2.5 Delivery time per driver
SELECT
    dr.driver_id,
    dr.name,
    COUNT(*)                                                AS delivered_count,
    ROUND(AVG(DATEDIFF(d.delivery_date, o.order_date)), 2)  AS avg_days_to_deliver
FROM deliveries d
INNER JOIN orders o   ON d.order_id = o.order_id
INNER JOIN drivers dr ON d.driver_id = dr.driver_id
WHERE d.status = 'Delivered'
GROUP BY dr.driver_id, dr.name
ORDER BY avg_days_to_deliver;


-- ############################################################
-- PART 3: COUNTS BY GROUP
-- ############################################################

-- 3.1 Customers per city
SELECT
    city,
    COUNT(*) AS customers
FROM customers
GROUP BY city
ORDER BY customers DESC, city;


-- 3.2 Deliveries per status
SELECT
    status,
    COUNT(*) AS deliveries
FROM deliveries
GROUP BY status
ORDER BY deliveries DESC;


-- 3.3 Deliveries per driver with a status breakdown (every driver shown)
-- In MySQL a comparison like (d.status = 'Delivered') returns 1 or 0,
-- so SUM() of it counts the matching rows.
SELECT
    dr.driver_id,
    dr.name,
    COUNT(d.delivery_id)          AS total_deliveries,
    SUM(d.status = 'Delivered')   AS delivered,
    SUM(d.status = 'In Transit')  AS in_transit,
    SUM(d.status = 'Processing')  AS processing
FROM drivers dr
LEFT JOIN deliveries d
    ON dr.driver_id = d.driver_id
GROUP BY dr.driver_id, dr.name
ORDER BY total_deliveries DESC, dr.name;


-- 3.4 Deliveries per vehicle type
SELECT
    v.vehicle_type,
    COUNT(d.delivery_id) AS total_deliveries
FROM vehicles v
LEFT JOIN deliveries d
    ON v.vehicle_id = d.vehicle_id
GROUP BY v.vehicle_type
ORDER BY total_deliveries DESC;


-- 3.5 Deliveries per individual vehicle
SELECT
    v.registration_number,
    v.vehicle_type,
    COUNT(d.delivery_id) AS total_deliveries
FROM vehicles v
LEFT JOIN deliveries d
    ON v.vehicle_id = d.vehicle_id
GROUP BY v.vehicle_id, v.registration_number, v.vehicle_type
ORDER BY total_deliveries DESC;


-- 3.6 Products per category
SELECT
    category,
    COUNT(*) AS products
FROM products
GROUP BY category
ORDER BY products DESC;


-- ############################################################
-- PART 4: COMBINED BUSINESS INSIGHTS
-- ############################################################

-- 4.1 Delivery success rate
SELECT
    COUNT(*)                                              AS total_deliveries,
    SUM(status = 'Delivered')                             AS delivered,
    ROUND(100 * SUM(status = 'Delivered') / COUNT(*), 1)  AS delivered_pct
FROM deliveries;


-- 4.2 Revenue by city and product category
SELECT
    c.city,
    p.category,
    SUM(oi.quantity * p.price) AS revenue
FROM orders o
INNER JOIN customers c    ON o.customer_id = c.customer_id
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p     ON oi.product_id = p.product_id
GROUP BY c.city, p.category
ORDER BY c.city, revenue DESC;


-- 4.3 Value of orders handled per driver
SELECT
    dr.name              AS driver_name,
    COUNT(d.delivery_id) AS deliveries,
    SUM(o.total_amount)  AS order_value_handled
FROM drivers dr
INNER JOIN deliveries d ON dr.driver_id = d.driver_id
INNER JOIN orders o     ON d.order_id = o.order_id
GROUP BY dr.driver_id, dr.name
ORDER BY order_value_handled DESC;


-- 4.4 Share of total revenue by category (percentage)
SELECT
    p.category,
    SUM(oi.quantity * p.price) AS category_revenue,
    ROUND(
        100 * SUM(oi.quantity * p.price) / (
            SELECT SUM(oi2.quantity * p2.price)
            FROM order_items oi2
            INNER JOIN products p2 ON oi2.product_id = p2.product_id
        ),
        1
    ) AS pct_of_revenue
FROM order_items oi
INNER JOIN products p
    ON oi.product_id = p.product_id
GROUP BY p.category
ORDER BY category_revenue DESC;


-- 4.5 Customers who spent more than the average customer
-- HAVING filters on the aggregate; the subquery computes the benchmark.
SELECT
    c.name,
    c.city,
    SUM(o.total_amount) AS total_spent
FROM customers c
INNER JOIN orders o
    ON c.customer_id = o.customer_id
GROUP BY c.customer_id, c.name, c.city
HAVING SUM(o.total_amount) > (
    SELECT AVG(customer_total)
    FROM (
        SELECT SUM(total_amount) AS customer_total
        FROM orders
        GROUP BY customer_id
    ) AS per_customer
)
ORDER BY total_spent DESC;


-- 4.6 Data-quality check: does orders.total_amount match its line items?
-- Any row returned is an order whose stored total disagrees with the items.
-- (Zero rows = data is consistent.)
SELECT
    o.order_id,
    o.total_amount              AS stored_total,
    SUM(oi.quantity * p.price)  AS calculated_total
FROM orders o
INNER JOIN order_items oi ON o.order_id = oi.order_id
INNER JOIN products p     ON oi.product_id = p.product_id
GROUP BY o.order_id, o.total_amount
HAVING o.total_amount <> SUM(oi.quantity * p.price);