import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QStackedWidget, QFrame, QSizePolicy,
    QTableWidget, QTableWidgetItem, QDialog, QFormLayout,
    QComboBox, QDoubleSpinBox, QLineEdit, QMessageBox
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

# ----------------------------- Product Form Dialog -----------------------------
class ProductForm(QDialog):
    def __init__(self, parent=None, product=None):
        super().__init__(parent)
        self.setWindowTitle("Add / Edit Product")
        self.setFixedWidth(300)
        layout = QFormLayout(self)

        self.name_input = QLineEdit()
        self.category_combo = QComboBox()
        self.price_input = QDoubleSpinBox()
        self.price_input.setMaximum(100000)
        self.price_input.setDecimals(2)

        # Load categories
        categories = Category.all()
        for cat in categories:
            self.category_combo.addItem(cat["name"], cat["id"])

        self.product = product
        if product:
            self.name_input.setText(product["name"])
            self.price_input.setValue(product["price"])
            idx = self.category_combo.findData(product["category_id"])
            if idx >= 0:
                self.category_combo.setCurrentIndex(idx)

        layout.addRow("Name:", self.name_input)
        layout.addRow("Category:", self.category_combo)
        layout.addRow("Price (DA):", self.price_input)

        self.save_btn = QPushButton("Save")
        self.save_btn.clicked.connect(self.accept)
        layout.addWidget(self.save_btn)

    def get_data(self):
        return {
            "name": self.name_input.text(),
            "category_id": self.category_combo.currentData(),
            "price": self.price_input.value(),
        }


