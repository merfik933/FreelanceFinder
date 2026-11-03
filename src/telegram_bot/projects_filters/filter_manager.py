import json

from db import db


def get_source_categories():
    return {source_category["id"]: source_category["name"] for source_category in sorted(
        db.get_records("source_categories"), key=lambda source_category: source_category["name"]
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
            "SELECT enabled, source_categories FROM user_filters WHERE user_id = ?",
            (user_id,),
        ).fetchone()
        return {"enabled": bool(row["enabled"]), "source_categories": json.loads(row["source_categories"])}

def toggle_enabled(user_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        connection.execute(
            "UPDATE user_filters SET enabled = 1 - enabled WHERE user_id = ?",
            (user_id,),
        )

def get_selected_source_categories(user_id):
    return get_filters(user_id)["source_categories"]

def toggle_source_category(user_id, source_category_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        row = connection.execute(
            "SELECT source_categories FROM user_filters WHERE user_id = ?", (user_id,)
        ).fetchone()
        source_categories = json.loads(row["source_categories"])
        if source_category_id in source_categories:
            source_categories.remove(source_category_id)
        else:
            if db.get_record("source_categories", source_category_id) is None:
                raise ValueError(f"Unknown source category {source_category_id}")
            source_categories.append(source_category_id)
        connection.execute(
            "UPDATE user_filters SET source_categories = ? WHERE user_id = ?",
            (json.dumps(source_categories), user_id),
        )

def reset_source_categories(user_id):
    with db.connect() as connection:
        _ensure_filters(connection, user_id)
        connection.execute(
            "UPDATE user_filters SET source_categories = '[]' WHERE user_id = ?", (user_id,)
        )

def is_project_allowed(project, user_id):
    filters = get_filters(user_id)
    if not filters["enabled"]:
        return True
    project_source_category_ids = {source_category["id"] for source_category in project["source_categories"]}
    return bool(project_source_category_ids & set(filters["source_categories"]))
