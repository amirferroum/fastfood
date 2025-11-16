import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QComboBox, QDoubleSpinBox, QLineEdit, QMessageBox,QScrollArea
)
from PyQt6.QtCore import Qt

from models.product import Product
from models.category import Category
from controllers.category_controller import CategoryController
from models.database import init_db
from PyQt6.QtWidgets import QInputDialog, QMessageBox, QTableWidget, QTableWidgetItem
from controllers.order_controller import OrderController
from PyQt6.QtWidgets import QFileDialog
import csv
from controllers.printer_controller import PrinterController
from models.printer import Printer
from PyQt6.QtWidgets import QDialog, QVBoxLayout, QCheckBox, QPushButton, QLabel
from models.category import Category
from ui.reports_window import ReportsPage  # adjust path if needed
from ui.settings_window import SettingsPage
from ui.users_window import UsersPage
from ui.filter_dialog import FilterDialog
from PyQt6.QtWidgets import QMessageBox
from utils.config_manager import save_config
from ui.login_window import LoginWindow
from ui.tables_page import TablesPage
from ui.inventory_window import InventoryPage
from models.category import Category
import usb.core
import usb.util


# ----------------------------- Product Form Dialog -----------------------------
class ProductForm(QDialog):
    def __init__(self, categories, product=None):
        super().__init__()
        self.setWindowTitle("Product Form")
        layout = QFormLayout(self)

        # Name
        self.name_input = QLineEdit()
        layout.addRow("Name:", self.name_input)

        # Category
        self.category_combo = QComboBox()
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])
        layout.addRow("Category:", self.category_combo)

        # Price
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setDecimals(2)
        layout.addRow("Price (DA):", self.price_input)

        # Cost
        self.cost_input = QDoubleSpinBox()
        self.cost_input.setMaximum(100000)
        self.cost_input.setDecimals(2)
        layout.addRow("Cost (DA):", self.cost_input)

        # Status
        self.status_combo = QComboBox()
        self.status_combo.addItems(["active", "inactive"])
        layout.addRow("Status:", self.status_combo)

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        layout.addRow(btn_layout)

        # Fill data if editing
        if product:
            self.name_input.setText(product["name"])
            self.category_combo.setCurrentIndex(self.category_combo.findData(product["category_id"]))
            self.price_input.setValue(product["price"])
            self.cost_input.setValue(product.get("cost", 0))
            self.status_combo.setCurrentText(product["status"])

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "category_id": self.category_combo.currentData(),
            "price": self.price_input.value(),
            "cost": self.cost_input.value(),
            "status": self.status_combo.currentText(),
        }



