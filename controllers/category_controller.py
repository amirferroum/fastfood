# controllers/category_controller.py
from models.category import Category

class CategoryController:
    @staticmethod
    def get_all():
        """Return all categories"""
        return Category.all()

    @staticmethod
    def add(name):
        """Add a new category"""
        Category.create(name)

    @staticmethod
    def update(category_id, name):
        """Update category name"""
        Category.update(category_id, name)

    @staticmethod
    def delete(category_id):
        """Delete a category"""
        Category.delete(category_id)
