import cups
from PyQt6.QtWidgets import QMessageBox
from models.printer import Printer
import subprocess

class PrinterController:
    @staticmethod
    def detect_system_printers():
        """Detect printers available through CUPS"""
        try:
            conn = cups.Connection()
            printers = conn.getPrinters()
            return [
                {
                    "name": name,
                    "info": info.get("printer-info", ""),
                    "state": info.get("printer-state", 0),
                }
                for name, info in printers.items()
            ]
        except RuntimeError as e:
            print("CUPS error:", e)
            return []

    @staticmethod
    def get_all():
        """Return printers stored in app DB"""
        printers = Printer.all()
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "ip": p["ip_address"],
                "category": p.get("assigned_categories", "Unassigned")
            }
            for p in printers
        ]


    
    @staticmethod
    def add_manual(name, ip, category, parent=None):
        """Add a manual printer entry"""
        if not name:
            QMessageBox.warning(parent, "Error", "Printer name required")
            return
        Printer.create(
            name=name,
            type="thermal",
            connection="manual",
            ip_address=ip,
            port=None,
            categories=[category],
            status="online"
        )
        QMessageBox.information(parent, "Success", "Printer added successfully")


    @staticmethod
    def delete_printer(printer_id, parent=None):
        """Delete printer"""
        Printer.delete(printer_id)
        QMessageBox.information(parent, "Deleted", "Printer removed from system")

    @staticmethod
    def print_test(printer_name, parent=None):
        """Send test print"""
        try:
            conn = cups.Connection()
            file_path = "/usr/share/cups/data/testprint"
            conn.printFile(printer_name, file_path, "Test Print", {})
            QMessageBox.information(parent, "Success", f"Test print sent to {printer_name}")
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed: {e}")

    @staticmethod
    def detect_printers():
        try:
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
            printers = []
            for line in result.stdout.splitlines():
                if line.startswith("printer"):
                    name = line.split()[1]
                    printers.append(name)
            return printers
        except Exception as e:
            print("Error detecting printers:", e)
            return []