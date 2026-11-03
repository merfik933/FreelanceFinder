import json

from db import db


def get_categories():
    return {category["id"]: category["name"] for category in sorted(
        db.get_records("categories"), key=lambda category: category["name"]
    )}

def _ensure_filters(connection, user_id):
    connection.execute(
        "INSERT INTO user_filters (user_id) VALUES (?) "
        "ON CONFLICT(user_id) DO NOTHING", (user_id,)
    )

def get_filters(user_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        row = connection.execute(
            "SELECT enabled, categories FROM user_filters WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return {"enabled": bool(row["enabled"]), "categories": json.loads(row["categories"])}

def toggle_enabled(user_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        connection.execute(
            "UPDATE user_filters SET enabled = 1 - enabled WHERE user_id = ?",
            (user_id,),
        )

def get_selected_categories(user_id):
    return get_filters(user_id)["categories"]

def toggle_category(user_id, category_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        row = connection.execute(
            "SELECT categories FROM user_filters WHERE user_id = ?", (user_id,)
        ).fetchone()
        categories = json.loads(row["categories"])
        if category_id in categories:
            categories.remove(category_id)
        else:
            if db.get_record("categories", category_id) is None:
                raise ValueError(f"Unknown category {category_id}")
            categories.append(category_id)
        connection.execute(
            "UPDATE user_filters SET categories = ? WHERE user_id = ?",
            (json.dumps(categories), user_id),
        )

def reset_categories(user_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        connection.execute(
            "UPDATE user_filters SET categories = '[]' WHERE user_id = ?", (user_id,)
        )

def is_project_allowed(project, user_id):
    filters = get_filters(user_id)
    if not filters["enabled"]:
        return True
    project_category_ids = {category["id"] for category in project["categories"]}
    return bool(project_category_ids & set(filters["categories"]))
