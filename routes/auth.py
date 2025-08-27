from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from auth import User

auth_bp = Blueprint("auth", __name__)  # Optional: use a blueprint for auth routes


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        user = User.find_by_username(username)
        if user and user.check_password(password):
            login_user(user)  # logs in the user and stores user_id in session
            flash("Logged in successfully!", "success")

            # Redirect to 'next' if it exists, otherwise homepage
            next_page = request.args.get("next")
            if next_page:
                return redirect(next_page)
            return redirect(url_for("index"))

        flash("Invalid username or password", "danger")

    return render_template("login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()  # Clears the session
    flash("You have been logged out.", "success")
    return redirect(url_for("index"))


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    next_url = request.args.get("next")  # capture `next` from query string

    if request.method == "POST":
        username = request.form.get("username").strip()  # type: ignore
        password = request.form.get("password")

        # Check if user already exists
        existing_user = User.find_by_username(username)
        if existing_user:
            flash("Username already taken. Please choose another.", "danger")
            return render_template("register.html", next=next_url)

        # Create new user
        new_user = User.create(username, password)
        login_user(new_user)

        # Redirect to next or index
        redirect_target = request.form.get("next") or url_for("index")
        return redirect(redirect_target)

    return render_template("register.html", next=next_url)
