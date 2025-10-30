# models/category.py
from models.database import get_connection

class Category:
    @staticmethod
    def all():
        """Return all categories"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM categories ORDER BY id DESC")
        rows = cur.fetchall()
        conn.close()
        return [dict(row) for row in rows]

    @staticmethod
    def create(name):
        """Create a new category"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        conn.close()

    @staticmethod
    def update(category_id, name):
        """Update category name"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE categories SET name = ? WHERE id = ?", (name, category_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(category_id):
        """Delete a category"""
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM categories WHERE id = ?", (category_id,))
        conn.commit()
        conn.close()
