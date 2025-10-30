# models/order.py
from models.database import get_connection
from datetime import datetime

class Order:
    @staticmethod
    def create(table_id, user_id, total, payment_type):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO orders (table_id, user_id, total, payment_type, created_at)
            VALUES (?, ?, ?, ?, ?)
        """, (table_id, user_id, total, payment_type, datetime.now().isoformat()))
        conn.commit()
        conn.close()

    @staticmethod
    def all():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT o.id, t.name AS table_name, u.username AS user_name,
                   o.total, o.payment_type, o.created_at
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            LEFT JOIN users u ON o.user_id = u.id
            ORDER BY o.created_at DESC
        """)
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def filter(start_date=None, end_date=None, payment_type=None):
        conn = get_connection()
        cur = conn.cursor()
        query = """
            SELECT o.id, t.name AS table_name, u.username AS user_name,
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
        return [dict(row) for row in rows]

    @staticmethod
    def stats():
        conn = get_connection()
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
        return [dict(row) for row in rows]
