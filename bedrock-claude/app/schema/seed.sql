-- Seed data for text2sql demo

INSERT INTO customers (first_name, last_name, email, country, signup_date, is_active) VALUES
('Alice',   'Johnson',  'alice@example.com',   'Nigeria',        '2024-01-15', TRUE),
('Bob',     'Smith',    'bob@example.com',     'Nigeria',        '2024-02-20', TRUE),
('Clara',   'Okafor',   'clara@example.com',   'Nigeria',        '2024-03-10', TRUE),
('David',   'Chen',     'david@example.com',   'United Kingdom', '2024-04-05', TRUE),
('Emma',    'Williams', 'emma@example.com',    'United States',  '2024-05-12', FALSE),
('Fatima',  'Adeyemi',  'fatima@example.com',  'Nigeria',        '2024-06-01', TRUE),
('George',  'Muller',   'george@example.com',  'Germany',        '2024-07-18', TRUE),
('Hannah',  'Ojo',      'hannah@example.com',  'Nigeria',        '2024-08-22', TRUE),
('Ibrahim', 'Bello',    'ibrahim@example.com', 'Nigeria',        '2024-09-03', TRUE),
('Jane',    'Doe',      'jane@example.com',    'United States',  '2024-10-11', FALSE)
ON CONFLICT DO NOTHING;

INSERT INTO products (product_name, category, price, stock_qty) VALUES
('Personal Loan 50k',    'Loans',      50000.00,  999),
('Personal Loan 100k',   'Loans',     100000.00,  999),
('Business Loan 500k',   'Loans',     500000.00,  999),
('Savings Account',      'Accounts',       0.00,  999),
('Fixed Deposit 90-day', 'Investments', 5000.00,  999),
('Insurance Basic',      'Insurance',   1500.00,  999),
('Insurance Premium',    'Insurance',   4500.00,  999)
ON CONFLICT DO NOTHING;

INSERT INTO orders (customer_id, order_date, status, total_amount) VALUES
(1, '2024-03-01 10:00:00', 'completed',  50000.00),
(2, '2024-03-15 14:30:00', 'completed', 100000.00),
(3, '2024-04-02 09:15:00', 'completed',  50000.00),
(1, '2024-05-10 11:00:00', 'completed',   1500.00),
(4, '2024-06-01 16:45:00', 'completed', 500000.00),
(5, '2024-06-20 08:30:00', 'cancelled', 100000.00),
(6, '2024-07-05 13:00:00', 'completed',  50000.00),
(7, '2024-08-12 10:30:00', 'pending',     4500.00),
(8, '2024-09-01 15:00:00', 'completed', 100000.00),
(9, '2024-10-15 09:45:00', 'completed',  55000.00),
(3, '2024-11-01 12:00:00', 'completed',   5000.00),
(2, '2024-12-01 14:00:00', 'pending',   104500.00)
ON CONFLICT DO NOTHING;

INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1,  1, 1,  50000.00),
(2,  2, 1, 100000.00),
(3,  1, 1,  50000.00),
(4,  6, 1,   1500.00),
(5,  3, 1, 500000.00),
(6,  2, 1, 100000.00),
(7,  1, 1,  50000.00),
(8,  7, 1,   4500.00),
(9,  2, 1, 100000.00),
(10, 1, 1,  50000.00),
(10, 4, 1,      0.00),
(10, 4, 1,   5000.00),
(11, 5, 1,   5000.00),
(12, 2, 1, 100000.00),
(12, 7, 1,   4500.00)
ON CONFLICT DO NOTHING;
