from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QFrame, QCheckBox
)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt, QTimer
from models.database import get_connection
from utils.config_manager import load_config, save_config


class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("🍔 FastFood POS - Login")
        self.setFixedSize(380, 320)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f6fa;
                font-family: 'Segoe UI';
            }
            QLabel {
                font-size: 14px;
            }
            QLineEdit {
                padding: 8px;
                border: 1px solid #dcdde1;
                border-radius: 6px;
                font-size: 14px;
            }
            QPushButton {
                background-color: #44bd32;
                color: white;
                border-radius: 6px;
                padding: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #4cd137;
            }
        """)

        # Layout setup
        main_layout = QVBoxLayout()
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title = QLabel("🍟 FastFood POS Login")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(title)

        frame = QFrame()
        frame_layout = QVBoxLayout(frame)
        frame_layout.setSpacing(12)
        frame_layout.setContentsMargins(30, 20, 30, 20)

        # Username
        lbl_user = QLabel("👤 Username:")
        self.username = QLineEdit()
        self.username.setPlaceholderText("Enter username")
        frame_layout.addWidget(lbl_user)
        frame_layout.addWidget(self.username)

        # Password
        lbl_pass = QLabel("🔒 Password:")
        self.password = QLineEdit()
        self.password.setPlaceholderText("Enter password")
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        frame_layout.addWidget(lbl_pass)
        frame_layout.addWidget(self.password)

        # Remember Me
        self.remember_me = QCheckBox("Remember Me")
        frame_layout.addWidget(self.remember_me)

        # Login Button
        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.handle_login)
        frame_layout.addWidget(self.btn_login)

        main_layout.addWidget(frame)
        self.setLayout(main_layout)

        # Try auto-login if config exists
        QTimer.singleShot(300, self.auto_login_if_saved)

    # ---------------------------------------
    # Auto login if saved
    # ---------------------------------------
    def auto_login_if_saved(self):
        config = load_config()
        if "username" in config and "role" in config:
            self.hide()
            self.open_dashboard(config["role"])

    # ---------------------------------------
    # Login Logic
    # ---------------------------------------
    def handle_login(self):
        username = self.username.text().strip()
        password = self.password.text().strip()

        if not username or not password:
            QMessageBox.warning(self, "Missing Fields", "Please enter both username and password.")
            return

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = cur.fetchone()
        conn.close()

        if user:
            role = user["role"]

            if self.remember_me.isChecked():
                save_config({"username": username, "role": role})
            else:
                save_config({})  # clear if not checked

            self.open_dashboard(role)
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password!")

    # ---------------------------------------
    # Open correct dashboard by role
    # ---------------------------------------
    def open_dashboard(self, role):
        self.close()

        if role == "admin":
            from ui.admin_dashboard import AdminDashboard
            self.dashboard = AdminDashboard(role)
        elif role == "cashier":
            from ui.pos_window import POSWindow
            self.dashboard = POSWindow(role)
        else:
            QMessageBox.warning(self, "Error", f"Unknown role: {role}")
            return

        self.dashboard.show()
