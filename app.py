from flask import Flask, render_template, request, redirect, url_for, session, g
import sqlite3
import os

# -----------------------------
# CONFIGURATION
# -----------------------------
app = Flask(__name__)
app.secret_key = (
    "supersecretkey"  # Needed for sessions. In real apps, use environment variable.
)

# Path to database (inside instance folder)
DB_PATH = os.path.join("instance", "recipes.db")


# -----------------------------
# DATABASE CONNECTION HELPERS
# -----------------------------
def get_db():
    """
    Opens a connection to the SQLite database.
    g is a Flask special object to store data during a request (like db connections).
    """
    if "db" not in g:
        g.db = sqlite3.connect(DB_PATH)
        g.db.row_factory = (
            sqlite3.Row
        )  # Makes rows act like dicts (column access by name)
    return g.db


@app.teardown_appcontext
def close_db(error):
    """
    Automatically closes database connection after each request.
    """
    db = g.pop("db", None)
    if db is not None:
        db.close()


# -----------------------------
# ROUTES
# -----------------------------
@app.route("/")
def index():
    """
    Homepage - shows list of recipes.
    """
    db = get_db()
    recipes = db.execute(
        "SELECT r.id, r.title, r.description, u.username FROM recipes r LEFT JOIN users u ON r.created_by = u.id"
    ).fetchall()
    return render_template("index.html", recipes=recipes)


@app.route("/register", methods=["GET", "POST"])
def register():
    """
    User registration page.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form[
            "password"
        ]  # NOTE: Plaintext for simplicity (not secure!)

        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, password),
            )
            db.commit()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            return "❌ Username already taken!"
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    """
    Login page.
    """
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        db = get_db()
        user = db.execute(
            "SELECT * FROM users WHERE username=? AND password=?", (username, password)
        ).fetchone()

        if user:
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("index"))
        else:
            return "❌ Invalid credentials!"
    return render_template("login.html")


@app.route("/logout")
def logout():
    """
    Logs the user out.
    """
    session.clear()
    return redirect(url_for("index"))


@app.route("/recipe/<int:recipe_id>", methods=["GET", "POST"])
def recipe_detail(recipe_id):
    """
    Recipe detail page + commenting.
    """
    db = get_db()

    # Handle new comment
    if request.method == "POST":
        if "user_id" not in session:
            return redirect(url_for("login"))
        content = request.form["content"]
        db.execute(
            "INSERT INTO comments (recipe_id, user_id, content) VALUES (?, ?, ?)",
            (recipe_id, session["user_id"], content),
        )
        db.commit()
        return redirect(url_for("recipe_detail", recipe_id=recipe_id))

    recipe = db.execute(
        "SELECT r.*, u.username FROM recipes r LEFT JOIN users u ON r.created_by = u.id WHERE r.id=?",
        (recipe_id,),
    ).fetchone()
    comments = db.execute(
        "SELECT c.content, u.username FROM comments c LEFT JOIN users u ON c.user_id=u.id WHERE c.recipe_id=?",
        (recipe_id,),
    ).fetchall()
    return render_template("recipe_detail.html", recipe=recipe, comments=comments)


@app.route("/add", methods=["GET", "POST"])
def add_recipe():
    """
    Add a new recipe.
    """
    if "user_id" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        title = request.form["title"]
        description = request.form["description"]
        instructions = request.form["instructions"]

        db = get_db()
        db.execute(
            "INSERT INTO recipes (title, description, instructions, created_by) VALUES (?, ?, ?, ?)",
            (title, description, instructions, session["user_id"]),
        )
        db.commit()
        return redirect(url_for("index"))

    return render_template("add_recipe.html")


# -----------------------------
# MAIN ENTRY
# -----------------------------
if __name__ == "__main__":
    app.run(debug=True)
