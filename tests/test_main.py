from tests.dbtestcase import DbTestCase
from linkarchivetools.model.entryrules import EntryRules
from main import app


class MainTest(DbTestCase):
    def test_api_status(self):
        connection = self.create_db_connection("test.db")
        connection.entry_rules.truncate()

        client = app.test_client()
        response = client.get("/api/status")
        self.assertEqual(response.status_code, 200)

    def test_api_stats(self):
        connection = self.create_db_connection("test.db")
        connection.entry_rules.truncate()

        client = app.test_client()
        response = client.get("/api/stats")
        self.assertEqual(response.status_code, 200)
