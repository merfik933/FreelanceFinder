import json
import configparser

config = configparser.ConfigParser()
config.read("config.ini")
tags_file_path = config.get("Files", "tags")

with open(tags_file_path, encoding="utf-8") as file:
    TAGS = json.load(file)

def get_project_tag(project):
    text = (project.get("name") or "").casefold()
    for tag in TAGS.values():
        if any(phrase.casefold() in text for phrase in tag["phrase_codes"] if phrase.strip()):
            return tag["name"]
    return None

if __name__ == "__main__":
    # Example usage
    project = {"name": "Треба витягнути дизайн зразка особистого кабінету з APK застосунків, на яких складна реєстрація"}
    tag = get_project_tag(project)
    print(f"Project: {project['name']}")
    print(f"Tag: {tag}")
