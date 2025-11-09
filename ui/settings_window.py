import os
import shutil
import sqlite3
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QFormLayout,
    QFileDialog, QMessageBox, QScrollArea, QGroupBox, QHBoxLayout
)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
from models.database import get_connection, DB_PATH


class SettingsPage(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Settings")
        self.resize(750, 700)

        # ---------- Scrollable Main Layout ----------
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        self.layout = QVBoxLayout(content)
        self.layout.setContentsMargins(25, 25, 25, 25)
        self.layout.setSpacing(20)
        scroll.setWidget(content)

        # ---------- Sections ----------
        self.init_business_info()
        self.init_tax_currency()
        self.init_inventory_toggle()
        self.init_user_settings()
        self.init_backup_restore()

        # ---------- Save Button ----------
        self.save_button = QPushButton("💾 Save Settings")
        self.save_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.save_button.clicked.connect(self.save_settings)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                font-weight: bold;
                padding: 10px 20px;
                border-radius: 8px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45A049;
            }
        """)
        self.layout.addWidget(self.save_button, alignment=Qt.AlignmentFlag.AlignCenter)

        # ---------- Main Layout ----------
        main_layout = QVBoxLayout()
        main_layout.addWidget(scroll)
        self.setLayout(main_layout)

        self.load_settings()
        self.apply_styles()

    # ------------------ STYLE ------------------
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', sans-serif;
                font-size: 13px;
            }
            QGroupBox {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 12px;
                margin-top: 10px;
                padding: 15px;
                font-weight: bold;
                font-size: 14px;
            }
            QLineEdit {
                padding: 6px;
                border-radius: 6px;
                border: 1px solid #ccc;
                background: #fff;
            }
            QLabel {
                font-size: 13px;
            }
        """)

    # ------------------ BUSINESS INFO ------------------
    def init_business_info(self):
        group = QGroupBox("🏢 Business Information")
        form = QFormLayout()

        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Enter restaurant name")
        self.address_input = QLineEdit()
        self.address_input.setPlaceholderText("Enter address")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("Enter phone number")

        self.logo_label = QLabel("No logo uploaded")
        self.logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.logo_label.setFixedSize(120, 120)
        self.logo_label.setStyleSheet("border: 1px dashed #aaa; border-radius: 10px; background: #fafafa;")
        self.logo_button = QPushButton("📁 Upload Logo")
        self.logo_button.clicked.connect(self.upload_logo)
        self.logo_path = None

        form.addRow("Restaurant Name:", self.name_input)
        form.addRow("Address:", self.address_input)
        form.addRow("Phone:", self.phone_input)
        form.addRow("Logo:", self.logo_button)
        form.addRow("", self.logo_label)

        group.setLayout(form)
        self.layout.addWidget(group)

    # ------------------ TAX & CURRENCY ------------------
    def init_tax_currency(self):
        group = QGroupBox("💰 Tax & Currency")
        form = QFormLayout()

        self.vat_input = QLineEdit()
        self.vat_input.setPlaceholderText("e.g. 19")
        self.currency_input = QLineEdit()
        self.currency_input.setPlaceholderText("e.g. DZD")

        form.addRow("VAT Percentage (%):", self.vat_input)
        form.addRow("Currency Symbol:", self.currency_input)
        group.setLayout(form)
        self.layout.addWidget(group)

    # ------------------ USER SETTINGS ------------------
    def init_user_settings(self):
        group = QGroupBox("👤 User Settings")
        form = QFormLayout()

        self.old_password = QLineEdit()
        self.old_password.setPlaceholderText("Enter old password")
        self.old_password.setEchoMode(QLineEdit.EchoMode.Password)
        self.new_password = QLineEdit()
        self.new_password.setPlaceholderText("Enter new password")
        self.new_password.setEchoMode(QLineEdit.EchoMode.Password)

        self.change_password_btn = QPushButton("🔑 Change Password")
        self.change_password_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.change_password_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078D7;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #006CBE;
            }
        """)
        self.change_password_btn.clicked.connect(self.change_password)

        form.addRow("Old Password:", self.old_password)
        form.addRow("New Password:", self.new_password)
        form.addRow("", self.change_password_btn)
        group.setLayout(form)
        self.layout.addWidget(group)

    # ------------------ BACKUP & RESTORE ------------------
    def init_backup_restore(self):
        group = QGroupBox("🗂️ Backup & Restore")
        layout = QHBoxLayout()

        backup_btn = QPushButton("⬇️ Export Database")
        backup_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        backup_btn.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #FB8C00;
            }
        """)
        backup_btn.clicked.connect(self.export_db)

        restore_btn = QPushButton("⬆️ Import Database")
        restore_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        restore_btn.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border-radius: 6px;
                padding: 6px 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
        """)
        restore_btn.clicked.connect(self.import_db)

        layout.addWidget(backup_btn)
        layout.addWidget(restore_btn)
        group.setLayout(layout)
        self.layout.addWidget(group)
    
    # ------------------ INVENTORY TOGGLE ------------------
    def init_inventory_toggle(self):
        group = QGroupBox("📦 Inventory Management")
        layout = QHBoxLayout()

        self.inventory_toggle = QPushButton()
        self.inventory_toggle.setCheckable(True)
        self.inventory_toggle.setCursor(Qt.CursorShape.PointingHandCursor)
        self.inventory_toggle.setFixedWidth(180)
        self.inventory_toggle.clicked.connect(self.toggle_inventory_button_style)

        layout.addWidget(QLabel("Enable / Disable Inventory:"))
        layout.addWidget(self.inventory_toggle)
        group.setLayout(layout)
        self.layout.addWidget(group)
    
    def toggle_inventory_button_style(self):
        enabled = self.inventory_toggle.isChecked()
        self.inventory_toggle.setText("✅ Enabled" if enabled else "❌ Disabled")
        self.inventory_toggle.setStyleSheet("""
            QPushButton {
                border-radius: 8px;
                padding: 6px 12px;
                font-weight: bold;
                color: white;
                background-color: %s;
            }
        """ % ("#4CAF50" if enabled else "#F44336"))



    # ------------------ LOAD SETTINGS ------------------
    def load_settings(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM settings LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        if row:
            self.name_input.setText(row["restaurant_name"] or "")
            self.address_input.setText(row["address"] or "")
            self.phone_input.setText(row["phone"] or "")
            self.vat_input.setText(str(row["vat_percentage"]))
            self.currency_input.setText(row["currency_symbol"] or "")
            self.inventory_toggle.setChecked(bool(row["inventory_enabled"]))
            self.toggle_inventory_button_style()

            if row["logo_path"] and os.path.exists(row["logo_path"]):
                pixmap = QPixmap(row["logo_path"]).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
                self.logo_label.setPixmap(pixmap)
                self.logo_path = row["logo_path"]

    # ------------------ SAVE SETTINGS ------------------
    def save_settings(self):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE settings
            SET restaurant_name = ?, address = ?, phone = ?, logo_path = ?, 
                vat_percentage = ?, currency_symbol = ?, inventory_enabled = ?
            WHERE id = 1
        """, (
            self.name_input.text(),
            self.address_input.text(),
            self.phone_input.text(),
            self.logo_path,
            float(self.vat_input.text() or 0),
            self.currency_input.text(),
            1 if self.inventory_toggle.isChecked() else 0
        ))

        conn.commit()
        conn.close()
        QMessageBox.information(self, "✅ Saved", "Settings saved successfully!")

    # ------------------ UPLOAD LOGO ------------------
    def upload_logo(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Logo", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if file_path:
            pixmap = QPixmap(file_path).scaled(120, 120, Qt.AspectRatioMode.KeepAspectRatio)
            self.logo_label.setPixmap(pixmap)
            self.logo_path = file_path

    # ------------------ CHANGE PASSWORD ------------------
    def change_password(self):
        old_pass = self.old_password.text()
        new_pass = self.new_password.text()

        if not old_pass or not new_pass:
            QMessageBox.warning(self, "⚠️ Error", "Please fill in both password fields.")
            return

        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT password FROM users WHERE id = 1")  # assuming admin = id 1
        row = cursor.fetchone()

        if not row or row["password"] != old_pass:
            QMessageBox.warning(self, "❌ Error", "Old password is incorrect.")
        else:
            cursor.execute("UPDATE users SET password = ? WHERE id = 1", (new_pass,))
            conn.commit()
            QMessageBox.information(self, "🔒 Success", "Password updated successfully!")

        conn.close()

    # ------------------ EXPORT DATABASE ------------------
    def export_db(self):
        target_file, _ = QFileDialog.getSaveFileName(self, "Export Database", "", "SQLite DB (*.db)")
        if target_file:
            shutil.copy(DB_PATH, target_file)
            QMessageBox.information(self, "✅ Backup", f"Database exported to:\n{target_file}")

    # ------------------ IMPORT DATABASE ------------------
    def import_db(self):
        source_file, _ = QFileDialog.getOpenFileName(self, "Import Database", "", "SQLite DB (*.db)")
        if source_file:
            try:
                shutil.copy(source_file, DB_PATH)
                QMessageBox.information(self, "✅ Restore", "Database imported successfully. Restart app to apply changes.")
            except Exception as e:
                QMessageBox.warning(self, "⚠️ Error", f"Import failed: {e}")
