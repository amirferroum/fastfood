from models.database import get_connection

class SettingsController:
    @staticmethod
    def get_settings():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM settings LIMIT 1")
        settings = cur.fetchone()
        conn.close()
        return dict(settings) if settings else {}

    @staticmethod
    def update_inventory_status(enabled: bool):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE settings SET inventory_enabled = ?", (1 if enabled else 0,))
        conn.commit()
        conn.close()

    @staticmethod
    def is_inventory_enabled():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT inventory_enabled FROM settings LIMIT 1")
        val = cur.fetchone()
        conn.close()
        return bool(val[0]) if val else False
