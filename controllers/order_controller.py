import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from datetime import datetime
from models.order import Order
from PyQt6.QtWidgets import QFileDialog, QMessageBox
import os


class OrderController:
    # === CRUD & QUERY METHODS ===
    @staticmethod
    def get_all_orders():
        """Return all orders from DB"""
        return Order.all()

    @staticmethod
    def filter_orders(start_date=None, end_date=None, payment_type=None):
        """Filter orders"""
        return Order.filter(start_date, end_date, payment_type)

    @staticmethod
    def get_stats():
        """Get order stats for dashboard analytics"""
        return Order.stats()

    # === EXPORT FUNCTIONS ===
    @staticmethod
    def export_to_excel(orders, parent=None):
        """Export orders to Excel"""
        if not orders:
            QMessageBox.warning(parent, "Export Failed", "No data to export.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"orders_{timestamp}.xlsx"

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save Excel File",
            default_name,
            "Excel Files (*.xlsx);;CSV Files (*.csv)"
        )
        if not file_path:
            return

        try:
            df = pd.DataFrame(orders)
            if file_path.endswith(".csv"):
                df.to_csv(file_path, index=False)
            else:
                df.to_excel(file_path, index=False)

            QMessageBox.information(parent, "Success", f"Orders exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to export: {str(e)}")

    @staticmethod
    def export_to_pdf(orders, parent=None):
        """Export orders to PDF"""
        if not orders:
            QMessageBox.warning(parent, "Export Failed", "No data to export.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"orders_{timestamp}.pdf"

        file_path, _ = QFileDialog.getSaveFileName(
            parent,
            "Save PDF File",
            default_name,
            "PDF Files (*.pdf)"
        )
        if not file_path:
            return

        try:
            pdf = canvas.Canvas(file_path, pagesize=A4)
            width, height = A4
            pdf.setTitle("Orders Report")

            # === Header ===
            y = height - 50
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(200, y, "Orders Report")
            y -= 30

            pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            y -= 25

            # === Content ===
            for order in orders:
                text = (
                    f"#{order['id']} | Table: {order.get('table_name', '')} | "
                    f"User: {order.get('user_name', '')} | "
                    f"Total: {order['total']} | Payment: {order['payment_type']} | "
                    f"Date: {order['created_at']}"
                )
                pdf.drawString(40, y, text)
                y -= 15

                # === New page if space runs out ===
                if y < 50:
                    pdf.showPage()
                    y = height - 50
                    pdf.setFont("Helvetica", 10)

            pdf.save()
            QMessageBox.information(parent, "Success", f"Orders exported to:\n{file_path}")

        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to export: {str(e)}")
