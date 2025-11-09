from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QDateEdit, QComboBox,
    QPushButton, QLabel, QFrame
)
from PyQt6.QtCore import QDate, Qt
from PyQt6.QtGui import QFont

class FilterDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("🔎 Filter Orders")
        self.setFixedWidth(360)
        self.setStyleSheet("""
            QDialog {
                background-color: #f5f6fa;
                font-family: 'Segoe UI';
            }
            QLabel {
                font-size: 13px;
                color: #2f3640;
                font-weight: bold;
            }
            QDateEdit, QComboBox {
                border: 1px solid #dcdde1;
                border-radius: 6px;
                padding: 6px;
                font-size: 13px;
                background-color: white;
            }
            QDateEdit:hover, QComboBox:hover {
                border: 1px solid #4cd137;
            }
            QPushButton {
                background-color: #44bd32;
                color: white;
                border-radius: 8px;
                padding: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4cd137;
            }
            QFrame {
                background-color: white;
                border: 1px solid #dcdde1;
                border-radius: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # --- Title ---
        title = QLabel("Filter Orders")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # --- Frame container ---
        frame = QFrame()
        form_layout = QFormLayout(frame)
        form_layout.setContentsMargins(25, 20, 25, 20)
        form_layout.setSpacing(14)

        # Date range
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate().addDays(-7))  # default: last week

        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        # Payment type dropdown
        self.payment_combo = QComboBox()
        self.payment_combo.addItem("All")
        self.payment_combo.addItems(["Cash", "Card", "Other"])

        form_layout.addRow("📅 Start Date:", self.start_date)
        form_layout.addRow("📆 End Date:", self.end_date)
        form_layout.addRow("💳 Payment Type:", self.payment_combo)

        layout.addWidget(frame)

        # --- Apply Button ---
        self.btn_apply = QPushButton("✅ Apply Filter")
        layout.addWidget(self.btn_apply)

        self.btn_apply.clicked.connect(self.accept)

    def get_filters(self):
        return {
            "start": self.start_date.date().toString("yyyy-MM-dd"),
            "end": self.end_date.date().toString("yyyy-MM-dd"),
            "payment_type": self.payment_combo.currentText()
        }
