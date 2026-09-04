# Database Design

## Project Overview

The Delivery & Logistics Data Engineering Project uses a relational database to manage customers, products, orders, drivers, vehicles, and deliveries.

The database is designed to keep related information in separate tables and connect the tables using primary keys and foreign keys.

---

## Database Tables

### 1. Customers

The `customers` table stores information about people who purchase products from the delivery company.

Each customer has a unique `customer_id` that identifies them in the database.

#### Main information stored:

* Customer ID
* Customer name
* Email address
* Phone number
* City

#### Purpose:

The table allows the company to keep track of its customers and identify which customer placed each order.

---

### 2. Products

The `products` table stores information about the products that the company sells.

Each product has a unique `product_id`.

#### Main information stored:

* Product ID
* Product name
* Product category
* Product price

#### Purpose:

The table provides information about the products that customers can purchase.

---

### 3. Orders

The `orders` table stores information about orders placed by customers.

Each order has a unique `order_id`. The `customer_id` connects the order to the customer who placed it.

#### Main information stored:

* Order ID
* Customer ID
* Order date
* Order status
* Total amount

#### Purpose:

The table keeps track of when orders were placed, which customer placed them, and the current status of each order.

---

### 4. Order Items

The `order_items` table stores the individual products included in each order.

An order can contain multiple products, and a product can appear in many different orders. Therefore, this table is used to connect the `orders` and `products` tables.

#### Main information stored:

* Order item ID
* Order ID
* Product ID
* Quantity

#### Purpose:

The table records which products were purchased in each order and how many of each product were ordered.

This table also solves the many-to-many relationship between orders and products.

For example, one order could contain:

* 1 Laptop
* 2 Keyboards
* 1 Mouse

Each of these products would be stored as a separate record in `order_items`.

---

### 5. Drivers

The `drivers` table stores information about the people responsible for delivering orders.

Each driver has a unique `driver_id`.

#### Main information stored:

* Driver ID
* Driver name
* Phone number

#### Purpose:

The table allows the company to keep track of its delivery drivers and identify which driver is responsible for each delivery.

---

### 6. Vehicles

The `vehicles` table stores information about the vehicles used by the delivery company.

Each vehicle has a unique `vehicle_id`.

#### Main information stored:

* Vehicle ID
* Registration number
* Vehicle type

#### Purpose:

The table allows the company to track the vehicles used to deliver orders.

Examples of vehicle types include:

* Van
* Truck
* Motorcycle

---

### 7. Deliveries

The `deliveries` table stores information about the delivery of an order.

It connects an order with the driver and vehicle responsible for delivering it.

#### Main information stored:

* Delivery ID
* Order ID
* Driver ID
* Vehicle ID
* Delivery date
* Delivery status

#### Purpose:

The table allows the company to track the delivery process, including which driver delivered an order, which vehicle was used, when the delivery took place, and whether the delivery was successful.

---

# Table Relationships

The database contains several relationships between the tables.

## Customers → Orders

One customer can place many orders.

This is a **one-to-many relationship**.

```text
customers 1 ─────────── * orders
```

The `customer_id` in the `orders` table is a foreign key that references the `customer_id` in the `customers` table.

---

## Orders → Order Items

One order can contain many order items.

This is a **one-to-many relationship**.

```text
orders 1 ─────────── * order_items
```

The `order_id` in `order_items` references the `order_id` in `orders`.

---

## Products → Order Items

One product can appear in many order items.

This is a **one-to-many relationship**.

```text
products 1 ─────────── * order_items
```

The `product_id` in `order_items` references the `product_id` in `products`.

---

## Orders → Products

Orders and products have a **many-to-many relationship**.

One order can contain many products, and one product can be included in many different orders.

Instead of directly connecting the two tables, the database uses the `order_items` table as a junction table.

```text
orders * ─────────── * products
             |
             |
        order_items
```

This design prevents duplicate information and makes the database more organized.

---

## Orders → Deliveries

Each order has a delivery record.

For this project, an order has one delivery.

```text
orders 1 ─────────── 1 deliveries
```

The `order_id` in `deliveries` identifies the order being delivered.

---

## Drivers → Deliveries

One driver can complete many deliveries.

This is a **one-to-many relationship**.

```text
drivers 1 ─────────── * deliveries
```

The `driver_id` in `deliveries` identifies the driver responsible for the delivery.

---

## Vehicles → Deliveries

One vehicle can be used for many deliveries.

This is a **one-to-many relationship**.

```text
vehicles 1 ─────────── * deliveries
```

The `vehicle_id` in `deliveries` identifies the vehicle used for the delivery.

---

# Overall Database Structure

The relationships can be summarized as follows:

```text
                    ┌──────────────┐
                    │  CUSTOMERS   │
                    └──────┬───────┘
                           │
                           │ 1
                           │
                           │ *
                    ┌──────▼───────┐
                    │    ORDERS    │
                    └──────┬───────┘
                           │
                           │ 1
                           │
                           │ *
                    ┌──────▼───────┐
                    │ ORDER_ITEMS  │
                    └──────┬───────┘
                           │
                           │ *
                           │
                           │ 1
                    ┌──────▼───────┐
                    │   PRODUCTS   │
                    └──────────────┘


                    ┌──────────────┐
                    │    ORDERS    │
                    └──────┬───────┘
                           │
                           │ 1
                           │
                           │ 1
                    ┌──────▼───────┐
                    │  DELIVERIES  │
                    └──────┬───────┘
                           │
                    ┌──────┴──────┐
                    │             │
                    ▼             ▼
             ┌───────────┐  ┌───────────┐
             │  DRIVERS  │  │  VEHICLES │
             └───────────┘  └───────────┘
```


