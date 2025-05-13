from abc import ABC, abstractmethod

class BaseParser(ABC):
    @abstractmethod
    def fetch_new_projects(self) -> list[dict]:
        """Get new projects from the freelance platform."""
        pass