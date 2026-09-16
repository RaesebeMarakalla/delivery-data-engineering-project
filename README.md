# Delivery & Logistics Data Engineering Project

## Overview

This project models the core data required by a delivery company: customers, products, orders, order items, drivers, vehicles, and deliveries. It is being built as a practical data-engineering project using MySQL, SQL, Python, and Pandas.

## Work completed today

- Created the MySQL database setup script.
- Created seven related tables with primary keys, foreign keys, and appropriate constraints.
- Added an initial data-seeding script for the `customers` table.
- Inserted 10 sample customers from Gauteng-area locations to support testing and future analysis.
- Added 10 sample products, 10 customer orders, 10 order items, 5 drivers, 5 vehicles, and 10 delivery assignments.
- Documented the database design and the relationships between the tables.

- Documented the database design and the relationships between the tables.
- Wrote JOIN queries combining customers, orders, order_items, products, drivers, and vehicles into meaningful views.
- Used LEFT JOIN queries to find customers with no orders, products never ordered, and delivery counts per driver.

## Sample data

The seeded customer, product, order, driver, vehicle, and delivery data can be viewed in the project screenshots.

### Customers

![Customer data](screenshots/customer-data.png)

### Orders

![Order data](screenshots/order-data.png)

### Order Items

![Order item data](screenshots/order-items-data.png)

### Drivers

![Driver data](screenshots/drivers-data.png)

### Vehicles

![Vehicle data](screenshots/vehicles-data.png)

### Deliveries

![Delivery data](screenshots/deliveries-data.png)

## Technologies

- MySQL
- SQL
- Python
- Pandas
- Git and GitHub

## Database schema

The `delivery_db` database contains the following tables:

- `customers`: customer contact and location details
- `products`: products available to purchase
- `orders`: orders placed by customers
- `order_items`: junction table connecting orders and products
- `drivers`: delivery-driver details
- `vehicles`: delivery-vehicle details
- `deliveries`: delivery assignment and status information

Key relationships:

- A customer can place many orders.
- An order can contain many products through `order_items`.
- A driver and a vehicle can each be assigned to many deliveries.
- Each delivery is linked to an order, driver, and vehicle.

For a fuller description, see [the database design documentation](sql/database_design.md).

## Project structure

```text
.
|-- data/                 # Source and processed data files
|-- python/               # ETL and analysis scripts
|-- screenshots/          # Project screenshots
`-- sql/
    |-- 01_create_database.sql
    |-- 02_create_tables.sql
    |-- 03_insert_data.sql
    |-- 04_insert_products.sql
    |-- 05_insert_orders.sql
    |-- 06_insert_drivers.sql
    |-- 07_insert_vehicles.sql
    |-- 08_insert_deliveries.sql
    |-- 09_insert_order_items.sql
    |-- 10_join_queries.sql
    `-- database_design.md
```

## Running the database scripts

Run the SQL files in this order in MySQL:

1. `sql/01_create_database.sql`: creates `delivery_db`.
2. `sql/02_create_tables.sql`: creates the seven tables and their relationships.
3. `sql/03_insert_data.sql`: loads the initial customer sample data.
4. `sql/04_insert_products.sql`: loads the product sample data.
5. `sql/05_insert_orders.sql`: loads the order sample data.
6. `sql/06_insert_drivers.sql`: loads the driver sample data.
7. `sql/07_insert_vehicles.sql`: loads the vehicle sample data.
8. `sql/08_insert_deliveries.sql`: loads the delivery sample data.
9. `sql/09_insert_order_items.sql`: loads the order-item sample data.
9. `sql/09_insert_order_items.sql`: loads the order-item sample data.
10. `sql/10_join_queries.sql`: runs JOIN queries across the tables (customer orders, delivery details, and gaps like customers with no orders).

For example, from a MySQL client:

```sql
SOURCE sql/01_create_database.sql;
SOURCE sql/02_create_tables.sql;
SOURCE sql/03_insert_data.sql;
SOURCE sql/04_insert_products.sql;
SOURCE sql/05_insert_orders.sql;
SOURCE sql/06_insert_drivers.sql;
SOURCE sql/07_insert_vehicles.sql;
SOURCE sql/08_insert_deliveries.sql;
SOURCE sql/09_insert_order_items.sql;
SOURCE sql/10_join_queries.sql;
```

## Next steps

- Write analytics queries (totals, averages, counts by group).
- Build a Python/Pandas ETL pipeline to clean and transform source data.
- Load cleaned data into the database via the ETL pipeline.
- Produce business insights and visualisations from the completed dataset.
