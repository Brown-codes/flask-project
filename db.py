import os
from typing import Optional, List, Dict
import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Database connection parameters
load_dotenv()
DB_HOST = os.getenv("DB_HOST", "postgresql-group10.alwaysdata.net")
DB_NAME = os.getenv("DB_NAME", "group10_recipe_db")
DB_USER = os.getenv("DB_USER", "group10")
DB_PASSWORD = os.getenv("DB_PASSWORD", "adamandevedeymad")
DB_PORT = os.getenv("DB_PORT", "5432")

# PostgreSQL connection string
DB_CONNECTION_STRING = f"host={DB_HOST} dbname={DB_NAME} user={DB_USER} password={DB_PASSWORD} port={DB_PORT}"


def get_db() -> psycopg2.extensions.connection:
    """Get a PostgreSQL database connection."""
    conn = psycopg2.connect(DB_CONNECTION_STRING, cursor_factory=DictCursor)
    return conn


def init_db() -> None:
    """Initialize the database and required tables."""
    conn = get_db()
    cur = conn.cursor()

    # Users table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
        );
        """
    )

    # Recipes table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS recipes (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            description TEXT,
            ingredients TEXT,
            instructions TEXT NOT NULL,
            image_data BYTEA,
            image_mime TEXT,
            created_by INTEGER,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id) ON DELETE SET NULL
        );
        """
    )

    # Comments table
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS comments (
            id SERIAL PRIMARY KEY,
            recipe_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (recipe_id) REFERENCES recipes (id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
        );
        """
    )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ Database initialized!")


def get_user(user_id: str) -> Optional[Dict]:
    """Fetch a user by ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def find_user_by_username(username: str) -> Optional[Dict]:
    """Fetch a user by username."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def create_user(username: str, password: str) -> int:
    """Create a new user and return the ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users (username, password) VALUES (%s, %s) RETURNING id",
        (username, password)
    )
    user_id: int = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return user_id


def create_recipe_db(
    title: str,
    description: Optional[str],
    ingredients: Optional[str],
    instructions: str,
    created_by: int,
    image_data: Optional[bytes] = None,
    image_mime: Optional[str] = None,
) -> int:
    """
    Insert a new recipe into the database.

    Args:
        title: Recipe title.
        description: Short description of the recipe.
        ingredients: Ingredients text (optional).
        instructions: Instructions for the recipe.
        created_by: User ID of the recipe creator.
        image_data: Optional image bytes.
        image_mime: Optional MIME type of the uploaded image.

    Returns:
        The ID of the newly created recipe.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO recipes (title, description, ingredients, instructions, created_by, image_data, image_mime)
        VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id
        """,
        (
            title,
            description,
            ingredients,
            instructions,
            created_by,
            image_data,
            image_mime,
        ),
    )
    recipe_id: int = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return recipe_id


def get_recipes(user_id: Optional[int] = None) -> List[Dict]:
    """
    Fetch recipes. If user_id is provided, fetch recipes created by that user only.

    Returns:
        List of recipes as dictionaries.
    """
    conn = get_db()
    cur = conn.cursor()

    if user_id is not None:
        cur.execute(
            "SELECT * FROM recipes WHERE created_by = %s ORDER BY created_at DESC",
            (user_id,)
        )
    else:
        cur.execute("SELECT * FROM recipes ORDER BY created_at DESC")

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]


def get_recipe_by_id(recipe_id: int) -> Optional[Dict]:
    """
    Fetch a single recipe by ID.
    Returns a dict or None if not found.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.*, u.username as author_name
        FROM recipes r
        LEFT JOIN users u ON r.created_by = u.id
        WHERE r.id = %s
        """,
        (recipe_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    return dict(row) if row else None


def get_comments_for_recipe(recipe_id: int) -> List[Dict]:
    """
    Fetch all comments for a given recipe, including author name.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT c.*, u.username AS author_name
        FROM comments c
        LEFT JOIN users u ON c.user_id = u.id
        WHERE c.recipe_id = %s
        ORDER BY c.id ASC
        """,
        (recipe_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]


def create_comment_db(recipe_id: int, user_id: int, body: str) -> int:
    """
    Insert a new comment for a recipe.
    Returns the comment ID.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO comments (recipe_id, user_id, content)
        VALUES (%s, %s, %s) RETURNING id
        """,
        (recipe_id, user_id, body)
    )
    comment_id: int = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()
    return comment_id


def update_recipe(
    recipe_id: int,
    title: str,
    description: Optional[str],
    ingredients: Optional[str],
    instructions: str,
    image_data: Optional[bytes] = None,
    image_mime: Optional[str] = None,
) -> None:
    """Update an existing recipe with optional image replacement."""
    conn = get_db()
    cur = conn.cursor()

    if image_data is not None:
        cur.execute(
            """
            UPDATE recipes
            SET title = %s, description = %s, ingredients = %s, instructions = %s, image_data = %s, image_mime = %s
            WHERE id = %s
            """,
            (
                title,
                description,
                ingredients,
                instructions,
                image_data,
                image_mime,
                recipe_id,
            ),
        )
    else:
        cur.execute(
            """
            UPDATE recipes
            SET title = %s, description = %s, ingredients = %s, instructions = %s
            WHERE id = %s
            """,
            (title, description, ingredients, instructions, recipe_id),
        )

    conn.commit()
    cur.close()
    conn.close()


def delete_recipe_by_id(recipe_id: int) -> None:
    """Delete a recipe and all its comments."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM recipes WHERE id = %s", (recipe_id,))
    conn.commit()
    cur.close()
    conn.close()


def get_recipes_by_user(user_id: int) -> List[Dict]:
    """Fetch all recipes created by a given user ID."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT r.*, u.username AS author_name
        FROM recipes r
        LEFT JOIN users u ON r.created_by = u.id
        WHERE r.created_by = %s
        ORDER BY r.created_at DESC
        """,
        (user_id,)
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [dict(row) for row in rows]