# models/product.py
from models.database import get_connection

class Product:
    @staticmethod
    def all():
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT products.*, categories.name AS category_name
            FROM products
            LEFT JOIN categories ON products.category_id = categories.id
        """)
        rows = cursor.fetchall()
        conn.close()
        return [dict(row) for row in rows]

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
