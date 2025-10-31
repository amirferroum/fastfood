from models.user import User

class AuthController:
    @staticmethod
    def login(username, password):
        user = User.find_by_username(username)
        if not user:
            return None
        # Simple password check (later we’ll use bcrypt)
        if user["password"] == password:
            return user
        return None
