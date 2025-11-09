# models/product.py
from models.database import get_connection

class Product:
    @staticmethod
    def get_all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, c.name AS category_name 
            FROM products p 
            LEFT JOIN categories c ON p.category_id = c.id
        """)
        products = [dict(zip([c[0] for c in cursor.description], row)) for row in cursor.fetchall()]
        conn.close()
        return products


    @staticmethod
    def create(name, category_id, price, image=None, status="available"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO products (name, category_id, price, image, status)
            VALUES (?, ?, ?, ?, ?)
        """, (name, category_id, price, image, status))
        conn.commit()
        conn.close()

    @staticmethod
    def update(product_id, name, category_id, price, status):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE products SET name=?, category_id=?, price=?, status=?
            WHERE id=?
        """, (name, category_id, price, status, product_id))
        conn.commit()
        conn.close()

    @staticmethod
    def delete(product_id):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products WHERE id=?", (product_id,))
        conn.commit()
        conn.close()

    @staticmethod
    def get_by_id(product_id):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM products WHERE id = ?", (product_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
