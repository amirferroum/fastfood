import usb.core
import usb.util
import re
from escpos.printer import Usb, Network
from PyQt6.QtWidgets import QMessageBox
from models.printer import Printer


class PrinterController:

    # ------------------------------------------------------
    # USB DETECTION (pyusb)
    # ------------------------------------------------------
    @staticmethod
    def detect_usb_printers():
        import usb.core, usb.util
        printers = []
        devices = usb.core.find(find_all=True)

        for dev in devices:
            is_printer = False

            if dev.bDeviceClass == 7:
                is_printer = True
            elif dev.bDeviceClass == 0:  # might expose printer class through interfaces
                try:
                    cfg = dev.get_active_configuration()
                    for interface in cfg:
                        if interface.bInterfaceClass == 7:
                            is_printer = True
                            break
                except:
                    pass

            if not is_printer:
                continue

            printers.append({
                "name": usb.util.get_string(dev, dev.iProduct) or "USB Printer",
                "vendor_id": f"{dev.idVendor:04X}",
                "product_id": f"{dev.idProduct:04X}",
                "serial_number": usb.util.get_string(dev, dev.iSerialNumber) or "",
                "connection": "usb"
            })

        return printers



    # ------------------------------------------------------
    # FALLBACK SIMPLE PRINTER DETECTOR (Manual mode)
    # ------------------------------------------------------
    @staticmethod
    def detect_printers():
        """Fallback manual detection if needed."""
        return [{"name": "Manual Printer", "connection": "manual"}]

    # ------------------------------------------------------
    # READ DATABASE
    # ------------------------------------------------------
    @staticmethod
    def get_all():
        printers = Printer.all()
        return [
            {
                "id": p["id"],
                "name": p["name"],
                "connection": p.get("connection_type", "manual"),
                "ip": p.get("ip_address", "N/A"),
                "port": p.get("port", "N/A"),
                "categories": p.get("assigned_categories", "Unassigned") or "Unassigned",
                "status": p.get("status", "offline"),
                "vendor_id": p.get("vendor_id", None),
                "product_id": p.get("product_id", None),
            }
            for p in printers
        ]

    # ------------------------------------------------------
    # ADD PRINTER TO DB
    # ------------------------------------------------------
    @staticmethod
    def add_printer(name, connection_type="manual", vendor_id=None, product_id=None,
                    serial_number=None, ip=None, port=None, categories=None, parent=None):

        if not name:
            QMessageBox.warning(parent, "Missing Name", "Printer name is required.")
            return

        # Normalize categories
        if isinstance(categories, str):
            categories = [c.strip() for c in categories.split(",") if c.strip()]

        try:
            Printer.create(
                name=name,
                connection_type=connection_type,
                vendor_id=vendor_id,
                product_id=product_id,
                serial_number=serial_number,
                ip_address=ip,
                port=port,
                assigned_categories=",".join(categories) if categories else None,
                status="offline"
            )

            QMessageBox.information(parent, "Success",
                                    f"Printer '{name}' added successfully!")

        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to add printer:\n{e}")

    # ------------------------------------------------------
    # DELETE
    # ------------------------------------------------------
    @staticmethod
    def delete_printer(printer_id, parent=None):
        try:
            Printer.delete(printer_id)
            QMessageBox.information(parent, "Deleted", "Printer removed successfully")
        except Exception as e:
            QMessageBox.warning(parent, "Error", f"Failed to delete: {e}")

    # ------------------------------------------------------
    # PRINT TEST
    # ------------------------------------------------------
    @staticmethod
    def print_test(printer, parent=None):
        """
        printer must be a DB printer row dict from get_all()
        """
        try:
            if printer["connection"] == "usb":
                v = int(printer["vendor_id"], 16)
                p = int(printer["product_id"], 16)
                escpos = Usb(v, p, timeout=4000)
                escpos.text("Test Print OK\n")
                escpos.cut()

            elif printer["connection"] == "network":
                escpos = Network(printer["ip"], printer["port"])
                escpos.text("Network Test Print OK\n")
                escpos.cut()

            else:
                raise Exception("Manual printers cannot print test automatically.")

            QMessageBox.information(parent, "Success", f"Test print sent to {printer['name']}")

        except Exception as e:
            QMessageBox.warning(parent, "Print Error", str(e))

    # ------------------------------------------------------
    # AUTO REGISTER DETECTED PRINTERS
    # ------------------------------------------------------
    @staticmethod
    def auto_register_printers(parent=None):
        detected = PrinterController.detect_usb_printers()
        existing_names = [p["name"] for p in Printer.all()]

        added = 0
        for p in detected:
            if p["name"] not in existing_names:
                Printer.create(
                    name=p["name"],
                    connection_type="usb",
                    vendor_id=p["vendor_id"],
                    product_id=p["product_id"],
                    assigned_categories=[],
                    status="online"
                )
                added += 1

        if parent:
            if added > 0:
                QMessageBox.information(parent, "Printers Detected", f"{added} new printer(s) added.")
            else:
                QMessageBox.information(parent, "No New Printers", "All detected printers already exist.")

        return added
