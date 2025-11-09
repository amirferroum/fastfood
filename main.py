# main.py
from PyQt6.QtWidgets import QApplication
from ui.login_window import LoginWindow
import sys
from models.database import init_db

if __name__ == "__main__":
    
    app = QApplication(sys.argv)
    init_db()

    window = LoginWindow()
    window.show()
    sys.exit(app.exec())
