# models/printer.py
from models.database import get_connection

class Printer:
    @staticmethod
    def create(name, type, connection, ip_address=None, port=None, categories=None, status="offline"):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO printers (name, type, connection, ip_address, port, assigned_categories, status)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (name, type, connection, ip_address, port, ",".join(categories or []), status))
        conn.commit()
        conn.close()

    @staticmethod
    def all():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM printers ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def update(id, **kwargs):
        conn = get_connection()
        cur = conn.cursor()
        fields = ", ".join([f"{k}=?" for k in kwargs])
        params = list(kwargs.values()) + [id]
        cur.execute(f"UPDATE printers SET {fields} WHERE id=?", params)
        conn.commit()
        conn.close()

    @staticmethod
    def delete(id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM printers WHERE id=?", (id,))
        conn.commit()
        conn.close()

    @staticmethod
    def find_by_name(name):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM printers WHERE name=?", (name,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    
    @staticmethod
    def assign_category(printer_id, category):
        """Assign or append category to printer (supports multiple categories)"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT assigned_categories FROM printers WHERE id=?", (printer_id,))
        row = cur.fetchone()
        if row and row["assigned_categories"]:
            existing = set(row["assigned_categories"].split(","))
        else:
            existing = set()

        existing.add(category)
        cur.execute("UPDATE printers SET assigned_categories=? WHERE id=?", (",".join(existing), printer_id))
        conn.commit()
        conn.close()

    @staticmethod
    def remove_category(printer_id, category):
        """Remove a category from printer"""
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("SELECT assigned_categories FROM printers WHERE id=?", (printer_id,))
        row = cur.fetchone()
        if not row or not row["assigned_categories"]:
            conn.close()
            return

        existing = set(row["assigned_categories"].split(","))
        if category in existing:
            existing.remove(category)
            cur.execute("UPDATE printers SET assigned_categories=? WHERE id=?", (",".join(existing), printer_id))

        conn.commit()
        conn.close()


