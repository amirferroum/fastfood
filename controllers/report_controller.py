# controllers/report_controller.py
from models.database import get_connection
from datetime import datetime
import csv
from fpdf import FPDF  # pip install fpdf


class ReportController:
    @staticmethod
    def get_sales_summary(start_date=None, end_date=None):
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        cur = conn.cursor()

        query = "SELECT SUM(total) AS total_sales FROM orders"
        params = []

        if start_date and end_date:
            query += " WHERE created_at BETWEEN ? AND ?"
            params = [start_date, end_date]

        cur.execute(query, params)
        result = cur.fetchone()
        total_sales = result["total_sales"] if result and result["total_sales"] else 0

        conn.close()
        return {"total": total_sales}

    @staticmethod
    def get_category_sales(start_date=None, end_date=None):
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {col[0]: row[idx] for idx, col in enumerate(cursor.description)}
        cur = conn.cursor()

        query = """
            SELECT c.name AS category,
                   SUM(oi.quantity * oi.price) AS total
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            JOIN categories c ON p.category_id = c.id
            JOIN orders o ON oi.order_id = o.id
        """

        params = []
        if start_date and end_date:
            query += " WHERE o.created_at BETWEEN ? AND ?"
            params = [start_date, end_date]

        query += " GROUP BY c.id"

        cur.execute(query, params)
        rows = cur.fetchall()
        conn.close()

        return [{"category": r["category"], "total": r["total"] or 0} for r in rows]

    @staticmethod
    def export_sales_to_csv(filename, data):
        with open(filename, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["Category", "Total Sales (DA)"])
            for item in data:
                writer.writerow([item["category"], item["total"]])

    @staticmethod
    def export_sales_to_pdf(filename, data):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, "Sales Report", ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", "B", 12)
        pdf.cell(80, 10, "Category", border=1, align="C")
        pdf.cell(80, 10, "Total (DA)", border=1, align="C")
        pdf.ln()

        pdf.set_font("Arial", "", 12)
        for item in data:
            pdf.cell(80, 10, str(item["category"]), border=1)
            pdf.cell(80, 10, f"{item['total']:.2f}", border=1, align="R")
            pdf.ln()

        pdf.output(filename)
