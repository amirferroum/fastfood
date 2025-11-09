# src/ui/users_window.py
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QHBoxLayout, QPushButton,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox, QDialog,
    QLineEdit, QComboBox, QFormLayout, QDialogButtonBox
)
from PyQt6.QtCore import Qt
import sqlite3

class UsersPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI';
            }
            QLabel {
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #005a9e;
            }
            QTableWidget {
                background: white;
                border: 1px solid #ddd;
                border-radius: 8px;
            }
            QHeaderView::section {
                background-color: #0078D7;
                color: white;
                font-weight: bold;
                padding: 6px;
                border: none;
            }
        """)
        self.init_ui()
        self.load_users()

    def init_ui(self):
        layout = QVBoxLayout()

        # --- Header ---
        header = QHBoxLayout()
        title = QLabel("👤 User Management")
        header.addWidget(title)
        header.addStretch()

        self.add_btn = QPushButton("➕ Add User")
        self.edit_btn = QPushButton("✏️ Edit")
        self.delete_btn = QPushButton("🗑️ Delete")

        self.add_btn.clicked.connect(self.add_user)
        self.edit_btn.clicked.connect(self.edit_user)
        self.delete_btn.clicked.connect(self.delete_user)

        for btn in (self.add_btn, self.edit_btn, self.delete_btn):
            header.addWidget(btn)

        layout.addLayout(header)

        # --- Table ---
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Username", "Role", "ID"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        layout.addWidget(self.table)

        self.setLayout(layout)

    def connect_db(self):
        return sqlite3.connect("fastfood.db")

    def load_users(self):
        conn = self.connect_db()
        cur = conn.cursor()
        cur.execute("SELECT username, role, id FROM users")
        rows = cur.fetchall()
        conn.close()

        self.table.setRowCount(len(rows))
        for i, row in enumerate(rows):
            for j, val in enumerate(row):
                self.table.setItem(i, j, QTableWidgetItem(str(val)))

    # --- Add User Dialog ---
    def add_user(self):
        dialog = UserDialog()
        if dialog.exec() == QDialog.DialogCode.Accepted:
            username, password, role = dialog.get_data()
            conn = self.connect_db()
            try:
                conn.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                             (username, password, role))
                conn.commit()
                self.load_users()
            except sqlite3.IntegrityError:
                QMessageBox.warning(self, "Error", "Username already exists!")
            finally:
                conn.close()

    def edit_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Please select a user to edit.")
            return

        username = self.table.item(row, 0).text()
        role = self.table.item(row, 1).text()
        user_id = int(self.table.item(row, 2).text())

        dialog = UserDialog(username, "", role)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_username, new_password, new_role = dialog.get_data()
            conn = self.connect_db()
            if new_password:
                conn.execute("UPDATE users SET username=?, password=?, role=? WHERE id=?",
                             (new_username, new_password, new_role, user_id))
            else:
                conn.execute("UPDATE users SET username=?, role=? WHERE id=?",
                             (new_username, new_role, user_id))
            conn.commit()
            conn.close()
            self.load_users()

    def delete_user(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "Error", "Select a user to delete.")
            return
        user_id = int(self.table.item(row, 2).text())
        confirm = QMessageBox.question(
            self, "Confirm", "Are you sure you want to delete this user?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if confirm == QMessageBox.StandardButton.Yes:
            conn = self.connect_db()
            conn.execute("DELETE FROM users WHERE id=?", (user_id,))
            conn.commit()
            conn.close()
            self.load_users()

# --- Add/Edit Dialog ---
class UserDialog(QDialog):
    def __init__(self, username="", password="", role="cashier"):
        super().__init__()
        self.setWindowTitle("User Details")
        layout = QFormLayout()

        self.username_input = QLineEdit(username)
        self.password_input = QLineEdit(password)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.role_combo = QComboBox()
        self.role_combo.addItems(["admin", "cashier", "kitchen", "manager"])
        self.role_combo.setCurrentText(role)

        layout.addRow("Username:", self.username_input)
        layout.addRow("Password:", self.password_input)
        layout.addRow("Role:", self.role_combo)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)
        self.setMinimumWidth(300)

    def get_data(self):
        return (
            self.username_input.text().strip(),
            self.password_input.text().strip(),
            self.role_combo.currentText()
        )
