from models.database import get_connection

class User:
    @staticmethod
    def find_by_username(username):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE username=?", (username,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
