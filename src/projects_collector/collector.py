import threading
import time

class ParserWorker(threading.Thread):
    def __init__(self, parser, callback):
        super().__init__(daemon=True)
        self.parser = parser
        self.callback = callback
        self.interval = parser.requests_interval

    def run(self):
        while True:
            try:
                new_projects = self.parser.fetch_new_projects()
                if new_projects:
                    for project in new_projects:
                        self.callback(project)
            except Exception as e:
                print(f"Error in parser worker: {e}")

            time.sleep(self.interval)

class Collector:
    def __init__(self, parsers: list, on_new_project: callable):
        self.parsers = parsers
        self.callback = on_new_project

    def run(self):
        for parser in self.parsers:
            worker = ParserWorker(parser, self.callback)
            worker.start()
                