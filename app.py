from flask import Flask, render_template, redirect, url_for, flash
import db
from flask_login import LoginManager, login_required, current_user
from auth import User
from routes.auth import auth_bp
from routes.recipe import recipes_bp

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = "supersecretkey"
login_manager = LoginManager(app)
# redirect here if not logged in
login_manager.login_view = "login"  # type: ignore


@login_manager.user_loader
def load_user(user_id):
    return User.get(user_id)


app.register_blueprint(auth_bp)
app.register_blueprint(recipes_bp)


@app.route("/")
def index():
    recipes = db.get_recipes()
    return render_template("index.html", recipes=recipes, user=current_user)


@app.route("/profile/<username>")
def profile(username: str):
    """Show a user's profile by username and their recipes."""
    owner = db.find_user_by_username(username)
    if not owner:
        flash("User not found.", "danger")
        return redirect(url_for("index"))

    recipes = db.get_recipes_by_user(owner["id"])

    return render_template("profile.html", owner=owner, recipes=recipes)


@app.route("/login")
def login():
    # TODO
    return "Login page — form to sign in."


if __name__ == "__main__":
    db.init_db()
    app.run(debug=True, host="0.0.0.0")