# ----------------------------- Main Admin Dashboard -----------------------------
class AdminDashboard(QMainWindow):
    def __init__(self,user=None):
        super().__init__()
        self.user = user or {"username": "Admin", "role": "Manager"}
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
        self.btn_printers = QPushButton("🖨️ Printers")
        self.btn_users = QPushButton("👥 Users")
        self.btn_settings = QPushButton("⚙️ Settings")

        for btn in [self.btn_dashboard,self.btn_printers, self.btn_products,self.btn_orders,self.btn_categories, self.btn_tables, self.btn_users, self.btn_settings]:
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
        self.page_tables = self.create_page("Tables Management")
        self.page_users = self.create_page("Users Management")
        self.page_settings = self.create_page("Settings")
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



        # ---------- STYLE ----------
        self.apply_style()

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
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Category", "Price", "Actions"])
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table)

        self.load_products()
        return page

    def load_products(self):
        self.table.setRowCount(0)
        products = Product.all()
        for row_index, product in enumerate(products):
            self.table.insertRow(row_index)
            self.table.setItem(row_index, 0, QTableWidgetItem(str(product["id"])))
            self.table.setItem(row_index, 1, QTableWidgetItem(product["name"]))
            self.table.setItem(row_index, 2, QTableWidgetItem(product.get("category_name", "")))
            self.table.setItem(row_index, 3, QTableWidgetItem(f"{product['price']:.2f}"))

            edit_btn = QPushButton("✏️ Edit")
            edit_btn.clicked.connect(lambda _, p=product: self.edit_product(p))
            del_btn = QPushButton("🗑️ Delete")
            del_btn.clicked.connect(lambda _, p=product: self.delete_product(p["id"]))

            action_layout = QHBoxLayout()
            action_layout.addWidget(edit_btn)
            action_layout.addWidget(del_btn)
            action_layout.setContentsMargins(0, 0, 0, 0)

            action_widget = QWidget()
            action_widget.setLayout(action_layout)
            self.table.setCellWidget(row_index, 4, action_widget)

    def add_product(self):
        dialog = ProductForm(self)
        if dialog.exec():
            data = dialog.get_data()
            Product.create(data["name"], data["category_id"], data["price"])
            self.load_products()

    def edit_product(self, product):
        dialog = ProductForm(self, product)
        if dialog.exec():
            data = dialog.get_data()
            Product.update(product["id"], data["name"], data["category_id"], data["price"], product["status"])
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
                background-color: #f5f6fa;
            }
            #sidebar {
                background-color: #2f3640;
                color: white;
            }
            QPushButton {
                color: white;
                background: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: #353b48;
            }
            #topbar {
                background-color: white;
                border-bottom: 1px solid #ddd;
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
        self.table_orders.setColumnCount(6)
        self.table_orders.setHorizontalHeaderLabels(["ID", "Table", "User", "Total (DA)", "Payment Type", "Date"])
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
            self.table_orders.setItem(i, 1, QTableWidgetItem(order.get("table_name", "")))
            self.table_orders.setItem(i, 2, QTableWidgetItem(order.get("user_name", "")))
            self.table_orders.setItem(i, 3, QTableWidgetItem(f"{order['total']:.2f}"))
            self.table_orders.setItem(i, 4, QTableWidgetItem(order["payment_type"]))
            self.table_orders.setItem(i, 5, QTableWidgetItem(order["created_at"]))

    def filter_orders(self):
        # Future version: show QDialog with date pickers + payment type
        QMessageBox.information(self, "Coming Soon", "Filter functionality coming soon!")

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
        self.table_printers.setColumnCount(4)
        self.table_printers.setHorizontalHeaderLabels(["ID", "Name", "IP", "Category"])
        self.table_printers.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_printers.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table_printers.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table_printers)

        # --- Connections
        btn_scan.clicked.connect(self.scan_printers)
        btn_add.clicked.connect(self.add_printer)
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
        """Load printers from database"""
        self.table_printers.setRowCount(0)
        printers = PrinterController.get_all()
        for row, p in enumerate(printers):
            self.table_printers.insertRow(row)
            self.table_printers.setItem(row, 0, QTableWidgetItem(str(p["id"])))
            self.table_printers.setItem(row, 1, QTableWidgetItem(p["name"]))
            self.table_printers.setItem(row, 2, QTableWidgetItem(p.get("ip", "")))
            self.table_printers.setItem(row, 3, QTableWidgetItem(p.get("category", "")))
    
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
        """Scan printers and let user select which to add"""
        printers = PrinterController.detect_system_printers() or PrinterController.detect_printers()
        if not printers:
            QMessageBox.information(self, "Scan Complete", "No printers found.")
            return

        # Get already added printers from DB
        existing = [p["name"] for p in Printer.all()]

        dialog = QDialog(self)
        dialog.setWindowTitle("Detected Printers")
        layout = QVBoxLayout(dialog)

        lbl = QLabel("Select printers to add:")
        layout.addWidget(lbl)

        checkboxes = []
        for p in printers:
            name = p["name"] if isinstance(p, dict) else p
            chk = QCheckBox(name)
            if name in existing:
                chk.setDisabled(True)
                chk.setText(f"{name} (already added)")
            layout.addWidget(chk)
            checkboxes.append(chk)

        btn_add = QPushButton("Add Selected")
        btn_add.setStyleSheet("background: #0984e3; color: white; padding: 5px 10px; border-radius: 5px;")
        layout.addWidget(btn_add)

        def add_selected():
            selected = [chk.text().replace(" (already added)", "") for chk in checkboxes if chk.isChecked()]
            if not selected:
                QMessageBox.warning(dialog, "No Selection", "Please select at least one printer.")
                return

            added_count = 0
            for name in selected:
                # Double-check again to avoid duplicates
                if any(p["name"] == name for p in Printer.all()):
                    continue
                Printer.create(
                    name=name,
                    type="thermal",
                    connection="local",
                    ip_address=None,
                    port=None,
                    categories=["Unassigned"],
                    status="online"
                )
                added_count += 1

            QMessageBox.information(dialog, "Success", f"Added {added_count} new printer(s).")
            dialog.accept()
            self.load_printers()

        btn_add.clicked.connect(add_selected)
        dialog.exec()


    def add_printer(self):
        """Add printer manually"""
        name, ok1 = QInputDialog.getText(self, "Add Printer", "Enter printer name:")
        if not ok1 or not name:
            return

        ip, ok2 = QInputDialog.getText(self, "Add Printer", "Enter IP (optional):")
        if not ok2:
            return

        category, ok3 = QInputDialog.getText(self, "Add Printer", "Enter category (optional):")
        if not ok3:
            return

        PrinterController.add_manual(name, ip, category, self)
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





if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec())
