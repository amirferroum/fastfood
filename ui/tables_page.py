from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QGridLayout, QSpinBox, QMessageBox, QFrame
)
from PyQt6.QtCore import Qt
from controllers.table_controller import TableController

class TablesPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QPushButton {
                border-radius: 8px;
                padding: 10px;
                font-size: 15px;
                font-weight: 500;
            }
            QPushButton[status="Free"] {
                background-color: #44bd32;
                color: white;
            }
            QPushButton[status="Occupied"] {
                background-color: #e84118;
                color: white;
            }
            QFrame {
                background-color: #f5f6fa;
                border-radius: 10px;
                padding: 10px;
            }
        """)

        layout = QVBoxLayout(self)
        title = QLabel("🪑 Table Management")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size: 20px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Controls
        controls = QHBoxLayout()
        self.table_count_input = QSpinBox()
        self.table_count_input.setMinimum(1)
        self.table_count_input.setMaximum(50)
        self.btn_generate = QPushButton("Generate Tables")
        self.btn_generate.clicked.connect(self.generate_tables)

        controls.addWidget(QLabel("Number of tables:"))
        controls.addWidget(self.table_count_input)
        controls.addWidget(self.btn_generate)
        layout.addLayout(controls)

        # Grid
        self.grid = QGridLayout()
        self.grid.setSpacing(15)
        layout.addLayout(self.grid)

        self.load_tables()

    def load_tables(self):
        for i in reversed(range(self.grid.count())):
            self.grid.itemAt(i).widget().deleteLater()

        tables = TableController.get_all_tables()
        row, col = 0, 0
        for table in tables:
            btn = QPushButton(f"Table {table['table_number']}")
            btn.setProperty("status", table["status"])
            btn.setFixedSize(100, 80)
            btn.clicked.connect(lambda _, t=table: self.toggle_status(t))
            self.grid.addWidget(btn, row, col)

            col += 1
            if col >= 5:
                col = 0
                row += 1

    def toggle_status(self, table):
        new_status = "Free" if table["status"] == "Occupied" else "Occupied"
        TableController.update_status(table["id"], new_status)
        self.load_tables()

    def generate_tables(self):
        count = self.table_count_input.value()
        TableController.generate_tables(count)
        QMessageBox.information(self, "Done", f"{count} tables generated!")
        self.load_tables()
