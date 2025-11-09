from models.database import get_connection

class TableController:
    @staticmethod
    def get_all_tables():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM tables ORDER BY table_number")
        tables = cur.fetchall()
        conn.close()
        return tables

    @staticmethod
    def generate_tables(count):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM tables")  # reset
        for i in range(1, count + 1):
            cur.execute("INSERT INTO tables (table_number, status) VALUES (?, ?)", (i, "Free"))
        conn.commit()
        conn.close()

    @staticmethod
    def update_status(table_id, status):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE tables SET status = ? WHERE id = ?", (status, table_id))
        conn.commit()
        conn.close()
