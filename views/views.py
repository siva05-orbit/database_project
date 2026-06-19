import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Connect to PostgreSQL
conn = psycopg2.connect(
    host=os.getenv("DB_HOST"),
    database=os.getenv("DB_NAME"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    port=os.getenv("DB_PORT")
)

cur = conn.cursor()

views = [

    # Query 1
    """
    CREATE OR REPLACE VIEW seller_dashboard_view AS
    SELECT
        sp.seller_id,
        sp.business_name,
        COUNT(DISTINCT oi.order_id) AS order_count,
        SUM(oi.quantity * oi.unit_price) AS total_revenue
    FROM seller_profiles sp
    LEFT JOIN products p
        ON sp.seller_id = p.seller_id
    LEFT JOIN order_items oi
        ON p.product_id = oi.product_id
    GROUP BY sp.seller_id, sp.business_name;
    """,

    # Query 2
    """
    CREATE OR REPLACE VIEW monthly_revenue_view AS
    WITH monthly_sales AS (
        SELECT
            DATE_TRUNC('month', o.created_at) AS sales_month,
            p.seller_id,
            SUM(oi.quantity * oi.unit_price) AS revenue
        FROM orders o
        JOIN order_items oi
            ON o.order_id = oi.order_id
        JOIN products p
            ON oi.product_id = p.product_id
        GROUP BY sales_month, p.seller_id
    )
    SELECT
        *,
        LAG(revenue) OVER (
            PARTITION BY seller_id
            ORDER BY sales_month
        ) AS previous_month_revenue
    FROM monthly_sales;
    """,

    # Query 3
    """
    CREATE OR REPLACE VIEW low_stock_view AS
    SELECT
        i.inventory_id,
        p.product_name,
        w.warehouse_name,
        i.quantity_available,
        i.reorder_threshold
    FROM inventory i
    JOIN products p
        ON i.product_id = p.product_id
    JOIN warehouses w
        ON i.warehouse_id = w.warehouse_id
    WHERE i.quantity_available < i.reorder_threshold;
    """,

    # Query 4
    """
    CREATE OR REPLACE VIEW customer_order_history_view AS
    SELECT
        o.order_id,
        u.full_name,
        o.order_status,
        p.payment_status,
        r.return_id
    FROM orders o
    JOIN customer_profiles cp
        ON o.customer_id = cp.customer_id
    JOIN users u
        ON cp.user_id = u.user_id
    LEFT JOIN payments p
        ON o.order_id = p.order_id
    LEFT JOIN order_items oi
        ON o.order_id = oi.order_id
    LEFT JOIN returns r
        ON oi.order_item_id = r.order_item_id;
    """,

    # Query 5
    """
    CREATE OR REPLACE VIEW abandoned_cart_view AS
    SELECT
        c.cart_id,
        u.email,
        COUNT(ci.cart_item_id) AS item_count,
        SUM(ci.quantity * p.base_price) AS cart_value
    FROM cart c
    JOIN customer_profiles cp
        ON c.customer_id = cp.customer_id
    JOIN users u
        ON cp.user_id = u.user_id
    LEFT JOIN cart_items ci
        ON c.cart_id = ci.cart_id
    LEFT JOIN products p
        ON ci.product_id = p.product_id
    WHERE c.expires_at < CURRENT_TIMESTAMP
    GROUP BY c.cart_id, u.email;
    """
]

try:

    for i, view_query in enumerate(views, start=1):
        cur.execute(view_query)
        print(f"View {i} created successfully")

    conn.commit()
    print("\nAll views created successfully!")

except Exception as e:
    conn.rollback()
    print("Error:", e)

finally:
    cur.close()
    conn.close()