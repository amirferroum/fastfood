# models/order.py
from models.database import get_connection
from datetime import datetime

class Order:
    @staticmethod
    def create(table_id, user_id, total, payment_type, status="pending"):
        """Insert a new order into the database."""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            INSERT INTO orders (table_id, user_id, total, payment_type, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (table_id, user_id, total, payment_type, status, datetime.now().isoformat()))

        conn.commit()
        order_id = cur.lastrowid
        conn.close()
        return order_id  # ✅ return the order ID to use in controller

    @staticmethod
    def all():
        """Return all orders with table and user info."""
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {
            "id": row[0],
            "table_name": row[1],
            "user_name": row[2],
            "total": row[3],
            "payment_type": row[4],
            "status": row[5],
            "created_at": row[6],
        }
        cur = conn.cursor()

        cur.execute("""
            SELECT o.id, 
                   t.table_number AS table_name, 
                   u.username AS user_name,
                   o.total, 
                   o.payment_type, 
                   o.status, 
                   o.created_at
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def filter(start_date=None, end_date=None, payment_type=None):
        """Return filtered orders by date range and payment type."""
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {
            "id": row[0],
            "table_name": row[1],
            "user_name": row[2],
            "total": row[3],
            "payment_type": row[4],
            "created_at": row[5],
        }
        cur = conn.cursor()

        query = """
            SELECT o.id, t.table_number AS table_name, u.username AS user_name,
                   o.total, o.payment_type, o.created_at
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            LEFT JOIN users u ON o.user_id = u.id
            WHERE 1=1
        """
        params = []

        if start_date:
            query += " AND o.created_at >= ?"
            params.append(start_date)
        if end_date:
            query += " AND o.created_at <= ?"
            params.append(end_date)
        if payment_type:
            query += " AND o.payment_type = ?"
            params.append(payment_type)

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def stats():
        """Return daily revenue for the last 7 days."""
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {
            "day": row[0],
            "daily_revenue": row[1],
        }
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                strftime('%Y-%m-%d', created_at) AS day,
                SUM(total) AS daily_revenue
            FROM orders
            GROUP BY day
            ORDER BY day DESC
            LIMIT 7
        """)
        rows = cur.fetchall()
        conn.close()
        return rows

    @staticmethod
    def get(order_id):
        """Return a single order with all details."""
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {
            "id": row[0],
            "table_id": row[1],
            "user_id": row[2],
            "total": row[3],
            "payment_type": row[4],
            "status": row[5],
            "created_at": row[6],
        }
        cur = conn.cursor()
        cur.execute("""
            SELECT id, table_id, user_id, total, payment_type, status, created_at
            FROM orders WHERE id=?
        """, (order_id,))
        order = cur.fetchone()
        conn.close()
        return order
