import json
import configparser
from pathlib import Path

config = configparser.ConfigParser()
config.read("config.ini")
tags_file_path = config.get("Files", "tags")

with open(tags_file_path, encoding="utf-8") as file:
    TAGS = json.load(file)

categories_file_path = config.get(
    "Files", "categories", fallback=str(Path(tags_file_path).with_name("categories.json"))
)
with open(categories_file_path, encoding="utf-8") as file:
    CATEGORIES = json.load(file)


def get_project_categories(project):
    return _get_matches(project, CATEGORIES)


def get_project_tags(project):
    return _get_matches(project, TAGS)


def _get_matches(project, rules):
    category_ids = {category["id"] for category in project.get("categories", [])}
    text = " ".join(
        (project.get(field) or "")
        for field in ("name", "description")
    ).casefold()
    matches = []
    for tag in rules.values():
        if category_ids.intersection(tag.get("source_skill_ids", [])) or any(
            rule.casefold() in text for rule in tag["rules"] if rule.strip()
        ):
            if tag["name"] not in matches:
                matches.append(tag["name"])
    return matches

if __name__ == "__main__":
    # Example usage
    project = {"name": "Треба витягнути дизайн зразка особистого кабінету з APK застосунків, на яких складна реєстрація"}
    tags = get_project_tags(project)
    categories = get_project_categories(project)
    print(f"Project: {project['name']}")
    print(f"Tags: {tags}")
    print(f"Categories: {categories}")
