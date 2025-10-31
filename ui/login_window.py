# ui/login_window.py
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from controllers.auth_controller import AuthController
from ui.admin_dashboard import AdminDashboard  # your main window

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")
        self.setFixedSize(300, 200)

        layout = QVBoxLayout()
        layout.addWidget(QLabel("Username:"))
        self.username = QLineEdit()
        layout.addWidget(self.username)

        layout.addWidget(QLabel("Password:"))
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addWidget(self.password)

        self.btn_login = QPushButton("Login")
        self.btn_login.clicked.connect(self.handle_login)
        layout.addWidget(self.btn_login)

        self.setLayout(layout)

    def handle_login(self):
        user = AuthController.login(self.username.text(), self.password.text())
        if user:
            self.hide()
            self.dashboard = AdminDashboard(user)
            self.dashboard.show()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password")
