from pathlib import Path
from datetime import datetime, timedelta


class System(object):
    instance = None

    def __init__(self):
        self.set_thread_ok()
        self.crawling_server = True

    def get_object():
        if System.instance is None:
            System.instance = System()
        return System.instance

    def set_thread_ok(self):
        self.thread_date = datetime.now()

    def set_crawling_server_fail(self):
        self.crawling_server = False

    def set_crawling_server_ok(self):
        self.crawling_server = True

    def is_system_ok(self):
        return self.is_read_thread_ok()

    def is_read_thread_ok(self):
        if self.thread_date:
            return datetime.now() - self.thread_date < timedelta(minutes=5)

    def get_indicators(self):
        data = {}

        data["threads_error"] = {}
        data["threads_error"]["message"] = ""
        data["threads_error"]["status"] = not self.is_read_thread_ok()

        data["crawling_server_error"] = {}
        data["crawling_server_error"]["message"] = ""
        data["crawling_server_error"]["status"] = not self.crawling_server

        return data

    def get_export_dir(self):
        """
        TODO url to file name
        """
        return Path("export")

