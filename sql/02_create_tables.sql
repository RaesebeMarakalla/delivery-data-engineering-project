USE delivery_db;

CREATE TABLE customers (
    customer_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) NOT NULL UNIQUE,
    phone VARCHAR(20),
    city VARCHAR(100),

    CONSTRAINT chk_customers_name CHECK (TRIM(name) <> ''),
    CONSTRAINT chk_customers_email CHECK (email LIKE '%@%'),
    CONSTRAINT chk_customers_phone CHECK (phone IS NULL OR TRIM(phone) <> ''),
    CONSTRAINT chk_customers_city CHECK (city IS NULL OR TRIM(city) <> '')
);

CREATE TABLE products (
    product_id INT AUTO_INCREMENT PRIMARY KEY,
    product_name VARCHAR(100) NOT NULL,
    category VARCHAR(100),
    price DECIMAL(10, 2) NOT NULL,

    CONSTRAINT chk_products_name CHECK (TRIM(product_name) <> ''),
    CONSTRAINT chk_products_category CHECK (category IS NULL OR TRIM(category) <> ''),
    CONSTRAINT chk_products_price CHECK (price >= 0)
);

CREATE TABLE orders (
    order_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT NOT NULL,
    order_date DATE NOT NULL,
    status VARCHAR(50) NOT NULL,
    total_amount DECIMAL(10, 2) NOT NULL,

    CONSTRAINT chk_orders_status CHECK (status IN ('Pending', 'Processing', 'In Transit', 'Delivered', 'Cancelled', 'Shipped')),
    CONSTRAINT chk_orders_total_amount CHECK (total_amount >= 0),
    CONSTRAINT chk_orders_customer_id CHECK (customer_id > 0),

    FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id)
);

CREATE TABLE order_items (
    order_item_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    product_id INT NOT NULL,
    quantity INT NOT NULL,

    CONSTRAINT chk_order_items_quantity CHECK (quantity > 0),
    CONSTRAINT chk_order_items_order_id CHECK (order_id > 0),
    CONSTRAINT chk_order_items_product_id CHECK (product_id > 0),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (product_id)
        REFERENCES products(product_id),

    UNIQUE (order_id, product_id)
);

CREATE TABLE drivers (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    phone VARCHAR(20) NOT NULL,

    CONSTRAINT chk_drivers_name CHECK (TRIM(name) <> ''),
    CONSTRAINT chk_drivers_phone CHECK (TRIM(phone) <> '')
);

CREATE TABLE vehicles (
    vehicle_id INT AUTO_INCREMENT PRIMARY KEY,
    registration_number VARCHAR(20) NOT NULL UNIQUE,
    vehicle_type VARCHAR(50) NOT NULL,

    CONSTRAINT chk_vehicles_registration_number CHECK (TRIM(registration_number) <> ''),
    CONSTRAINT chk_vehicles_vehicle_type CHECK (TRIM(vehicle_type) <> '')
);

CREATE TABLE deliveries (
    delivery_id INT AUTO_INCREMENT PRIMARY KEY,
    order_id INT NOT NULL,
    driver_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    delivery_date DATE,
    status VARCHAR(50) NOT NULL,

    CONSTRAINT chk_deliveries_order_id CHECK (order_id > 0),
    CONSTRAINT chk_deliveries_driver_id CHECK (driver_id > 0),
    CONSTRAINT chk_deliveries_vehicle_id CHECK (vehicle_id > 0),
    CONSTRAINT chk_deliveries_status CHECK (status IN ('Pending', 'Processing', 'In Transit', 'Delivered', 'Cancelled', 'Shipped')),

    FOREIGN KEY (order_id)
        REFERENCES orders(order_id),

    FOREIGN KEY (driver_id)
        REFERENCES drivers(driver_id),

    FOREIGN KEY (vehicle_id)
        REFERENCES vehicles(vehicle_id)
);