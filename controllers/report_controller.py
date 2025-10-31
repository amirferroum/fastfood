from models.database import get_connection
from datetime import datetime, timedelta

class ReportController:
    @staticmethod
    def get_sales_summary():
        conn = get_connection()
        cur = conn.cursor()

        today = datetime.now().date()
        week_ago = today - timedelta(days=7)
        month_ago = today - timedelta(days=30)

        cur.execute("SELECT SUM(total) FROM orders WHERE date(created_at)=?", (today,))
        today_sales = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(total) FROM orders WHERE date(created_at)>=?", (week_ago,))
        week_sales = cur.fetchone()[0] or 0

        cur.execute("SELECT SUM(total) FROM orders WHERE date(created_at)>=?", (month_ago,))
        month_sales = cur.fetchone()[0] or 0

        conn.close()
        return {"today": today_sales, "week": week_sales, "month": month_sales}


    @staticmethod
    def get_top_products(limit=5):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT p.name, SUM(oi.quantity) AS qty
            FROM order_items oi
            JOIN products p ON p.id = oi.product_id
            GROUP BY p.id
            ORDER BY qty DESC
            LIMIT ?
        """, (limit,))
        rows = cur.fetchall()
        conn.close()
        return [{"name": r["name"], "qty": r["qty"]} for r in rows]

    @staticmethod
    def get_sales_trend(days=7):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(f"""
            SELECT date(created_at) as d, SUM(total) as total
            FROM orders
            WHERE date(created_at) >= date('now', '-{days} day')
            GROUP BY date(created_at)
            ORDER BY date(created_at)
        """)
        rows = cur.fetchall()
        conn.close()
        return [{"date": r["d"], "total": r["total"]} for r in rows]

