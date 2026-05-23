import unittest
from pathlib import Path
import shutil
from sqlalchemy import create_engine

from linkarchivetools.model import DbConnection
from webtoolkit.tests import FakeInternetTestCase
from src.taskrunner import TaskRunner


class DbTestCase(FakeInternetTestCase):
    def disable_web_pages(self):
        super().disable_web_pages()
        self.use_remote_server(self.connection)

    def create_db_connection(self, file_name):
        path = Path(file_name)
        if path.exists():
            path.unlink()

        shutil.copy("data/input.db", file_name)

        return DbConnection(file_name)

    def use_remote_server(self, connection):
        runner = TaskRunner("table")
        runner.connection = connection

        config_id = runner.add_configuration()

        json_data = {}
        json_data["remote_webtools_server_location"] = "https://0.0.0.0"
        connection.configurationentry.update_json_data(id=config_id, json_data=json_data)

    def initialize_database(self):
        self.database_name = "test.db"
        self.connection = self.create_db_connection(self.database_name)

        self.connection.configurationentry.truncate()
        self.connection.backgroundjob.truncate()
        self.connection.entry_rules.truncate()
        self.connection.sources_table.truncate()
        self.connection.entries_table.truncate()

        self.use_remote_server(self.connection)

        return self.connection
