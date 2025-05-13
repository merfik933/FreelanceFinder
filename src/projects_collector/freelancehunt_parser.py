import requests
import json

from .base_parser import BaseParser

class FreelanceHuntParser(BaseParser):
    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.freelancehunt.com/v2/projects"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Authorization": f"Bearer {self.token}"
        }
        self.requests_interval = 5  # seconds

        try:
            with open("src\\state\\freelancehunt_state.json", "r") as f:
                state = json.load(f)
                self.last_project_id = state.get("last_project_id", 0)
        except FileNotFoundError:
            self.last_project_id = 0
        

    def fetch_new_projects(self) -> list[dict]:
        response = requests.get(self.url, headers=self.headers)
        if response.status_code == 200:
            projects = response.json().get("data", [])
            new_projects = [p for p in projects if p["id"] > self.last_project_id]
            if new_projects:
                self.last_project_id = max(p["id"] for p in new_projects)
                with open("src\\state\\freelancehunt_state.json", "w") as f:
                    json.dump({"last_project_id": self.last_project_id}, f)

                new_projects = [self._format_project(p) for p in new_projects]

            return new_projects
        else:
            print(f"Error fetching projects: {response.status_code}")
            return []
        
    def _format_project(self, p: dict) -> dict:
        attrs = p["attributes"]
        return {
            "id": p["id"],
            "title": attrs["name"],
            "description": attrs["description"],
            "url": p["links"]["self"]["web"],
            "skills": [s["name"] for s in attrs.get("skills", [])],
            "budget": {
                "amount": attrs.get("budget")["amount"] if attrs.get("budget") else None,
                "currency": attrs.get("budget")["currency"] if attrs.get("budget") else None,
            },
            "source": "freelancehunt",
            "published_at": attrs["published_at"],
        }