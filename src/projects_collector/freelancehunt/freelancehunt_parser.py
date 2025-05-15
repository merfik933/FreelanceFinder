import requests

from ..base_parser import BaseParser
from pathlib import Path

LAST_PROJECT_ID_PATH = Path(__file__).parent / "last_project_id.txt"

class FreelanceHuntParser(BaseParser):
    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.freelancehunt.com/v2/projects"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Authorization": f"Bearer {self.token}"
        }
        self.requests_interval = 5  # seconds

        if LAST_PROJECT_ID_PATH.exists():
            with open(LAST_PROJECT_ID_PATH, "r") as f:
                self.last_project_id = int(f.read().strip())
        else:
            self.last_project_id = 0
        

    def fetch_new_projects(self) -> list[dict]:
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            projects = response.json().get("data", [])
            new_projects = [p for p in projects if p["id"] > self.last_project_id]
            if new_projects:
                self.last_project_id = max(p["id"] for p in new_projects)
                self._save_state()

                new_projects = [self._format_project(p) for p in new_projects]
                new_projects.reverse()
                
            return new_projects
        else:
            print(f"Error fetching projects: {response.status_code}")
            return []
        
    def _save_state(self):
        with open(LAST_PROJECT_ID_PATH, "w") as f:
            f.write(str(self.last_project_id))
        
    def _format_project(self, project: dict) -> dict:
        attrs = project["attributes"]
        return {
            "id": project["id"],
            "title": attrs["name"],
            "description": attrs["description"],
            "url": project["links"]["self"]["web"],
            "skills": [s["name"] for s in attrs.get("skills", [])],
            "budget": {
                "amount": attrs.get("budget")["amount"] if attrs.get("budget") else None,
                "currency": attrs.get("budget")["currency"] if attrs.get("budget") else None,
            },
            "source": "freelancehunt",
            "published_at": attrs["published_at"],
        }