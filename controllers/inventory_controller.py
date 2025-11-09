# controllers/inventory_controller.py
from models.database import get_connection

class InventoryController:
    @staticmethod
    def get_all():
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT i.id, i.name, i.quantity, i.unit, i.min_quantity, i.cost, p.name AS product_name
            FROM ingredients i
            LEFT JOIN products p ON i.product_id = p.id
            ORDER BY i.name
        """)
        items = cur.fetchall()
        conn.close()
        return items

    @staticmethod
    def add(name, quantity, unit, min_quantity, cost, product_id=None):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ingredients (name, quantity, unit, min_quantity, cost, product_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (name, quantity, unit, min_quantity, cost, product_id))
        conn.commit()
        conn.close()

    @staticmethod
    def update(item_id, name, quantity, unit, min_quantity, cost, product_id=None):
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE ingredients
            SET name=?, quantity=?, unit=?, min_quantity=?, cost=?, product_id=?
            WHERE id=?
        """, (name, quantity, unit, min_quantity, cost, product_id, item_id))
        conn.commit()
        conn.close()
