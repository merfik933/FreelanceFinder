import requests

from ..base_parser import BaseParser
from pathlib import Path
from datetime import datetime, timedelta, timezone
import time

LAST_PROJECT_ID_PATH = Path(__file__).parent / "last_project_id.txt"

class FreelanceHuntParser(BaseParser):
    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.freelancehunt.com/v2/projects"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept-Language": "uk",
            "Authorization": f"Bearer {self.token}"
        }
        self.requests_interval = 5  # seconds

        if LAST_PROJECT_ID_PATH.exists():
            with open(LAST_PROJECT_ID_PATH, "r") as f:
                self.last_project_id = int(f.read().strip())
        else:
            self.last_project_id = 0
        

    def fetch_new_projects(self) -> list[dict]:
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        url = self.url
        new_projects = {}
        while url:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            projects = payload.get("data", [])
            reached_boundary = False
            for project in projects:
                published = datetime.fromisoformat(project["attributes"]["published_at"])
                if project["id"] <= self.last_project_id or published < cutoff:
                    reached_boundary = True
                    continue
                new_projects[project["id"]] = project
            if reached_boundary or not projects:
                break
            url = payload.get("links", {}).get("next")
            if url:
                time.sleep(self.requests_interval)
        return [self._format_project(new_projects[key]) for key in sorted(new_projects)]

    def acknowledge_project(self, project: dict):
        self.last_project_id = max(self.last_project_id, project["id"])
        self._save_state()
        
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
            "skills": attrs.get("skills", []),
            "budget": {
                "amount": attrs.get("budget")["amount"] if attrs.get("budget") else None,
                "currency": attrs.get("budget")["currency"] if attrs.get("budget") else None,
            },
            "source": "freelancehunt",
            "published_at": attrs["published_at"],
        }
