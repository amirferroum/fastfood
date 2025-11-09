# ui/pos_window.py
import sys
from functools import partial
import cups
import time
import os
import tempfile
import sqlite3
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QScrollArea, QGridLayout, QTableWidget, QTableWidgetItem,
    QSizePolicy, QLineEdit, QInputDialog, QMessageBox, QSpacerItem, QSizePolicy as QSP
)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QSizePolicy as QSP, QSpacerItem
from models.database import get_connection
from PyQt6.QtWidgets import QMessageBox, QTableWidgetItem
from datetime import datetime
import json
from controllers.order_controller import OrderController

# try import project controllers/models; handle gracefully if absent
try:
    from models.category import Category
except Exception:
    Category = None

try:
    from models.product import Product
except Exception:
    Product = None

try:
    from controllers.order_controller import OrderController
except Exception:
    OrderController = None

try:
    from controllers.printer_controller import PrinterController
except Exception:
    PrinterController = None

try:
    from ui.login_window import LoginWindow
except Exception:
    LoginWindow = None

# config helper used to clear saved login on logout
try:
    from utils.config_manager import save_config
except Exception:
    def save_config(_): pass


class POSWindow(QMainWindow):
    def __init__(self, role="cashier", user_id=None):
        super().__init__()
        self.role = role
        self.current_user_id = user_id
        self.selected_table = None
        self.cart_items = []  # ✅ initialize empty cart list

        self.setWindowTitle("🍟 FastFood — POS")
        self.setGeometry(100, 80, 1250, 760)

        # cart: list of dicts {product_id, name, price, cost(optional), qty}
        self.cart = []

        # central
        central = QWidget()
        self.setCentralWidget(central)
        self.main_layout = QVBoxLayout(central)
        self.main_layout.setContentsMargins(12, 12, 12, 12)
        self.main_layout.setSpacing(10)

        # top bar
        self._build_topbar()

        # main area: categories | products | cart
        self._build_main_area()

        # bottom bar (quick actions)
        self._build_bottombar()

        self.apply_style()

        # initial load
        self.load_categories()
        self.load_products()  # all products by default
        self.update_cart_table()

    # -----------------------
    # UI Builders
    # -----------------------
    def _build_topbar(self):
        top = QFrame()
        top.setObjectName("topbar")
        top_layout = QHBoxLayout(top)
        top_layout.setContentsMargins(8, 4, 8, 4)
        top_layout.setSpacing(6)

        # Tables button
        self.btn_toggle_tables = QPushButton("🪑 Tables")
        self.btn_toggle_tables.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_toggle_tables.setFixedHeight(34)
        self.btn_toggle_tables.setStyleSheet("""
            QPushButton {
                background-color: #0078d7;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #005fa3;
            }
        """)
        self.btn_toggle_tables.clicked.connect(self._toggle_tables_placeholder)

        # Search input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("🔎 Search products...")
        self.search_input.setFixedHeight(32)
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: 1px solid #d0d0d0;
                border-radius: 6px;
                padding: 4px 10px;
                font-size: 13px;
                background-color: #fafafa;
            }
            QLineEdit:focus {
                border: 1px solid #0078d7;
                background-color: #ffffff;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)

        # Selected table label
        self.lbl_selected_table = QLabel("Table: —")
        self.lbl_selected_table.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_selected_table.setMinimumWidth(120)
        self.lbl_selected_table.setStyleSheet("font-size: 13px; color: #333;")

        # Logout button
        self.btn_logout = QPushButton("🚪 Logout")
        self.btn_logout.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_logout.setFixedHeight(34)
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #ff7043;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 6px 14px;
                font-size: 13px;
            }
            QPushButton:hover {
                background-color: #f4511e;
            }
        """)
        self.btn_logout.clicked.connect(self._handle_logout)

        # Layout arrangement
        top_layout.addWidget(self.btn_toggle_tables)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.search_input, 2)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_selected_table)
        top_layout.addSpacing(8)
        top_layout.addWidget(self.btn_logout)

        # Reduce top bar height
        top.setFixedHeight(50)

        self.main_layout.addWidget(top)


    def _build_main_area(self):
        # Wrap the POS layout in a content area frame
        self.content_area = QFrame()
        area_layout = QHBoxLayout(self.content_area)
        area_layout.setSpacing(12)
        area_layout.setContentsMargins(0, 0, 0, 0)

        # --- left: categories (vertical scroll) ---
        cat_card = QFrame()
        cat_card.setObjectName("card")
        cat_layout = QVBoxLayout(cat_card)
        cat_layout.setContentsMargins(12, 12, 12, 12)
        cat_layout.setSpacing(8)

        title = QLabel("Categories")
        title.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        cat_layout.addWidget(title)

        self.scroll_categories = QScrollArea()
        self.scroll_categories.setWidgetResizable(True)
        self.scroll_cat_content = QWidget()
        self.scroll_cat_layout = QVBoxLayout(self.scroll_cat_content)
        self.scroll_cat_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_categories.setWidget(self.scroll_cat_content)
        cat_layout.addWidget(self.scroll_categories)
        cat_layout.addItem(QSpacerItem(20, 20, QSP.Policy.Expanding, QSP.Policy.Expanding))

        area_layout.addWidget(cat_card, 10)

        # --- middle: product grid ---
        prod_card = QFrame()
        prod_card.setObjectName("card")
        prod_layout = QVBoxLayout(prod_card)
        prod_layout.setContentsMargins(12, 12, 12, 12)
        prod_layout.setSpacing(8)

        ptitle = QLabel("Products")
        ptitle.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        prod_layout.addWidget(ptitle)

        # grid area inside scroll
        self.prod_scroll = QScrollArea()
        self.prod_scroll.setWidgetResizable(True)
        self.prod_container = QWidget()
        self.prod_grid = QGridLayout(self.prod_container)
        self.prod_grid.setSpacing(10)
        self.prod_scroll.setWidget(self.prod_container)
        prod_layout.addWidget(self.prod_scroll)

        area_layout.addWidget(prod_card, 26)

        # --- right: cart ---
        cart_card = QFrame()
        cart_card.setObjectName("card")
        cart_layout = QVBoxLayout(cart_card)
        cart_layout.setContentsMargins(12, 12, 12, 12)
        cart_layout.setSpacing(8)

        ctitle_layout = QHBoxLayout()
        ctitle = QLabel("🧾 Cart")
        ctitle.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        ctitle_layout.addWidget(ctitle)
        ctitle_layout.addStretch()
        self.btn_clear = QPushButton("Clear")
        self.btn_clear.clicked.connect(self.clear_cart)
        ctitle_layout.addWidget(self.btn_clear)
        cart_layout.addLayout(ctitle_layout)

        self.table_cart = QTableWidget(0, 4)
        self.table_cart.setHorizontalHeaderLabels(["Item", "Qty", "Price", ""])
        self.table_cart.horizontalHeader().setStretchLastSection(False)
        self.table_cart.setColumnWidth(0, 140)
        self.table_cart.setColumnWidth(1, 60)
        self.table_cart.setColumnWidth(2, 80)
        self.table_cart.setColumnWidth(3, 80)
        self.table_cart.cellDoubleClicked.connect(self._edit_qty)
        cart_layout.addWidget(self.table_cart)

        self.lbl_total = QLabel("Total: 0.00 DA")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.lbl_profit = QLabel("")  # shown only if cost data exists
        self.lbl_profit.setAlignment(Qt.AlignmentFlag.AlignRight)
        cart_layout.addWidget(self.lbl_profit)
        cart_layout.addWidget(self.lbl_total)

        self.btns_frame = QFrame()
        btns_layout = QHBoxLayout(self.btns_frame)
        self.btn_print = QPushButton("🖨 Print")
        self.btn_print.clicked.connect(self._print_receipt)
        self.btn_execute = QPushButton("✅ Execute (Pay)")
        self.btn_execute.clicked.connect(self._execute_order)
        btns_layout.addWidget(self.btn_print)
        btns_layout.addWidget(self.btn_execute)
        cart_layout.addWidget(self.btns_frame)

        area_layout.addWidget(cart_card, 14)

        # ✅ Add content area to the main layout
        self.main_layout.addWidget(self.content_area)


    def _build_bottombar(self):
        footer = QFrame()
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(6, 6, 6, 6)

        info = QLabel("FastFood POS • Local Mode")
        footer_layout.addWidget(info)
        footer_layout.addStretch()
        help_btn = QPushButton("Help")
        help_btn.clicked.connect(self._show_help)
        footer_layout.addWidget(help_btn)

        self.main_layout.addWidget(self.content_area)

    # -----------------------
    # Data Loading
    # -----------------------
    def load_categories(self):
        # clear existing
        for i in reversed(range(self.scroll_cat_layout.count())):
            w = self.scroll_cat_layout.itemAt(i).widget()
            if w:
                w.setParent(None)

        cats = []
        if Category:
            try:
                cats = getattr(Category, "all", getattr(Category, "get_all", lambda: []) )()
            except Exception:
                try:
                    cats = Category.all()
                except Exception:
                    cats = []
        else:
            cats = []

        # "All" button
        btn_all = QPushButton("All")
        btn_all.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_all.clicked.connect(lambda: self.load_products(None))
        btn_all.setStyleSheet("padding:8px; text-align:left;")
        self.scroll_cat_layout.addWidget(btn_all)

        for c in cats:
            name = c.get("name") if isinstance(c, dict) else str(c)
            cid = c.get("id") if isinstance(c, dict) and "id" in c else None
            btn = QPushButton(name)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.clicked.connect(partial(self.load_products, cid))
            btn.setStyleSheet("padding:8px; text-align:left;")
            self.scroll_cat_layout.addWidget(btn)

    def load_products(self, category_id=None, search_term=""):
        # clear grid
        for i in reversed(range(self.prod_grid.count())):
            item = self.prod_grid.itemAt(i)
            if item:
                w = item.widget()
                if w:
                    w.setParent(None)

        products = []
        if Product:
            # try common APIs
            try:
                getter = getattr(Product, "all", getattr(Product, "get_all", None))
                if getter:
                    products = getter()
                else:
                    products = []
            except Exception:
                try:
                    products = Product.get_all()
                except Exception:
                    products = []
        else:
            products = []

        # filter by category & search
        def matches(p):
            if category_id:
                pid_cat = p.get("category_id") if isinstance(p, dict) else None
                if pid_cat != category_id:
                    return False
            if search_term:
                name = p.get("name", "") if isinstance(p, dict) else str(p)
                if search_term.lower() not in name.lower():
                    return False
            return True

        # if products might be sqlite3.Row, convert to dict-like safely
        pr_list = []
        for p in products:
            try:
                pr = dict(p)
            except Exception:
                # maybe p is object or dict already
                pr = p if isinstance(p, dict) else {"id": getattr(p, "id", None), "name": str(p)}
            pr_list.append(pr)

        filtered = [p for p in pr_list if matches(p)]

        # grid rendering: 3 columns
        cols = 3
        for idx, p in enumerate(filtered):
            r = idx // cols
            c = idx % cols
            card = self._make_product_card(p)
            self.prod_grid.addWidget(card, r, c)

    def _make_product_card(self, product):
        # product is dict-like
        pid = product.get("id")
        name = product.get("name", "Unknown")
        price = product.get("price", 0.0) or 0.0
        cost = product.get("cost", None)

        card = QFrame()
        card.setObjectName("prod_card")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(6)

        lbl_name = QLabel(name)
        lbl_name.setWordWrap(True)
        lbl_name.setFont(QFont("Segoe UI", 10, QFont.Weight.Medium))
        layout.addWidget(lbl_name)

        lbl_price = QLabel(f"Price: {price:.2f} DA")
        layout.addWidget(lbl_price)

        if cost is not None:
            try:
                cost_f = float(cost)
                lbl_cost = QLabel(f"Cost: {cost_f:.2f} DA")
                lbl_cost.setStyleSheet("color: #666; font-size: 12px;")
                layout.addWidget(lbl_cost)
            except Exception:
                pass

        btn_add = QPushButton("➕ Add")
        btn_add.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_add.clicked.connect(partial(self.add_to_cart, product))
        layout.addStretch()
        layout.addWidget(btn_add)

        return card

    # -----------------------
    # Cart operations
    # -----------------------
    def add_to_cart(self, product):
        pid = product.get("id")
        # find in cart
        for item in self.cart:
            if item["product_id"] == pid:
                item["qty"] += 1
                self.update_cart_table()
                return

        # else add new
        self.cart.append({
            "product_id": pid,
            "name": product.get("name", "Item"),
            "price": float(product.get("price") or 0),
            "cost": float(product.get("cost") or 0) if product.get("cost") is not None else None,
            "qty": 1
        })
        self.update_cart_table()

    def update_cart_table(self):
        self.table_cart.setRowCount(0)
        total = 0.0
        total_cost = 0.0
        for row_idx, item in enumerate(self.cart):
            self.table_cart.insertRow(row_idx)
            self.table_cart.setItem(row_idx, 0, QTableWidgetItem(item["name"]))
            self.table_cart.setItem(row_idx, 1, QTableWidgetItem(str(item["qty"])))
            self.table_cart.setItem(row_idx, 2, QTableWidgetItem(f"{item['price'] * item['qty']:.2f}"))

            # actions cell: + / - / remove
            btns = QWidget()
            b_layout = QHBoxLayout(btns)
            b_layout.setContentsMargins(0, 0, 0, 0)
            inc = QPushButton("+")
            dec = QPushButton("-")
            rem = QPushButton("✖")
            inc.setFixedSize(QSize(28, 24)); dec.setFixedSize(QSize(28, 24)); rem.setFixedSize(QSize(28, 24))
            inc.clicked.connect(partial(self._change_qty, row_idx, 1))
            dec.clicked.connect(partial(self._change_qty, row_idx, -1))
            rem.clicked.connect(partial(self._remove_item, row_idx))
            b_layout.addWidget(inc)
            b_layout.addWidget(dec)
            b_layout.addWidget(rem)
            self.table_cart.setCellWidget(row_idx, 3, btns)

            total += item["price"] * item["qty"]
            if item.get("cost") is not None:
                total_cost += item["cost"] * item["qty"]

        self.lbl_total.setText(f"Total: {total:.2f} DA")
        if total_cost:
            profit = total - total_cost
            self.lbl_profit.setText(f"Profit: {profit:.2f} DA (Revenue {total:.2f} - Cost {total_cost:.2f})")
        else:
            self.lbl_profit.setText("")

    def _change_qty(self, row_idx, delta):
        if row_idx < 0 or row_idx >= len(self.cart):
            return
        self.cart[row_idx]["qty"] += delta
        if self.cart[row_idx]["qty"] <= 0:
            self.cart.pop(row_idx)
        self.update_cart_table()

    def _remove_item(self, row_idx):
        if 0 <= row_idx < len(self.cart):
            self.cart.pop(row_idx)
            self.update_cart_table()

    def clear_cart(self):
        if not self.cart:
            return
        confirm = QMessageBox.question(self, "Clear Cart", "Remove all items from cart?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if confirm == QMessageBox.StandardButton.Yes:
            self.cart = []
            self.update_cart_table()

    def _edit_qty(self, row, col):
        # only allow editing qty cell (col 1)
        if col != 1 or row < 0 or row >= len(self.cart):
            return
        current = self.cart[row]["qty"]
        qty, ok = QInputDialog.getInt(self, "Edit Quantity", "Quantity:", value=current, min=1, max=999)
        if ok:
            self.cart[row]["qty"] = qty
            self.update_cart_table()

    # -----------------------
    # Actions: print / execute
    # -----------------------
    def _print_order(self):
        if not self.cart:
            QMessageBox.warning(self, "Empty Cart", "Cart is empty.")
            return
        try:
            if PrinterController and hasattr(PrinterController, "print_order"):
                # create minimal order object to print
                order = {"items": self.cart, "total": sum(i["price"] * i["qty"] for i in self.cart)}
                PrinterController.print_order(order)
                QMessageBox.information(self, "Printed", "Order sent to printer.")
            else:
                QMessageBox.information(self, "Print (demo)", "PrinterController not available — demo print OK.")
        except Exception as e:
            QMessageBox.warning(self, "Print Error", f"Failed to print: {e}")

    def _execute_order(self):
        """
        Save the current cart as a pending order via OrderController.
        This moves all DB writes to the controller to avoid DB lock issues.
        """
        try:
            if not getattr(self, "selected_table", None):
                QMessageBox.warning(self, "Error", "Please select a table first.")
                return

            if not self.cart:
                QMessageBox.warning(self, "Error", "The cart is empty.")
                return

            # Compute total from cart
            total = 0.0
            for it in self.cart:
                qty = int(it.get("qty", it.get("quantity", 1)))
                price = float(it.get("price", 0.0))
                total += qty * price

            # Create order via controller (returns order_id)
            order_id = OrderController.create_order(
                table_id=self.selected_table,
                user_id=self.current_user_id,
                total=total,
                payment_type="cash",
                status="pending"
            )

            if not order_id:
                raise Exception("OrderController failed to create order (no id returned).")

            # Insert items via controller
            for it in self.cart:
                product_id = it.get("product_id") or it.get("id")
                qty = int(it.get("qty", it.get("quantity", 1)))
                price = float(it.get("price", 0.0))
                OrderController.add_order_item(order_id, product_id, qty, price)

            # Optionally send to category printers using existing helper (keeps printing isolated)
            # We build items_by_category similarly to previous behavior but do it after DB ops:
            items_by_category = {}
            try:
                # group by category for kitchen printers (touch DB only inside controller helpers or short connections)
                conn = get_connection()
                cur = conn.cursor()
                for it in self.cart:
                    pid = it.get("product_id") or it.get("id")
                    cur.execute("SELECT category_id, name FROM products WHERE id=?", (pid,))
                    prod = cur.fetchone()
                    cat_id = prod["category_id"] if prod else None
                    name = prod["name"] if prod and "name" in prod.keys() else it.get("name", "Item")
                    qty = int(it.get("qty", it.get("quantity", 1)))
                    items_by_category.setdefault(cat_id, []).append(f"{name} x{qty}")
                conn.close()
            except Exception:
                # If product lookups fail, just proceed without category printers
                items_by_category = {}

            # send to per-category printers (if any)
            try:
                if items_by_category:
                    OrderController.print_receipt(order_id)
            except Exception as e:
                print("Printer error (category):", e)
                QMessageBox.warning(self, "Printer Warning", f"Failed sending to category printers: {e}")

            # Mark table as occupied
            self._mark_table_as_occupied(self.selected_table)

            # Keep the cart (or clear, depending on your flow). We'll keep it as pending but clear UI if you want:
            # self.cart = []
            # self.update_cart_table()

            QMessageBox.information(self, "Success", f"Order saved (id {order_id}) as pending for Table {self.selected_table}.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to execute order:\n{e}")



    def _load_table_order(self, table_id):
        """Load existing pending order for a table into the cart table."""
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT o.id
            FROM orders o
            WHERE o.table_id=? AND o.status='pending'
        """, (table_id,))
        order = cursor.fetchone()

        self.cart = []
        self.table_cart.setRowCount(0)

        if order:
            order_id = order["id"]
            cursor.execute("""
                SELECT p.name, oi.quantity, oi.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id=?
            """, (order_id,))
            rows = cursor.fetchall()

            for r in rows:
                self.cart.append({
                    "product_id": None,
                    "name": r["name"],
                    "qty": r["quantity"],
                    "price": r["price"]
                })

            self.update_cart_table()
        else:
            self.clear_cart()

        conn.close()




    # -----------------------
    # Helpers & placeholders
    # -----------------------
    def _toggle_tables_placeholder(self):
        """Toggle between product view and full tables view"""
        if hasattr(self, "tables_visible") and self.tables_visible:
            # back to POS view
            self.tables_frame.hide()
            self.content_area.show()
            self.btn_toggle_tables.setText("🪑 Tables")
            self.tables_visible = False
        else:
            # show tables full screen
            if not hasattr(self, "tables_frame"):
                self._build_tables_view()
            self.content_area.hide()
            self.tables_frame.show()
            self.btn_toggle_tables.setText("🍔 POS View")
            self.tables_visible = True

    
    def _build_tables_view(self):
        """Build full-screen tables view"""
        self.tables_frame = QFrame()
        self.tables_layout = QGridLayout(self.tables_frame)  # ✅ FIXED
        self.tables_layout.setContentsMargins(40, 40, 40, 40)
        self.tables_layout.setSpacing(24)

        table_count = 12
        cols = 4
        for i in range(table_count):
            btn = QPushButton(f"Table {i + 1}")
            btn.setCheckable(True)
            btn.setMinimumSize(150, 100)
            btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Medium))
            btn.clicked.connect(partial(self._select_table, i + 1))
            self.tables_layout.addWidget(btn, i // cols, i % cols)

        self.main_layout.addWidget(self.tables_frame)
        self.tables_frame.hide()
        self.tables_visible = False


    
    def _select_table(self, table_number):
        """Select a table and mark it as active"""
        self.selected_table = table_number
        self.lbl_selected_table.setText(f"Table: {table_number}")

        # visually uncheck all other table buttons
        for i in range(self.tables_layout.count()):
            w = self.tables_layout.itemAt(i).widget()
            if isinstance(w, QPushButton):
                w.setChecked(w.text() == f"Table {table_number}")

        # ✅ Load any existing pending order for this table into the cart
        self._load_table_order(table_number)

    def _calculate_total(self):
        total = 0
        for i in range(self.table_cart.rowCount()):
            qty = int(self.table_cart.item(i, 1).text())
            price = float(self.table_cart.item(i, 2).text())
            total += qty * price
        return total


    def _on_search(self, text):
        # re-run load_products with search term
        self.load_products(category_id=None, search_term=text)

    def _show_help(self):
        QMessageBox.information(self, "Help", "POS window: click a product to add to cart.\nDouble-click Qty cell to edit.\nUse Print / Execute to handle the order.")

    # -----------------------
    # Logout
    # -----------------------
    def _handle_logout(self):
        reply = QMessageBox.question(self, "Logout", "Sign out and return to login?", QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply != QMessageBox.StandardButton.Yes:
            return

        # clear remembered login
        try:
            save_config({})
        except Exception:
            pass

        self.close()
        # reopen login window if available:
        try:
            if LoginWindow:
                login = LoginWindow()
                login.show()
                # keep reference to prevent GC
                self._login_ref = login
            else:
                QMessageBox.information(self, "Logged out", "You are logged out.")
        except Exception as e:
            QMessageBox.information(self, "Logout", f"Logged out. ({e})")

  
    def _print_receipt(self):
        """
        Print the latest order for the selected table via OrderController.print_receipt(),
        then mark the table free and clear the cart UI.
        """
        try:
            if not getattr(self, "selected_table", None):
                QMessageBox.warning(self, "No Table", "Please select a table first.")
                return

            # Find the last order id for this table (most recent)
            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT id FROM orders
                    WHERE table_id=? 
                    ORDER BY created_at DESC
                    LIMIT 1
                """, (self.selected_table,))
                row = cur.fetchone()

            if not row:
                QMessageBox.warning(self, "No Order", "No order found for this table.")
                return

            order_id = row["id"]

            # Use controller to print (controller opens/closes its own DB connections)
            try:
                OrderController.print_receipt(order_id)
            except Exception as e:
                # surface the error but do not leave DB open here (controller handles its own DB)
                QMessageBox.critical(self, "Print Error", f"Failed to print receipt: {e}")
                return

            # Mark table free after printing
            self._mark_table_as_free(self.selected_table)

            # Clear cart UI and internal cart
            self.cart = []
            self.update_cart_table()
            self.lbl_selected_table.setText("Table: —")
            self.selected_table = None

            QMessageBox.information(self, "Done", "Receipt printed and table cleared.")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to print:\n{e}")

    def _mark_table_as_occupied(self, table_id):
        """
        Try to mark a table as occupied. We try common table schemas:
        - If table has 'status' column: set to 'occupied'
        - Else if it has 'occupied' numeric/boolean column: set to 1
        Silence errors (UI should continue).
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                # try status column first
                try:
                    cur.execute("UPDATE tables SET status=? WHERE id=?", ("occupied", table_id))
                    conn.commit()
                    return
                except Exception:
                    # fallback to occupied boolean/int column
                    try:
                        cur.execute("UPDATE tables SET occupied=? WHERE id=?", (1, table_id))
                        conn.commit()
                        return
                    except Exception:
                        # nothing else to do
                        return
        except Exception:
            return


    def _mark_table_as_free(self, table_id):
        """
        Mark table as free after printing/completing order.
        Mirror logic of _mark_table_as_occupied.
        """
        try:
            with get_connection() as conn:
                cur = conn.cursor()
                try:
                    cur.execute("UPDATE tables SET status=? WHERE id=?", ("free", table_id))
                    conn.commit()
                    return
                except Exception:
                    try:
                        cur.execute("UPDATE tables SET occupied=? WHERE id=?", (0, table_id))
                        conn.commit()
                        return
                    except Exception:
                        return
        except Exception:
            return



    def _print_with_cups(self, receipt_text, printer_name):
        try:
            conn = cups.Connection()

            # Save receipt temporarily
            tmp_path = "/tmp/receipt.txt"
            with open(tmp_path, "w") as f:
                f.write(receipt_text)

            # Send to printer
            conn.printFile(printer_name, tmp_path, "Receipt", {})
            print(f"🖨️ Sent to printer: {printer_name}")

        except Exception as e:
            print(f"❌ Printing failed: {e}")

    def _send_to_cashier_printer(self, order_id):
        """
        Send the receipt to the cashier printer via CUPS.
        Expects printers table to contain either a 'cups_name' column or 'name' field
        that matches an available CUPS printer queue.
        """
        # Get printer from DB
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM printers WHERE assigned_categories LIKE '%cashier%' AND status='online' LIMIT 1")
            printer = cursor.fetchone()

        if not printer:
            raise Exception("No online cashier printer (assigned 'cashier') found in DB.")

        # determine the queue name to use with CUPS
        cups_queue = None
        # if you store an explicit cups queue name column, prefer it (recommended):
        if "cups_name" in printer.keys() and printer["cups_name"]:
            cups_queue = printer["cups_name"]
        else:
            # fallback to name: ensure it's a queue that CUPS knows
            cups_queue = printer["name"]

        # build receipt text from DB
        with get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT o.id, o.total, o.created_at, t.name as table_name
                FROM orders o
                LEFT JOIN tables t ON o.table_id = t.id
                WHERE o.id=?
            """, (order_id,))
            order = cursor.fetchone()

            cursor.execute("""
                SELECT p.name, oi.quantity, oi.price
                FROM order_items oi
                JOIN products p ON oi.product_id = p.id
                WHERE oi.order_id=?
            """, (order_id,))
            items = cursor.fetchall()

        # Compose receipt
        table_name = order["table_name"] or "No Table"
        receipt_lines = []
        receipt_lines.append(f"*** {table_name} ***")
        receipt_lines.append(f"Order #{order_id}")
        receipt_lines.append(f"Date: {order['created_at']}")
        receipt_lines.append("-" * 32)
        for it in items:
            name = it["name"][:28]
            qty = it["quantity"]
            line_total = it["price"] * qty
            receipt_lines.append(f"{name:28} x{qty:<3} {line_total:7.2f} DA")
        receipt_lines.append("-" * 32)
        receipt_lines.append(f"TOTAL: {order['total']:.2f} DA")
        receipt_lines.append("")
        receipt_lines.append("*** THANK YOU ***")
        receipt_text = "\n".join(receipt_lines) + "\n"

        # Print via CUPS
        try:
            cups_conn = cups.Connection()
            # Validate printer exists in CUPS
            available = cups_conn.getPrinters()
            if cups_queue not in available:
                # if not found, try to match by substring (friendly fallback)
                found = None
                for q in available:
                    if cups_queue.lower() in q.lower() or printer.get("ip_address") and printer["ip_address"] in q:
                        found = q
                        break
                if found:
                    cups_queue = found
                else:
                    raise Exception(f"CUPS queue '{cups_queue}' not found. Available: {', '.join(available.keys())}")

            # write to tmp file and print
            with tempfile.NamedTemporaryFile(delete=False, suffix=".txt") as tmp:
                tmp.write(receipt_text.encode("utf-8"))
                tmp.flush()
                tmp_path = tmp.name

            # send to CUPS
            cups_conn.printFile(cups_queue, tmp_path, f"Order-{order_id}", {})
            print(f"✅ Sent receipt to printer queue: {cups_queue}")
        finally:
            # cleanup tmp file if exists
            try:
                if tmp_path and os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    # -----------------------
    # Styling
    # -----------------------
    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background: #f6f7fb;
            }
            #topbar {
                background: #ffffff;
                border-radius: 8px;
                padding: 6px;
            }
            QFrame#card, QFrame#prod_card {
                background: white;
                border-radius: 10px;
                border: 1px solid #e6e9ef;
            }
            QFrame#prod_card:hover {
                border: 1px solid #98c1ff;
            }
            QPushButton {
                background: #2f80ed;
                color: white;
                border-radius: 8px;
                padding: 6px 10px;
            }
            QPushButton:checked {
            background-color: #27ae60;
            color: white;
            }

            QPushButton[flat="true"] {
                background: transparent;
                color: #333;
            }
            QPushButton:hover {
                background: #1366d6;
            }
            QTableWidget {
                background: #fff;
                border-radius: 8px;
            }
            QLabel {
                color: #222;
            }
        """)


# quick test runner
if __name__ == "__main__":
    app = QApplication(sys.argv)
    w = POSWindow("cashier")
    w.show()
    sys.exit(app.exec())
