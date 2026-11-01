import json

from db import db


class FilterManager:
    @property
    def skills(self):
        return {skill["id"]: skill["name"] for skill in sorted(
            db.get_records("skills"), key=lambda skill: skill["name"]
        )}

    def _ensure_filters(self, connection, user_id):
        connection.execute(
            "INSERT INTO user_filters (user_id) VALUES (?) "
            "ON CONFLICT(user_id) DO NOTHING", (user_id,)
        )

    def get_filters(self, user_id):
        with db.connect() as connection:
            self._ensure_filters(connection, user_id)
            row = connection.execute(
                "SELECT enabled, skills FROM user_filters WHERE user_id = ?",
                (user_id,),
            ).fetchone()
            return {"enabled": bool(row["enabled"]), "skills": json.loads(row["skills"])}

    def toggle_enabled(self, user_id):
        with db.connect() as connection:
            self._ensure_filters(connection, user_id)
            connection.execute(
                "UPDATE user_filters SET enabled = 1 - enabled WHERE user_id = ?",
                (user_id,),
            )

    def get_selected_skills(self, user_id):
        return self.get_filters(user_id)["skills"]

    def toggle_skill(self, user_id, skill_id):
        with db.connect() as connection:
            self._ensure_filters(connection, user_id)
            row = connection.execute(
                "SELECT skills FROM user_filters WHERE user_id = ?", (user_id,)
            ).fetchone()
            skills = json.loads(row["skills"])
            if skill_id in skills:
                skills.remove(skill_id)
            else:
                if db.get_record("skills", skill_id) is None:
                    raise ValueError(f"Unknown skill {skill_id}")
                skills.append(skill_id)
            connection.execute(
                "UPDATE user_filters SET skills = ? WHERE user_id = ?",
                (json.dumps(skills), user_id),
            )

    def reset_skills(self, user_id):
        with db.connect() as connection:
            self._ensure_filters(connection, user_id)
            connection.execute(
                "UPDATE user_filters SET skills = '[]' WHERE user_id = ?", (user_id,)
            )

    def is_project_allowed(self, project, user_id):
        filters = self.get_filters(user_id)
        if not filters["enabled"]:
            return True
        project_skill_ids = {skill["id"] for skill in project["skills"]}
        return bool(project_skill_ids & set(filters["skills"]))
