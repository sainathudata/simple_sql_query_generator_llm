C:/sainathudata/projects/simple_sql_query_generator>uv run main.py
--- Database Schema ---
# Database Schema (MSSQL)

## Table: customers
Columns:
- customer_id: int NOT NULL (PRIMARY KEY)
- name: nvarchar NULL
- email: nvarchar NULL
- created_at: datetime2 NULL

## Table: orders
Columns:
- order_id: int NOT NULL (PRIMARY KEY)
- customer_id: int NULL
- order_date: date NULL
- total_amount: decimal NULL

Foreign Keys:
- customer_id → customers.customer_id


User Question: Show me the top 5 customers by total order amount.

--- Generated SQL ---
SELECT TOP 5
    c.customer_id,
    c.name,
    COALESCE(SUM(o.total_amount), 0) AS total_order_amount
FROM
    customers AS c
LEFT JOIN
    orders AS o ON c.customer_id = o.customer_id
GROUP BY
    c.customer_id, c.name
ORDER BY
    total_order_amount DESC;