# ----------------------------- Main Admin Dashboard -----------------------------
class AdminDashboard(QMainWindow):
    def __init__(self, role, user=None):
        super().__init__()
        self.user = user or {"username": "Admin", "role": role.capitalize()}
        self.role = role

        self.setWindowTitle("FastFood Admin Dashboard")
        self.setWindowTitle("FastFood Admin Dashboard")
        self.setGeometry(150, 100, 1300, 750)

        # Central widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QHBoxLayout(self.central_widget)

        # ---------- LEFT SIDEBAR ----------
        self.sidebar = QFrame()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        self.sidebar_layout = QVBoxLayout(self.sidebar)
        self.sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        self.lbl_logo = QLabel("🍟 FastFood Admin")
        self.lbl_logo.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_logo.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 20px;")
        self.sidebar_layout.addWidget(self.lbl_logo)

        # Sidebar buttons
        self.btn_dashboard = QPushButton("🏠 Dashboard")
        self.btn_products = QPushButton("🍔 Products")
        self.btn_categories = QPushButton("📂 Categories")
        self.btn_orders = QPushButton("💰 Orders & Sales")
        self.btn_tables = QPushButton("🪑 Tables")
        self.btn_inventory = QPushButton(" Inventory")
        self.btn_printers = QPushButton("🖨️ Printers")
        self.btn_users = QPushButton("👥 Users")
        self.btn_settings = QPushButton("⚙️ Settings")
        # --- Sign Out button ---
        self.btn_logout = QPushButton("🚪 Sign Out")
        self.btn_logout.setStyleSheet("""
            QPushButton {
                background-color: #e84118;
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c23616;
            }
        """)
        self.btn_logout.clicked.connect(self.handle_logout)
        self.sidebar_layout.addWidget(self.btn_logout)


        for btn in [self.btn_dashboard,self.btn_inventory,self.btn_printers, self.btn_products,self.btn_orders,self.btn_categories, self.btn_tables, self.btn_users, self.btn_settings]:
            btn.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet("text-align: left; padding: 10px 15px; font-size: 14px;")
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()

        # ---------- MAIN AREA ----------
        self.main_area = QFrame()
        self.main_area_layout = QVBoxLayout(self.main_area)

        # Top bar
        self.top_bar = QFrame()
        self.top_bar.setObjectName("topbar")
        self.top_bar.setFixedHeight(60)
        self.top_layout = QHBoxLayout(self.top_bar)
        self.lbl_title = QLabel("Dashboard Overview")
        self.lbl_title.setStyleSheet("font-weight: bold; font-size: 18px;")
        self.lbl_user = QLabel(f"👤 {self.user['username']} ({self.user['role']})")
        self.lbl_user.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.top_layout.addWidget(self.lbl_title)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.lbl_user)

        # Stacked pages
        self.pages = QStackedWidget()
        self.page_dashboard = ReportsPage()
        self.page_products = self.create_products_page()
        self.page_categories = self.create_categories_page()
        self.page_tables = TablesPage()
        self.page_inventory = InventoryPage()


        self.page_users = UsersPage()
        self.page_settings = SettingsPage()
        self.page_orders = self.create_orders_page()
        self.page_printers = self.create_printers_page()


        self.pages.addWidget(self.page_dashboard)
        self.pages.addWidget(self.page_products)
        self.pages.addWidget(self.page_categories)
        self.pages.addWidget(self.page_tables)
        self.pages.addWidget(self.page_users)
        self.pages.addWidget(self.page_settings)
        self.pages.addWidget(self.page_orders)
        self.pages.addWidget(self.page_printers)
        self.pages.addWidget(self.page_inventory)



        # Add top bar and pages
        self.main_area_layout.addWidget(self.top_bar)
        self.main_area_layout.addWidget(self.pages)

        # Add to main layout
        self.main_layout.addWidget(self.sidebar)
        self.main_layout.addWidget(self.main_area)

        # ---------- CONNECTIONS ----------
        self.btn_dashboard.clicked.connect(lambda: self.switch_page(0, "Dashboard Overview"))
        self.btn_products.clicked.connect(lambda: self.switch_page(1, "Products Management"))
        self.btn_categories.clicked.connect(lambda: self.switch_page(2, "Categories Management"))
        self.btn_tables.clicked.connect(lambda: self.switch_page(3, "Tables Management"))
        self.btn_users.clicked.connect(lambda: self.switch_page(4, "Users Management"))
        self.btn_settings.clicked.connect(lambda: self.switch_page(5, "Settings"))
        self.btn_orders.clicked.connect(lambda: self.switch_page(6, "Orders & Sales"))
        self.btn_printers.clicked.connect(lambda: self.switch_page(7, "Printers Management"))
        self.btn_inventory.clicked.connect(lambda: self.switch_page(8, "Inventory Management"))


        

        # ---------- STYLE ----------
        self.apply_style()
        self.apply_role_permissions()


    # ------------------------- PAGE HANDLERS -------------------------
    def switch_page(self, index, title):
        self.pages.setCurrentIndex(index)
        self.lbl_title.setText(title)

    def create_page(self, title):
        page = QWidget()
        layout = QVBoxLayout(page)
        lbl = QLabel(title)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold;")
        layout.addWidget(lbl)
        return page

    

    # ------------------------- PRODUCTS PAGE -------------------------
    def create_products_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Header
        header_layout = QHBoxLayout()
        header_label = QLabel("🍔 Products Management")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_label)
        header_layout.addStretch()
        add_btn = QPushButton("➕ Add Product")
        add_btn.clicked.connect(self.add_product)
        header_layout.addWidget(add_btn)
        layout.addLayout(header_layout)

        # Table
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price", "Cost", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.load_products()
        return page

    def load_products(self):
        from models.product import Product
        products = Product.get_all()

        self.table.setRowCount(len(products))
        for row_index, product in enumerate(products):
            self.table.setItem(row_index, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(product["category_name"] if product["category_name"] else "—"))
            self.table.setItem(row_index, 3, QTableWidgetItem(f"{product['price']:.2f} DA"))
            self.table.setItem(row_index, 4, QTableWidgetItem(f"{product.get('cost', 0):.2f} DA"))

            # --- Styled Action Buttons ---
            edit_btn = QPushButton("✏️ Edit")
            delete_btn = QPushButton("🗑️ Delete")

            # Button Styling
            edit_btn.setStyleSheet("""
                QPushButton {
                    background-color: #28a745;
                    color: white;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #218838;
                }
            """)
            delete_btn.setStyleSheet("""
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border-radius: 8px;
                    padding: 4px 10px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
            """)

            edit_btn.clicked.connect(lambda _, pid=product["id"]: self.edit_product(pid))
            delete_btn.clicked.connect(lambda _, pid=product["id"]: self.delete_product(pid))

            # Layout
            action_layout = QHBoxLayout()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(delete_btn)
            action_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
            action_layout.setSpacing(8)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_index, 5, action_widget)



    def add_product(self):
        from models.category import Category
        categories = Category.all()
        dialog = ProductForm(categories)
        if dialog.exec():
            self.load_products()


    def edit_product(self, product_id):
        product = Product.get_by_id(product_id)   # ✅ get full product data
        categories = Category.all()
        dialog = ProductForm(categories, product)
        if dialog.exec():
            self.load_products()


    def delete_product(self, product_id):
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            "Are you sure you want to delete this product?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            Product.delete(product_id)
            self.load_products()

    # ------------------------- STYLE -------------------------
    def apply_style(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', sans-serif;
            }
            #sidebar {
                background-color: #1e272e;
                color: white;
                border-top-right-radius: 15px;
                border-bottom-right-radius: 15px;
            }
            QLabel#title {
                color: #2f3640;
                font-size: 20px;
                font-weight: 600;
            }
            QPushButton {
                color: #dcdde1;
                background: transparent;
                border: none;
                padding: 10px 15px;
                text-align: left;
                font-size: 15px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #485460;
                color: #ffffff;
            }
            QPushButton:pressed {
                background-color: #808e9b;
            }
            #topbar {
                background-color: white;
                border-bottom: 1px solid #ddd;
                border-radius: 10px;
            }
            QTableWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                gridline-color: #f1f2f6;
                selection-background-color: #ff9f43;
                selection-color: white;
                font-size: 14px;
            }
            QHeaderView::section {
                background-color: #2f3640;
                color: white;
                padding: 6px;
                border: none;
                font-weight: bold;
            }
            QPushButton#action {
                background-color: #ff9f43;
                color: white;
                border-radius: 6px;
                padding: 6px 12px;
            }
            QPushButton#action:hover {
                background-color: #e67e22;
            }
            QMessageBox {
                background-color: #fff;
            }
        """)


    def create_categories_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        lbl = QLabel("Categories Management")
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lbl.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(lbl)

        # Buttons
        buttons_layout = QHBoxLayout()
        self.btn_add_cat = QPushButton("➕ Add Category")
        self.btn_edit_cat = QPushButton("✏️ Edit Selected")
        self.btn_delete_cat = QPushButton("🗑️ Delete Selected")

        for btn in [self.btn_add_cat, self.btn_edit_cat, self.btn_delete_cat]:
            btn.setStyleSheet("padding: 6px 12px; background: #0984e3; color: white; border-radius: 5px;")
            buttons_layout.addWidget(btn)
        layout.addLayout(buttons_layout)

        # Table
        self.table_categories = QTableWidget()
        self.table_categories.setColumnCount(2)
        self.table_categories.setHorizontalHeaderLabels(["ID", "Category Name"])
        self.table_categories.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_categories)

        self.load_categories()

        # Connect buttons
        self.btn_add_cat.clicked.connect(self.add_category)
        self.btn_edit_cat.clicked.connect(self.edit_category)
        self.btn_delete_cat.clicked.connect(self.delete_category)

        return page


    def load_categories(self):
        categories = CategoryController.get_all()
        self.table_categories.setRowCount(len(categories))
        for row, cat in enumerate(categories):
            self.table_categories.setItem(row, 0, QTableWidgetItem(str(cat["id"])))
            self.table_categories.setItem(row, 1, QTableWidgetItem(cat["name"]))



    def add_category(self):
        name, ok = QInputDialog.getText(self, "Add Category", "Enter category name:")
        if ok and name:
            try:
                CategoryController.add(name)
                self.load_categories()
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Could not add category:\n{e}")


    def edit_category(self):
        selected = self.table_categories.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Select Category", "Please select a category to edit.")
            return

        id_ = int(self.table_categories.item(selected, 0).text())
        current_name = self.table_categories.item(selected, 1).text()
        new_name, ok = QInputDialog.getText(self, "Edit Category", "Edit category name:", text=current_name)
        if ok and new_name:
            CategoryController.update(id_, new_name)
            self.load_categories()


    def delete_category(self):
        selected = self.table_categories.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "Select Category", "Please select a category to delete.")
            return

        id_ = int(self.table_categories.item(selected, 0).text())
        name = self.table_categories.item(selected, 1).text()
        confirm = QMessageBox.question(
            self,
            "Delete Category",
            f"Are you sure you want to delete '{name}'?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )

        if confirm == QMessageBox.StandardButton.Yes:
            CategoryController.delete(id_)
            self.load_categories()


    def create_orders_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        # Header
        header_layout = QHBoxLayout()
        lbl = QLabel("💰 Orders & Sales")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()

        self.btn_filter = QPushButton("🔍 Filter")
        self.btn_export = QPushButton("📤 Export to CSV")
        header_layout.addWidget(self.btn_filter)
        header_layout.addWidget(self.btn_export)
        layout.addLayout(header_layout)

        # Table
        self.table_orders = QTableWidget()
        self.table_orders.setColumnCount(7)
        self.table_orders.setHorizontalHeaderLabels(["ID", "Table", "User", "Total (DA)", "Payment Type", "Date", "Actions"])

        self.table_orders.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_orders)

        self.load_orders()

        # Connect buttons
        self.btn_filter.clicked.connect(self.filter_orders)
        self.btn_export.clicked.connect(self.export_orders)

        return page

    def load_orders(self):
        orders = OrderController.get_all_orders()
        self.table_orders.setRowCount(len(orders))

        for i, order in enumerate(orders):
            self.table_orders.setItem(i, 0, QTableWidgetItem(str(order["id"])))
            self.table_orders.setItem(i, 1, QTableWidgetItem(str(order["table_number"]) if "table_number" in order.keys() else ""))
            self.table_orders.setItem(i, 2, QTableWidgetItem(str(order["user_name"]) if "user_name" in order.keys() else ""))
            self.table_orders.setItem(i, 3, QTableWidgetItem(f"{order['total']:.2f}" if order["total"] else "0.00"))
            self.table_orders.setItem(i, 4, QTableWidgetItem(order["payment_type"] if "payment_type" in order.keys() else ""))
            self.table_orders.setItem(i, 5, QTableWidgetItem(order["status"] if "status" in order.keys() else ""))


            # --- Add buttons: Reprint | Refund | Details ---
            btn_reprint = QPushButton("🖨 Reprint")
            btn_refund = QPushButton("💸 Refund")
            btn_details = QPushButton("📋 Details")

            btn_reprint.setStyleSheet("background:#0984e3; color:white; border-radius:5px; padding:4px;")
            btn_refund.setStyleSheet("background:#e84118; color:white; border-radius:5px; padding:4px;")
            btn_details.setStyleSheet("background:#00b894; color:white; border-radius:5px; padding:4px;")

            btn_reprint.clicked.connect(lambda _, o=order: self.reprint_order(o))
            btn_refund.clicked.connect(lambda _, o=order: self.refund_order(o))
            btn_details.clicked.connect(lambda _, o=order: self.show_order_details(o))

            action_layout = QHBoxLayout()
            action_layout.addWidget(btn_reprint)
            action_layout.addWidget(btn_refund)
            action_layout.addWidget(btn_details)
            action_layout.setContentsMargins(0, 0, 0, 0)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.table_orders.setCellWidget(i, 6, action_widget)


    def filter_orders(self):
        dialog = FilterDialog(self)
        if not dialog.exec():
            return

        filters = dialog.get_filters()
        orders = OrderController.get_all_orders()

        filtered = []
        for order in orders:
            date = order["created_at"].split(" ")[0]
            if not (filters["start"] <= date <= filters["end"]):
                continue
            if filters["payment_type"] != "All" and order["payment_type"] != filters["payment_type"]:
                continue
            filtered.append(order)

        self.table_orders.setRowCount(len(filtered))
        for i, order in enumerate(filtered):
            self.table_orders.setItem(i, 0, QTableWidgetItem(str(order["id"])))
            self.table_orders.setItem(i, 1, QTableWidgetItem(order.get("table_name", "")))
            self.table_orders.setItem(i, 2, QTableWidgetItem(order.get("user_name", "")))
            self.table_orders.setItem(i, 3, QTableWidgetItem(f"{order['total']:.2f}"))
            self.table_orders.setItem(i, 4, QTableWidgetItem(order["payment_type"]))
            self.table_orders.setItem(i, 5, QTableWidgetItem(order["created_at"]))


    def export_orders(self):
        path, _ = QFileDialog.getSaveFileName(self, "Export Orders", "", "CSV Files (*.csv)")
        if not path:
            return
        orders = OrderController.get_all()
        with open(path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Table", "User", "Total (DA)", "Payment Type", "Date"])
            for o in orders:
                writer.writerow([o["id"], o["table_name"], o["user_name"], o["total"], o["payment_type"], o["created_at"]])
        QMessageBox.information(self, "Export Complete", f"Orders exported to:\n{path}")


    def reprint_order(self, order):
        printer_name = PrinterController.get_default_printer_name()
        if not printer_name:
            QMessageBox.warning(self, "No Printer", "No default printer configured.")
            return
        PrinterController.print_order(order)
        QMessageBox.information(self, "Reprinted", f"Order #{order['id']} sent to printer.")

    def refund_order(self, order):
        confirm = QMessageBox.question(
            self, "Confirm Refund",
            f"Refund order #{order['id']} of {order['total']} DA?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            OrderController.refund(order["id"])
            QMessageBox.information(self, "Refunded", f"Order #{order['id']} refunded successfully.")
            self.load_orders()

    def show_order_details(self, order):
        details = OrderController.get_order_items(order["id"])
        msg = f"🧾 Order #{order['id']}\n\n"
        for item in details:
            msg += f"{item['quantity']}x {item['product_name']} — {item['price']:.2f} DA\n"
        msg += f"\nTotal: {order['total']:.2f} DA"
        QMessageBox.information(self, "Order Details", msg)

        # ------------------------- PRINTERS PAGE -------------------------
        # ------------------------- PRINTERS PAGE -------------------------
    def create_printers_page(self):
        page = QWidget()
        layout = QVBoxLayout(page)

        header_layout = QHBoxLayout()
        lbl = QLabel("🖨️ Printers Management")
        lbl.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(lbl)
        header_layout.addStretch()

        btn_scan = QPushButton("🔍 Scan Printers")
        btn_add = QPushButton("➕ Add Printer")
        btn_delete = QPushButton("🗑 Delete Printer")
        btn_assign = QPushButton("🔧 Assign Category")
        btn_test = QPushButton("🧾 Test Print")
        btn_refresh = QPushButton("🔄 Refresh")
        assign_btn = QPushButton("Assign Category")
        remove_btn = QPushButton("Remove Category")

        for btn in [btn_scan,assign_btn,remove_btn, btn_add, btn_assign, btn_delete, btn_test,btn_refresh]:
            btn.setStyleSheet(
                "padding: 6px 12px; background: #0984e3; color: white; border-radius: 5px;"
            )
            header_layout.addWidget(btn)

        layout.addLayout(header_layout)

        # --- Table
        self.table_printers = QTableWidget()
        self.table_printers.setColumnCount(6)
        self.table_printers.setHorizontalHeaderLabels(["ID", "Name", "Connection", "IP", "Categories", "Status"])
        self.table_printers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_printers.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_printers.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_printers)

        # --- Connections
        btn_scan.clicked.connect(self.scan_printers)
        btn_add.clicked.connect(self.open_add_printer_dialog)
        btn_assign.clicked.connect(self.assign_printer_category)
        btn_delete.clicked.connect(self.delete_printer)
        btn_test.clicked.connect(self.test_print)
        btn_refresh.clicked.connect(self.refresh_printers)
        assign_btn.clicked.connect(self.assign_printer_category)
        remove_btn.clicked.connect(self.remove_printer_category)



        # --- Initial load
        self.load_printers()

        return page
    
    def refresh_printers(self):
        self.load_printers()
        QMessageBox.information(self, "Refreshed", "Printer list updated.")

    def load_printers(self):
        # Clear old rows
        self.table_printers.setRowCount(0)

        printers = PrinterController.get_all()
        if not printers:
            return

        # Ensure table has the right number of rows
        self.table_printers.setRowCount(len(printers))

        for row, p in enumerate(printers):
            self.table_printers.setItem(row, 0, QTableWidgetItem(str(p.get("id", ""))))
            self.table_printers.setItem(row, 1, QTableWidgetItem(p.get("name", "")))
            self.table_printers.setItem(row, 2, QTableWidgetItem(p.get("connection", "")))
            self.table_printers.setItem(row, 3, QTableWidgetItem(str(p.get("ip", ""))))
            self.table_printers.setItem(row, 4, QTableWidgetItem(str(p.get("categories", ""))))
            self.table_printers.setItem(row, 5, QTableWidgetItem(p.get("status", "")))

        self.table_printers.resizeColumnsToContents()


    
    def remove_printer_category(self):
        selected_items = self.table_printers.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Error", "Select a printer first")
            return

        printer_id = int(selected_items[0].text())
        category, ok = QInputDialog.getText(self, "Remove Category", "Category name to remove:")
        if not ok or not category:
            return

        Printer.remove_category(printer_id, category)
        QMessageBox.information(self, "Success", "Category removed successfully")
        self.load_printers()


    def scan_printers(self):
        """Scan USB printers (PyUSB) and allow the user to add them."""
        printers = PrinterController.detect_usb_printers()

        if not printers:
            QMessageBox.information(self, "Scan Complete", "No USB printers found.")
            return

        existing = [p["name"] for p in Printer.all()]

        dialog = QDialog(self)
        dialog.setWindowTitle("Detected USB Printers")
        dialog.resize(500, 400)

        layout = QVBoxLayout(dialog)
        layout.addWidget(QLabel("Select USB printers to add:"))

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_content = QWidget()
        scroll_layout = QVBoxLayout(scroll_content)

        checkboxes = []
        for p in printers:
            name = p.get("name", "Unknown")
            vid = p.get("vendor_id", "N/A")
            pid = p.get("product_id", "N/A")
            serial = p.get("serial_number", "N/A")

            info = (
                f"🖨️ <b>{name}</b><br>"
                f"<small>Vendor ID: {vid}<br>"
                f"Product ID: {pid}<br>"
                f"Serial: {serial}</small>"
            )

            chk = QCheckBox()
            lbl_info = QLabel(info)
            lbl_info.setTextFormat(Qt.TextFormat.RichText)

            row = QWidget()
            row_layout = QHBoxLayout(row)
            row_layout.addWidget(chk)
            row_layout.addWidget(lbl_info)
            row_layout.addStretch()

            if name in existing:
                chk.setDisabled(True)
                lbl_info.setText(f"🖨️ <b>{name}</b> <small>(already added)</small>")

            scroll_layout.addWidget(row)
            checkboxes.append((chk, p))

        scroll_area.setWidget(scroll_content)
        layout.addWidget(scroll_area)

        btn_add = QPushButton("Add Selected")
        layout.addWidget(btn_add)

        def add_selected():
            selected = [(chk, p) for chk, p in checkboxes if chk.isChecked()]
            if not selected:
                QMessageBox.warning(dialog, "No Selection", "Please select at least one printer.")
                return

            added_count = 0
            for chk, printer in selected:
                name = printer.get("name", "")
                if any(p["name"] == name for p in Printer.all()):
                    continue

                Printer.create(
                    name=name,
                    connection_type="usb",
                    vendor_id=printer.get("vendor_id"),
                    product_id=printer.get("product_id"),
                    serial_number=printer.get("serial_number"),
                    assigned_categories="[]",
                    status="online"
                )
                added_count += 1

            QMessageBox.information(dialog, "Success", f"Added {added_count} printer(s).")
            dialog.accept()
            self.load_printers()

        btn_add.clicked.connect(add_selected)
        dialog.exec()




    def open_add_printer_dialog(self):
        from PyQt6.QtWidgets import QDialog, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox, QHBoxLayout

        dialog = QDialog(self)
        dialog.setWindowTitle("Add Printer")

        layout = QVBoxLayout(dialog)

        # Printer Name
        self.printer_name = QLineEdit()
        layout.addWidget(QLabel("Printer Name:"))
        layout.addWidget(self.printer_name)

        # Connection Type
        self.connection_type = QComboBox()
        self.connection_type.addItems(["manual", "usb", "network"])
        layout.addWidget(QLabel("Connection Type:"))
        layout.addWidget(self.connection_type)

        # USB Vendor/Product ID
        self.vendor_input = QLineEdit()
        self.product_input = QLineEdit()

        # Network IP/PORT
        self.ip_input = QLineEdit()
        self.port_input = QLineEdit()
        self.port_input.setText("9100")

        # Categories
        self.categories_input = QLineEdit()
        layout.addWidget(QLabel("Categories (comma separated):"))
        layout.addWidget(self.categories_input)

        # Dynamic field zone
        self.dynamic_zone = QVBoxLayout()
        layout.addLayout(self.dynamic_zone)

        def update_fields():
            for i in reversed(range(self.dynamic_zone.count())):
                widget = self.dynamic_zone.itemAt(i).widget()
                if widget:
                    widget.deleteLater()

            c = self.connection_type.currentText()

            if c == "usb":
                self.dynamic_zone.addWidget(QLabel("Vendor ID (hex):"))
                self.dynamic_zone.addWidget(self.vendor_input)
                self.dynamic_zone.addWidget(QLabel("Product ID (hex):"))
                self.dynamic_zone.addWidget(self.product_input)

            elif c == "network":
                self.dynamic_zone.addWidget(QLabel("IP Address:"))
                self.dynamic_zone.addWidget(self.ip_input)
                self.dynamic_zone.addWidget(QLabel("Port:"))
                self.dynamic_zone.addWidget(self.port_input)

            # manual requires no extra fields.

        self.connection_type.currentTextChanged.connect(update_fields)
        update_fields()

        # Buttons
        button_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

        # Save event
        def save_printer():
            from controllers.printer_controller import PrinterController

            name = self.printer_name.text().strip()
            conn_type = self.connection_type.currentText()
            categories = self.categories_input.text().strip()

            vendor = product = serial = ip = port = None

            if conn_type == "usb":
                vendor = self.vendor_input.text().strip()
                product = self.product_input.text().strip()

            elif conn_type == "network":
                ip = self.ip_input.text().strip()
                port = int(self.port_input.text().strip())

            PrinterController.add_printer(
                name=name,
                connection_type=conn_type,
                vendor_id=vendor,
                product_id=product,
                ip=ip,
                port=port,
                categories=categories,
                parent=self
            )
            dialog.close()
            self.load_printers_table()

        save_btn.clicked.connect(save_printer)
        cancel_btn.clicked.connect(dialog.close)

        dialog.exec()
                            


    def add_printer(self):
        name = self.name_input.text().strip()
        connection = self.connection_type_combo.currentText().lower()  # usb, network, manual
        ip = self.ip_input.text().strip() or None
        categories = self.category_input.text().strip()  # comma separated

        if not name:
            QMessageBox.warning(self, "Error", "Printer name is required")
            return

        # Determine printer type based on connection
        printer_type = connection if connection in ("usb", "network") else "manual"


        Printer.create(
            name=name,
            type=printer_type,          # type now matches the allowed values in DB
            connection=connection,      # keep connection info as descriptive
            ip_address=ip,
            port=None,
            categories=[c.strip() for c in categories.split(",") if c.strip()],
            status="online"
        )

        QMessageBox.information(self, "Success", f"Printer '{name}' added successfully")
        self.load_printers()



    def assign_printer_category(self):
        """Assign existing category from DB to selected printer"""
        selected = self.table_printers.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a printer.")
            return

        printer_id = int(self.table_printers.item(selected, 0).text())
        printer_name = self.table_printers.item(selected, 1).text()

        # Load all categories from DB
        categories = Category.all()
        if not categories:
            QMessageBox.warning(self, "No Categories", "Please add at least one category first.")
            return

        # Build a dropdown selection dialog
        category_names = [cat["name"] for cat in categories]
        category, ok = QInputDialog.getItem(
            self,
            "Assign Category",
            f"Select category for {printer_name}:",
            category_names,
            editable=False
        )

        if ok and category:
            Printer.assign_category(printer_id, category)
            QMessageBox.information(self, "Assigned", f"{printer_name} assigned to {category}.")
            self.load_printers()


    def delete_printer(self):
        """Delete selected printer"""
        selected = self.table_printers.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a printer to delete.")
            return

        printer_id = int(self.table_printers.item(selected, 0).text())
        PrinterController.delete_printer(printer_id, self)
        self.load_printers()

    def test_print(self):
        """Send a test print to the selected printer"""
        selected = self.table_printers.currentRow()
        if selected < 0:
            QMessageBox.warning(self, "No Selection", "Please select a printer to test.")
            return

        printer_name = self.table_printers.item(selected, 1).text()
        PrinterController.print_test(printer_name, self)
    
    def apply_role_permissions(self):
        """Hide or disable certain pages based on user role."""
        if self.role == "cashier":
            # Cashier can only see Orders and Products
            self.btn_users.setVisible(False)
            self.btn_settings.setVisible(False)
            self.btn_printers.setVisible(False)
            self.btn_categories.setVisible(False)
            self.btn_tables.setVisible(False)

        elif self.role == "kitchen":
            # Kitchen only sees Orders
            self.btn_dashboard.setVisible(False)
            self.btn_products.setVisible(False)
            self.btn_categories.setVisible(False)
            self.btn_tables.setVisible(False)
            self.btn_printers.setVisible(False)
            self.btn_users.setVisible(False)
            self.btn_settings.setVisible(False)

        elif self.role == "manager":
            # Manager can view reports and orders but not users/settings
            self.btn_users.setVisible(False)
            self.btn_settings.setVisible(False)

        elif self.role == "admin":
            # Full access
            pass


    def handle_logout(self):
        reply = QMessageBox.question(
            self,
            "Confirm Logout",
            "Are you sure you want to sign out?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            # Clear saved login info
            save_config({})
            self.close()

            # Show login window again
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()



if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec())
