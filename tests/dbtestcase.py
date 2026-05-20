import unittest
from pathlib import Path
import shutil
from sqlalchemy import create_engine

from linkarchivetools.model import DbConnection


class DbTestCase(unittest.TestCase):
    def create_db_connection(self, file_name):
        path = Path(file_name)
        if path.exists():
            path.unlink()

        shutil.copy("data/input.db", file_name)

        return DbConnection(file_name)
