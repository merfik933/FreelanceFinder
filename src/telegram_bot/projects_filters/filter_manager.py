import json
from pathlib import Path
from enum import Enum
from db import db

FILTERS_PATH = Path(__file__).parent / "filters.json"

class FilterMode(str, Enum):
    ALL = "all"
    WHITELIST = "whitelist"
    BLACKLIST = "blacklist"

class FilterManager:
    def __init__(self):
        self.filters = self._load_filters()
        self.skills = self._load_skills()

    def _load_filters(self):
        if FILTERS_PATH.exists():
            with open(FILTERS_PATH, "r", encoding="utf-8") as f:
                filters = json.load(f)
        else:
            print("Filters file not found. Creating default filters.")
            filters = {
                "mode": FilterMode.ALL,
                "skills": [],
            }

        return filters

    def _save_filters(self):
        with open(FILTERS_PATH, "w", encoding="utf-8") as f:
            json.dump(self.filters, f, ensure_ascii=False, indent=4)

    def _load_skills(self):
        return {skill["id"]: skill["name"] for skill in sorted(
            db.get_records("skills"), key=lambda skill: skill["name"]
        )}

    def get_filter_mode(self):
        return self.filters["mode"]
    
    def toggle_filter_mode(self):
        modes = list(FilterMode)
        current = FilterMode(self.filters["mode"])
        next_index = (modes.index(current) + 1) % len(modes)
        self.filters["mode"] = modes[next_index].value
        self._save_filters()

    def get_selected_skills(self):
        return self.filters["skills"]

    def add_skill(self, skill_id: int):
        if skill_id not in self.filters["skills"]:
            self.filters["skills"].append(skill_id)
            self._save_filters()

    def remove_skill(self, skill_id: int):
        if skill_id in self.filters["skills"]:
            self.filters["skills"].remove(skill_id)
            self._save_filters()

    def is_project_allowed(self, project: dict) -> bool:
        project_skill_ids = {skill["id"] for skill in project["skills"]}

        selected_skills = set(self.filters["skills"])
        mode = FilterMode(self.filters["mode"])

        if mode == FilterMode.ALL:
            return True
        elif mode == FilterMode.WHITELIST:
            return bool(project_skill_ids & selected_skills)
        elif mode == FilterMode.BLACKLIST:
            return not bool(project_skill_ids & selected_skills)

