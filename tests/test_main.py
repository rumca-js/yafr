from tests.dbtestcase import DbTestCase
from linkarchivetools.model import (
   EntryRules,
   Entries,
)
from main import app


class MainTest(DbTestCase):
    def add_entry(self):
        json_data = {}
        json_data["link"] = "https://www.google.com"
        json_data["title"] = "Google"

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)
        return entry_id

    def test_api_status(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()
        connection.close()

        client = app.test_client()
        response = client.get("/api/status")

        self.assertEqual(response.status_code, 200)

    def test_api_stats(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()
        connection.close()

        client = app.test_client()
        response = client.get("/api/stats")

        self.assertEqual(response.status_code, 200)

    def test_api_entries(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get("/api/entries")

        self.assertEqual(response.status_code, 200)

    def test_entry_bookmark(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()

        entry_id = self.add_entry()
        self.assertTrue(entry_id)
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry-bookmark?id={entry_id}")

        # redirect
        self.assertEqual(response.status_code, 302)

    def test_entry_unbookmark(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()

        entry_id = self.add_entry()
        self.assertTrue(entry_id)
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry-unbookmark?id={entry_id}")

        self.assertEqual(response.status_code, 302)

