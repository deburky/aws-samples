-- Sample schema for text2sql demo
-- Works on both PostgreSQL (RDS free tier) and Redshift

CREATE TABLE IF NOT EXISTS customers (
    customer_id    SERIAL PRIMARY KEY,
    first_name     VARCHAR(100) NOT NULL,
    last_name      VARCHAR(100) NOT NULL,
    email          VARCHAR(255) UNIQUE NOT NULL,
    country        VARCHAR(100),
    signup_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    is_active      BOOLEAN NOT NULL DEFAULT TRUE
);

CREATE TABLE IF NOT EXISTS products (
    product_id     SERIAL PRIMARY KEY,
    product_name   VARCHAR(255) NOT NULL,
    category       VARCHAR(100) NOT NULL,
    price          NUMERIC(10, 2) NOT NULL,
    stock_qty      INTEGER NOT NULL DEFAULT 0,
    created_at     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS orders (
    order_id       SERIAL PRIMARY KEY,
    customer_id    INTEGER NOT NULL REFERENCES customers(customer_id),
    order_date     TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    status         VARCHAR(50) NOT NULL DEFAULT 'pending',
    total_amount   NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS order_items (
    item_id        SERIAL PRIMARY KEY,
    order_id       INTEGER NOT NULL REFERENCES orders(order_id),
    product_id     INTEGER NOT NULL REFERENCES products(product_id),
    quantity       INTEGER NOT NULL,
    unit_price     NUMERIC(10, 2) NOT NULL
);
