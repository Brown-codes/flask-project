from flask_login import UserMixin
import db


class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = str(id)  # Flask-Login requires IDs to be strings
        self.username = username
        self.password_hash = password_hash

    @staticmethod
    def get(user_id):
        """Load a user by ID."""
        user_row = db.get_user(user_id)
        if user_row:
            return User(user_row["id"], user_row["username"], user_row["password"])
        return None

    @staticmethod
    def find_by_username(username):
        """Load a user by username."""
        user_row = db.find_user_by_username(username)
        if user_row:
            return User(user_row["id"], user_row["username"], user_row["password"])
        return None

    def check_password(self, password):
        """Verify the password."""
        return self.password_hash == password

    @staticmethod
    def create(username, password):
        """Create a new user."""
        db.create_user(username=username, password=password)
        return User.find_by_username(username)
