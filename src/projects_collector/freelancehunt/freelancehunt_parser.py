import requests

from ..base_parser import BaseParser
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
import time

from db import db

class FreelanceHuntParser(BaseParser):
    def __init__(self, token: str):
        self.token = token
        self.url = "https://api.freelancehunt.com/v2/projects"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
            "Accept-Language": "uk",
            "Authorization": f"Bearer {self.token}"
        }
        self.requests_interval = 5

    def fetch_new_projects(self) -> list[dict]:
        last_project = db.get_record("projects", -1, source="freelancehunt")
        last_project_id = last_project["external_id"] if last_project else 0
        now = datetime.now(timezone.utc)
        cutoff = (
            now - timedelta(days=3) if last_project_id else
            now.astimezone(ZoneInfo("Europe/Warsaw")).replace(
                hour=0, minute=0, second=0, microsecond=0
            )
        )

        url = self.url
        new_projects = {}
        page = 0
        while url:
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            payload = response.json()
            projects = payload.get("data", [])
            page += 1
            reached_boundary = False
            for project in projects:
                project_id = int(project["id"])
                published = datetime.fromisoformat(project["attributes"]["published_at"])
                if project_id <= last_project_id or published < cutoff:
                    reached_boundary = True
                    continue
                new_projects[project_id] = project
            print(f"Freelancehunt: page {page}, collected {len(new_projects)} new projects", flush=True)
            if reached_boundary or not projects:
                break
            url = payload.get("links", {}).get("next")
            if url:
                time.sleep(self.requests_interval)
        return [self._format_project(new_projects[key]) for key in sorted(new_projects)]
        
    def _format_project(self, project: dict) -> dict:
        attrs = project["attributes"]
        return {
            "external_id": project["id"],
            "name": attrs["name"],
            "description": attrs["description"],
            "url": project["links"]["self"]["web"],
            "project_skills": [skill["id"] for skill in attrs.get("skills", [])],
            "budget_amount": attrs.get("budget")["amount"] if attrs.get("budget") else None,
            "budget_currency": attrs.get("budget")["currency"] if attrs.get("budget") else None,
            "source": "freelancehunt",
            "published_at": int(datetime.fromisoformat(attrs["published_at"]).timestamp()),
        }
