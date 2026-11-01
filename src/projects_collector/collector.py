import threading
import time

from db import db

class ParserWorker(threading.Thread):
    def __init__(self, parser, callback):
        super().__init__(daemon=True)
        self.parser = parser
        self.callback = callback
        self.interval = parser.requests_interval

    def run(self):
        while True:
            try:
                print(f"{type(self.parser).__name__}: checking for new projects", flush=True)
                new_projects = self.parser.fetch_new_projects()
                if new_projects:
                    ids = db.add_records("projects", new_projects)
                    print(f"Saved {len(ids)} projects to database", flush=True)

                    for id in ids:
                        self.callback(id)
            except Exception as e:
                print(f"Error in parser worker: {e}", flush=True)

            time.sleep(self.interval)

class Collector:
    def __init__(self, parsers: list, on_new_project: callable):
        self.parsers = parsers
        self.callback = on_new_project

    def run(self):
        for parser in self.parsers:
            worker = ParserWorker(parser, self.callback)
            worker.start()

