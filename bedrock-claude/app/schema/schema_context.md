# Database Schema Reference

## Tables

### customers
| Column      | Type         | Description                     |
|-------------|--------------|---------------------------------|
| customer_id | SERIAL (PK)  | Auto-increment customer ID      |
| first_name  | VARCHAR(100)  | Customer first name             |
| last_name   | VARCHAR(100)  | Customer last name              |
| email       | VARCHAR(255)  | Unique email address            |
| country     | VARCHAR(100)  | Country of residence            |
| signup_date | DATE          | Date the customer signed up     |
| is_active   | BOOLEAN       | Whether the customer is active  |

### products
| Column       | Type           | Description                    |
|--------------|----------------|--------------------------------|
| product_id   | SERIAL (PK)    | Auto-increment product ID      |
| product_name | VARCHAR(255)   | Product display name           |
| category     | VARCHAR(100)   | Product category (Loans, Accounts, Investments, Insurance) |
| price        | NUMERIC(10,2)  | Product price / principal amount |
| stock_qty    | INTEGER        | Available quantity              |
| created_at   | TIMESTAMP      | Record creation timestamp       |

### orders
| Column       | Type           | Description                    |
|--------------|----------------|--------------------------------|
| order_id     | SERIAL (PK)    | Auto-increment order ID        |
| customer_id  | INTEGER (FK)   | References customers.customer_id |
| order_date   | TIMESTAMP      | When the order was placed       |
| status       | VARCHAR(50)    | Order status: pending, completed, cancelled |
| total_amount | NUMERIC(12,2)  | Total order value               |

### order_items
| Column     | Type          | Description                     |
|------------|---------------|---------------------------------|
| item_id    | SERIAL (PK)   | Auto-increment item ID          |
| order_id   | INTEGER (FK)  | References orders.order_id      |
| product_id | INTEGER (FK)  | References products.product_id  |
| quantity   | INTEGER       | Quantity ordered                 |
| unit_price | NUMERIC(10,2) | Price per unit at time of order  |

## Common Queries

- Revenue by month: JOIN orders + order_items, GROUP BY month
- Active customers by country: filter customers WHERE is_active = TRUE
- Top products: JOIN order_items + products, aggregate by product_name
- Customer lifetime value: SUM(total_amount) per customer from orders
