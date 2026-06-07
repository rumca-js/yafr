import unittest
from pathlib import Path
import shutil
from sqlalchemy import create_engine
from main import app

from linkarchivetools.model import (
   DbConnection,
   ConfigurationEntry,
)
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

        wal_path = Path(f"{file_name}-wal")
        if wal_path.exists():
            wal_path.unlink()

        shm_path = Path(f"{file_name}-shm")
        if shm_path.exists():
            shm_path.unlink()

        app.config["DB_FILE"] = file_name
        shutil.copy("data/input.db", file_name)

        self.connection = DbConnection(file_name)
        return self.connection

    def use_remote_server(self, connection):
        from src.controller import Controller
        controller = Controller(connection)

        config_id = controller.add_configuration()

        config = ConfigurationEntry(self.connection).get()
        controller.update_configuration(config)

        json_data = {}
        json_data["remote_webtools_server_location"] = "https://0.0.0.0"
        json_data["initialized"] = True
        connection.configurationentry.update_json_data(id=config_id, json_data=json_data)

    def initialize_database(self):
        self.database_name = "test.db"
        self.connection = self.create_db_connection(self.database_name)

        self.connection.configurationentry.truncate()
        self.connection.backgroundjob.truncate()
        self.connection.entry_rules.truncate()
        self.connection.sources_table.truncate()
        self.connection.entries_table.truncate()
        self.connection.socialdata.truncate()
        self.connection.sourceoperationaldata.truncate()

        self.use_remote_server(self.connection)

        return self.connection
