# Delivery & Logistics Data Engineering Project

## Project Overview

This project is a small data engineering and relational database
project for managing a delivery company's customers, products,
orders, drivers and deliveries.

## Technologies

- MYSQL
- SQL
- Python
- Pandas
- Git
- GitHub

## Project Goals

- Design a relational database
- Store delivery company data
- Write SQL queries for analysis
- Build a small ETL pipeline
- Clean and transform data using Python
- Generate useful business insights

## Database Design

The database contains seven main tables:

- customers
- products
- orders
- order_items
- drivers
- vehicles
- deliveries

### Relationships

- One customer can place many orders.
- One order can contain many products.
- One product can appear in many orders.
- The order_items table handles the many-to-many relationship between orders and products.
- One order has one delivery.
- One driver can complete many deliveries.
- One vehicle can be used for many deliveries.

## Database Implementation

The database was implemented using MySQL.

The database is called `delivery_db` and contains seven relational tables:

- `customers`
- `products`
- `orders`
- `order_items`
- `drivers`
- `vehicles`
- `deliveries`

Primary keys are used to uniquely identify records, while foreign keys are used to establish relationships between related tables.

The `order_items` table acts as a junction table between `orders` and `products`, allowing an order to contain multiple products and a product to appear in multiple orders.