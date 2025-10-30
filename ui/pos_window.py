from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QFrame,
    QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QTableWidget, QTableWidgetItem, QSizePolicy
)
from PyQt6.QtCore import Qt
import sys


class POSWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FastFood POS System")
        self.setGeometry(100, 100, 1200, 700)

        # Central Widget
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)

        # ---------- Main Layout ----------
        self.main_layout = QVBoxLayout(self.central_widget)

        # ---------- TOP BAR ----------
        self.top_bar = QFrame()
        self.top_bar.setFrameShape(QFrame.Shape.StyledPanel)
        self.top_layout = QHBoxLayout(self.top_bar)

        self.btn_toggle_tables = QPushButton("🪑 Tables View")
        self.lbl_selected_table = QLabel("Selected: None")
        self.lbl_selected_table.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_logout = QPushButton("Logout")

        self.top_layout.addWidget(self.btn_toggle_tables)
        self.top_layout.addWidget(self.lbl_selected_table)
        self.top_layout.addStretch()
        self.top_layout.addWidget(self.btn_logout)

        self.main_layout.addWidget(self.top_bar)

        # ---------- MAIN AREA (3 panels) ----------
        self.main_area = QFrame()
        self.main_area_layout = QHBoxLayout(self.main_area)

        # ===== Left Panel (Categories) =====
        self.frame_categories = QFrame()
        self.frame_categories.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout_categories = QVBoxLayout(self.frame_categories)

        # Add scroll area for categories
        self.scroll_categories = QScrollArea()
        self.scroll_categories.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_content.setLayout(self.scroll_layout)
        self.scroll_categories.setWidget(self.scroll_content)

        self.layout_categories.addWidget(self.scroll_categories)

        # ===== Middle Panel (Products) =====
        self.frame_products = QFrame()
        self.frame_products.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout_products = QVBoxLayout(self.frame_products)
        self.layout_products.setAlignment(Qt.AlignmentFlag.AlignTop)

        # Example label for now
        self.layout_products.addWidget(QLabel("Products will appear here"))

        # ===== Right Panel (Cart) =====
        self.frame_cart = QFrame()
        self.frame_cart.setFrameShape(QFrame.Shape.StyledPanel)
        self.layout_cart = QVBoxLayout(self.frame_cart)

        self.table_cart = QTableWidget(0, 3)
        self.table_cart.setHorizontalHeaderLabels(["Item", "Qty", "Price"])
        self.layout_cart.addWidget(self.table_cart)

        self.lbl_total = QLabel("Total: 0 DA")
        self.lbl_total.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.layout_cart.addWidget(self.lbl_total)

        # Buttons area
        self.btns_frame = QFrame()
        self.btns_layout = QHBoxLayout(self.btns_frame)
        self.btn_print = QPushButton("🖨️ Print")
        self.btn_execute = QPushButton("✅ Execute")
        self.btns_layout.addWidget(self.btn_print)
        self.btns_layout.addWidget(self.btn_execute)

        self.layout_cart.addWidget(self.btns_frame)

        # Add frames to main layout
        self.main_area_layout.addWidget(self.frame_categories, 1)
        self.main_area_layout.addWidget(self.frame_products, 2)
        self.main_area_layout.addWidget(self.frame_cart, 1)

        self.main_layout.addWidget(self.main_area)

        # Adjust size policies
        self.frame_products.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        # ---------- STYLE ----------
        self.apply_style()

    def apply_style(self):
        self.setStyleSheet("""
            QFrame {
                background-color: #f8f8f8;
            }
            QPushButton {
                font-size: 14px;
                padding: 8px 14px;
            }
            QLabel {
                font-size: 14px;
            }
            QTableWidget {
                background-color: white;
            }
            #frame_categories {
                background-color: #eeeeee;
            }
            #frame_cart {
                background-color: #fff8dc;
            }
        """)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = POSWindow()
    window.show()
    sys.exit(app.exec())
