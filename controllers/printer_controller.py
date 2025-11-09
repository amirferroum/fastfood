import cups
import subprocess
import re
from PyQt6.QtWidgets import QMessageBox
from models.printer import Printer


class PrinterController:
    # === SYSTEM DETECTION ===
    @staticmethod
    def detect_system_printers():
        """Detect printers available through CUPS and classify them."""
        printers = []
        try:
            conn = cups.Connection()
            cups_printers = conn.getPrinters()

            for name, info in cups_printers.items():
                uri = info.get("device-uri", "").lower()
                printer_type = "manual"
                ip = None
                port = None

                # Detect connection type from URI
                if uri.startswith("usb://"):
                    printer_type = "usb"
                elif any(uri.startswith(proto) for proto in ["socket://", "ipp://", "lpd://"]):
                    printer_type = "network"
                    match = re.search(r"(\d+\.\d+\.\d+\.\d+)(?::(\d+))?", uri)
                    if match:
                        ip = match.group(1)
                        port = int(match.group(2)) if match.group(2) else 9100

                printers.append({
                    "name": name,
                    "uri": uri,
                    "connection": printer_type,
                    "ip": ip,
                    "port": port,
                    "info": info.get("printer-info", ""),
                    "state": info.get("printer-state", 0),
                    "status": info.get("printer-state-message", "Unknown"),
                })
        except RuntimeError as e:
            print("CUPS error:", e)

        return printers

    @staticmethod
    def detect_printers():
        """Fallback printer detection using lpstat (if CUPS unavailable)."""
        try:
            result = subprocess.run(["lpstat", "-p"], capture_output=True, text=True)
            printers = []
            for line in result.stdout.splitlines():
                if line.startswith("printer"):
                    name = line.split()[1]
                    printers.append({"name": name, "connection": "manual"})
            return printers
        except Exception as e:
            print("Error detecting printers:", e)
            return []

    # === DATABASE ACCESS ===
    @staticmethod
    def get_all():
        """Return all printers stored in the local database."""
        printers = Printer.all()
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "ip": p.get("ip_address", "N/A"),
                "connection": p.get("connection", "manual"),
                "categories": p.get("assigned_categories", "Unassigned")
                    if p.get("assigned_categories") else "Unassigned",
                "status": p.get("status", "offline"),
            }
            for p in printers
        ]

    # === ADD / REMOVE ===
    @staticmethod
    def add_printer(name, connection_type="usb", ip=None, port=None, categories=None, parent=None):
        """
        Add a new printer entry with flexible connection type.
        connection_type: 'usb', 'network', or 'manual'
        categories: can be a string or list
        """
        if not name:
            QMessageBox.warning(parent, "Error", "Printer name is required")
            return

        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",") if c.strip()]

        try:
            Printer.create(
                name=name,
                type="thermal",
                connection=connection_type,
                ip_address=ip,
                port=port,
                categories=categories,
                status="online"
            )
            QMessageBox.information(parent, "Success", f"Printer '{name}' added successfully")
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to add printer: {e}")

    @staticmethod
    def add_manual(name, ip, categories, parent=None):
        """Backward compatibility for manual printer addition."""
        PrinterController.add_printer(name, "manual", ip=ip, categories=categories, parent=parent)

    @staticmethod
    def delete_printer(printer_id, parent=None):
        """Delete printer from DB."""
        try:
            Printer.delete(printer_id)
            QMessageBox.information(parent, "Deleted", "Printer removed successfully")
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to delete: {e}")

    # === PRINT TEST ===
    @staticmethod
    def print_test(printer_name, parent=None):
        """Send a test print to the given printer."""
        try:
            conn = cups.Connection()
            file_path = "/usr/share/cups/data/testprint"
            conn.printFile(printer_name, file_path, "Test Print", {})
            QMessageBox.information(parent, "Success", f"Test print sent to {printer_name}")
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to print: {e}")

    # === AUTO-REGISTER ===
    @staticmethod
    def auto_register_printers(parent=None):
        """
        Detect all printers (USB & network) via CUPS
        and automatically register new ones in the local DB if not found.
        """
        detected = PrinterController.detect_system_printers()
        existing = [p["name"] for p in Printer.all()]

        added = 0
        for p in detected:
            if p["name"] not in existing:
                Printer.create(
                    name=p["name"],
                    type="thermal",
                    connection=p["connection"],
                    ip_address=p["ip"],
                    port=p["port"],
                    categories=[],
                    status="online",
                )
                added += 1

        if parent:
            if added > 0:
                QMessageBox.information(parent, "Printers Detected", f"{added} new printer(s) added.")
            else:
                QMessageBox.information(parent, "No New Printers", "All detected printers already exist.")

        return added
