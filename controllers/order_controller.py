# controllers/order_controller.py
import os
import cups
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from PyQt6.QtWidgets import QFileDialog, QMessageBox

from models.order import Order
from models.database import get_connection


class OrderController:
    # === CORE CRUD ===
    @staticmethod
    def create_order(table_id, user_id, total, payment_type="cash", status="pending"):
        """Create a new order and return its ID."""
        return Order.create(table_id, user_id, total, payment_type, status)

    @staticmethod
    def add_order_item(order_id, product_id, quantity, price):
        """Add a product to an order."""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO order_items (order_id, product_id, quantity, price)
            VALUES (?, ?, ?, ?)
        """, (order_id, product_id, quantity, price))
        conn.commit()
        conn.close()

    @staticmethod
    def get_order_items(order_id):
        """Fetch all items for a given order."""
        conn = get_connection()
        conn.row_factory = lambda cursor, row: {
            "quantity": row[0],
            "product_name": row[1],
            "price": row[2]
        }
        cur = conn.cursor()
        cur.execute("""
            SELECT oi.quantity, p.name, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = cur.fetchall()
        conn.close()
        return items

    @staticmethod
    def get_all_orders():
        return Order.all()

    @staticmethod
    def filter_orders(start_date=None, end_date=None, payment_type=None):
        return Order.filter(start_date, end_date, payment_type)

    @staticmethod
    def get_stats():
        return Order.stats()

    # === EXPORTS ===
    @staticmethod
    def export_to_excel(orders, parent=None):
        """Export all orders to Excel or CSV."""
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
            QMessageBox.information(parent, "Success", f"Exported to:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Export failed:\n{e}")

    @staticmethod
    def export_to_pdf(orders, parent=None):
        """Export orders to a PDF report."""
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

            y = height - 50
            pdf.setFont("Helvetica-Bold", 16)
            pdf.drawString(200, y, "Orders Report")
            y -= 30

            pdf.setFont("Helvetica", 10)
            pdf.drawString(40, y, f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            y -= 25

            for order in orders:
                text = (
                    f"#{order['id']} | Table: {order.get('table_name', '')} | "
                    f"User: {order.get('user_name', '')} | "
                    f"Total: {order['total']} | Payment: {order['payment_type']} | "
                    f"Date: {order['created_at']}"
                )
                pdf.drawString(40, y, text)
                y -= 15
                if y < 50:
                    pdf.showPage()
                    y = height - 50
                    pdf.setFont("Helvetica", 10)

            pdf.save()
            QMessageBox.information(parent, "Success", f"PDF saved:\n{file_path}")
        except Exception as e:
            QMessageBox.critical(parent, "Error", f"Failed to export: {e}")

    # === PRINT RECEIPT ===
    @staticmethod
    def print_receipt(order_id):
        """Print a receipt to the cashier printer via CUPS."""
        conn = get_connection()
        cur = conn.cursor()

        # Get order info
        cur.execute("""
            SELECT o.id, o.total, o.created_at, t.name AS table_name
            FROM orders o
            LEFT JOIN tables t ON o.table_id = t.id
            WHERE o.id = ?
        """, (order_id,))
        order = cur.fetchone()
        if not order:
            raise Exception("Order not found.")

        # Get order items
        cur.execute("""
            SELECT p.name, oi.quantity, oi.price
            FROM order_items oi
            JOIN products p ON oi.product_id = p.id
            WHERE oi.order_id = ?
        """, (order_id,))
        items = cur.fetchall()
        conn.close()

        # Build receipt text
        receipt_text = f"*** {order['table_name']} ***\n"
        receipt_text += f"Order #{order['id']}\nDate: {order['created_at']}\n"
        receipt_text += "-" * 30 + "\n"
        for item in items:
            receipt_text += f"{item['name']} x{item['quantity']}  {item['price'] * item['quantity']:.2f} DZD\n"
        receipt_text += "-" * 30 + "\n"
        receipt_text += f"TOTAL: {order['total']:.2f} DZD\n"
        receipt_text += "*** THANK YOU ***\n"

        # Print via CUPS
        try:
            conn_cups = cups.Connection()
            printers = conn_cups.getPrinters()
            if not printers:
                raise Exception("No printer found in CUPS.")

            printer_name = list(printers.keys())[0]
            temp_path = f"/tmp/receipt_{order_id}.txt"
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(receipt_text)

            conn_cups.printFile(printer_name, temp_path, f"Order {order_id}", {})
            os.remove(temp_path)
        except Exception as e:
            print(f"Failed to print: {e}")
            raise



    @staticmethod
    def send_to_category_printers(order_id):
        """Send order items to category printers after order is saved."""
        def _do_print():
            try:
                conn = get_connection()
                cur = conn.cursor()

                # 1. Fetch all order items with categories
                cur.execute("""
                    SELECT oi.quantity, oi.price, p.name AS product_name, c.name AS category_name
                    FROM order_items oi
                    JOIN products p ON oi.product_id = p.id
                    JOIN categories c ON p.category_id = c.id
                    WHERE oi.order_id = ?
                """, (order_id,))
                items = cur.fetchall()
                if not items:
                    print(f"No items found for order {order_id}")
                    return

                # 2. Group by category
                grouped = {}
                for item in items:
                    cat = item["category_name"]
                    grouped.setdefault(cat, []).append(item)

                # 3. Get all printers
                cur.execute("SELECT * FROM printers")
                printers = cur.fetchall()

                # 4. Match categories to printers
                for printer in printers:
                    assigned = [c.strip() for c in printer["assigned_categories"].split(",") if c.strip()]
                    for cat, cat_items in grouped.items():
                        if cat in assigned:
                            OrderController._print_to_printer(printer, cat_items, order_id, cat)

                conn.close()

            except Exception as e:
                print(f"⚠️ Failed sending to category printers: {e}")

        # run in background thread to avoid UI blocking
        threading.Thread(target=_do_print, daemon=True).start()

    @staticmethod
    def _print_to_printer(printer, items, order_id, category_name):
        """Example printer handler (replace with real printer logic)."""
        print(f"\n🖨️ Sending order #{order_id} - category {category_name} to printer {printer['name']}")

        # Example: Just simulate print for now
        for item in items:
            print(f"   {item['product_name']} x{item['quantity']} - {item['price']} DZD")

        print(f"✅ Done printing for {printer['name']}")
