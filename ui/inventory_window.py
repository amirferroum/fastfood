# ui/inventory_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QDialog,
    QFormLayout, QLineEdit, QDoubleSpinBox, QMessageBox
)
from controllers.inventory_controller import InventoryController

class InventoryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())

        # --- Top Buttons ---
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("➕ Add Ingredient")
        self.btn_refresh = QPushButton("🔄 Refresh")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_refresh)
        self.layout().addLayout(btn_layout)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Name", "Qty", "Unit", "Min Qty", "Cost (DZD)", "Product"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.layout().addWidget(self.table)

        # --- Connections ---
        self.btn_add.clicked.connect(self.add_item)
        self.btn_refresh.clicked.connect(self.load_items)

        self.load_items()

    def load_items(self):
        self.table.setRowCount(0)
        items = InventoryController.get_all()
        for row_idx, item in enumerate(items):
            self.table.insertRow(row_idx)
            for col_idx, key in enumerate(["id", "name", "quantity", "unit", "min_quantity", "cost", "product_name"]):
                value = item[key] if key in item.keys() else ""
                cell = QTableWidgetItem(str(value))
                if key == "min_quantity" and item["quantity"] <= item["min_quantity"]:
                    cell.setBackground(Qt.GlobalColor.red)
                    cell.setForeground(Qt.GlobalColor.white)
                self.table.setItem(row_idx, col_idx, cell)

    def add_item(self):
        dialog = AddIngredientDialog(self)
        if dialog.exec():
            name, qty, unit, min_qty, cost = dialog.get_data()
            InventoryController.add(name, qty, unit, min_qty, cost)
            self.load_items()


class AddIngredientDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Add Ingredient")
        layout = QFormLayout(self)

        self.input_name = QLineEdit()
        self.input_qty = QDoubleSpinBox()
        self.input_qty.setRange(0, 100000)
        self.input_unit = QLineEdit("pcs")
        self.input_min_qty = QDoubleSpinBox()
        self.input_min_qty.setRange(0, 10000)
        self.input_cost = QDoubleSpinBox()
        self.input_cost.setRange(0, 100000)
        self.input_cost.setPrefix("DZD ")

        layout.addRow("Name:", self.input_name)
        layout.addRow("Quantity:", self.input_qty)
        layout.addRow("Unit:", self.input_unit)
        layout.addRow("Min Quantity:", self.input_min_qty)
        layout.addRow("Cost per Unit:", self.input_cost)

        # Buttons
        btns = QHBoxLayout()
        btn_ok = QPushButton("Save")
        btn_cancel = QPushButton("Cancel")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btns.addWidget(btn_ok)
        btns.addWidget(btn_cancel)
        layout.addRow(btns)

    def get_data(self):
        return (
            self.input_name.text(),
            self.input_qty.value(),
            self.input_unit.text(),
            self.input_min_qty.value(),
            self.input_cost.value(),
        )
