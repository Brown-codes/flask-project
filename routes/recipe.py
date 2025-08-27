from typing import Optional
from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    abort,
)
from flask_login import login_required, current_user
import db

# from db import create_recipe_db, get_recipe_by_id  # We'll need this helper function

recipes_bp = Blueprint("recipes", __name__, url_prefix="/recipes")


@recipes_bp.route("/<int:recipe_id>/img")
def recipe_image(recipe_id: int):
    """
    Serve the image for a recipe by ID.
    Returns a 404 if no image exists.
    """
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe or not recipe.get("image_data"):
        abort(404)  # No recipe or no image

    image_data = recipe["image_data"]
    image_mime = recipe.get("image_mime") or "application/octet-stream"

    return Response(image_data, mimetype=image_mime)


@recipes_bp.route("/<int:recipe_id>", methods=["GET", "POST"])
def recipe_detail(recipe_id: int):
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for("index"))

    comments = db.get_comments_for_recipe(recipe_id)

    import logging

    logging.warning(
        f"UserId:{getattr(current_user, 'id', None)} RecipeId:{recipe.get('created_by')}"
    )

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("You must be logged in to comment.", "danger")
            return redirect(url_for("auth.login"))

        comment_body = request.form.get("comment")
        if comment_body:
            db.create_comment_db(
                recipe_id=recipe_id, user_id=int(current_user.id), body=comment_body
            )
            flash("Comment posted!", "success")
            return redirect(url_for("recipes.recipe_detail", recipe_id=recipe_id))

    return render_template(
        "recipe_detail.html",
        recipe=recipe,
        comments=comments,
        user=current_user if current_user.is_authenticated else None,
    )


@recipes_bp.route("/create", methods=["GET", "POST"])
@login_required
def create_recipe():
    if request.method == "POST":
        # Get form data with proper types
        title: Optional[str] = request.form.get("title")
        description: Optional[str] = request.form.get("description")
        ingredients: Optional[str] = request.form.get("ingredients")
        instructions: Optional[str] = request.form.get("instructions")
        image_file = request.files.get("image")

        # Validate required fields
        if not title or not instructions:
            flash("Title and instructions are required.", "danger")
            return render_template("create_recipe.html")

        image_data: Optional[bytes] = None
        image_mime: Optional[str] = None
        if image_file and image_file.filename:
            image_data = image_file.read()
            image_mime = image_file.mimetype

        db.create_recipe_db(
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            created_by=int(current_user.id),
            image_data=image_data,
            image_mime=image_mime,
        )

        flash("Recipe published successfully!", "success")
        return redirect(url_for("index"))

    return render_template("create_recipe.html")


@recipes_bp.route("/<int:recipe_id>/edit", methods=["GET", "POST"])
@login_required
def edit_recipe(recipe_id: int):
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for("index"))

    # Only the author can edit
    if int(recipe["created_by"]) != int(current_user.id):
        flash("You are not allowed to edit this recipe.", "danger")
        return redirect(url_for("recipes.recipe_detail", recipe_id=recipe_id))

    # Handle POST
    if request.method == "POST":
        title = request.form.get("title")
        description = request.form.get("description")
        ingredients = request.form.get("ingredients")
        instructions = request.form.get("instructions")
        remove_image = request.form.get("remove_image")
        image_file = request.files.get("image")

        if not title or not instructions:
            flash("Title and instructions are required.", "danger")
            return redirect(url_for("recipes.edit_recipe", recipe_id=recipe_id))

        image_data = None
        image_mime = None
        if remove_image:
            image_data = b""
            image_mime = None
        elif image_file and image_file.filename:
            image_data = image_file.read()
            image_mime = image_file.mimetype

        db.update_recipe(
            recipe_id=recipe_id,
            title=title,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            image_data=image_data,
            image_mime=image_mime,
        )

        flash("Recipe updated successfully!", "success")
        return redirect(url_for("recipes.recipe_detail", recipe_id=recipe_id))

    # GET request
    image_data = None
    if recipe.get("image_data"):
        image_data = url_for("recipes.recipe_image", recipe_id=recipe["id"])

    return render_template("edit_recipe.html", recipe=recipe, image_data=image_data)


@recipes_bp.route("/<int:recipe_id>/delete", methods=["POST"])
@login_required
def delete_recipe(recipe_id: int):
    """Delete a recipe. Only the author can delete it."""
    recipe = db.get_recipe_by_id(recipe_id)
    if not recipe:
        flash("Recipe not found.", "danger")
        return redirect(url_for("index"))

    # Ensure the current user is the author
    if int(current_user.id) != int(recipe["created_by"]):
        abort(403)  # Forbidden

    db.delete_recipe_by_id(recipe_id)
    flash("Recipe deleted successfully!", "success")
    return redirect(url_for("index"))
