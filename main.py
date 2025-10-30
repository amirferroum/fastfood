# main.py
from models.database import init_db
from ui.admin_dashboard import AdminDashboard
from PyQt6.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    init_db()

    app = QApplication(sys.argv)
    window = AdminDashboard()
    window.show()
    sys.exit(app.exec())
