import json
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
tags_file_path = config.get("Files", "tags")

with open(tags_file_path, encoding="utf-8") as file:
    TAGS = json.load(file)

def get_project_tags(project):
    category_ids = {category["id"] for category in project.get("categories", [])}
    text = " ".join(
        (project.get(field) or "")
        for field in ("name", "description")
    ).casefold()
    tags = []
    for tag in TAGS.values():
        if category_ids.intersection(tag.get("source_skill_ids", [])) or any(
            phrase.casefold() in text for phrase in tag["phrase_codes"] if phrase.strip()
        ):
            if tag["name"] not in tags:
                tags.append(tag["name"])
    return tags

if __name__ == "__main__":
    # Example usage
    project = {"name": "Треба витягнути дизайн зразка особистого кабінету з APK застосунків, на яких складна реєстрація"}
    tags = get_project_tags(project)
    print(f"Project: {project['name']}")
    print(f"Tags: {tags}")
