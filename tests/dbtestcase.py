import unittest
from pathlib import Path
import shutil
from sqlalchemy import create_engine

from linkarchivetools.model import DbConnection
from webtoolkit.tests import FakeInternetTestCase
from src.taskrunner import TaskRunner


class DbTestCase(FakeInternetTestCase):
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
