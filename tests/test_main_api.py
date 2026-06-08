from tests.dbtestcase import DbTestCase
from linkarchivetools.model import (
   Entries,
   SearchView,
)
from main import app


class MainApiTest(DbTestCase):
    def add_entry(self):
        json_data = {}
        json_data["link"] = "https://www.google.com"
        json_data["title"] = "Google"

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)
        return entry_id

    def test_api_status(self):
        connection = self.initialize_database()
        connection.close()

        client = app.test_client()
        response = client.get("/api/status")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_stats(self):
        connection = self.initialize_database()
        connection.close()

        client = app.test_client()
        response = client.get("/api/stats")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_entries(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get("/api/entries")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(len(data["entries"]), 1)

    def test_api_entry(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get(f"/api/entry?id={entry_id}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertEqual(data["id"], entry_id)

    def test_api_sources(self):
        connection = self.initialize_database()
        connection.close()

        client = app.test_client()
        response = client.get("/api/sources")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertIn("sources", data)

    def test_api_entry_visit(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get(f"/api/entry-visit?id={entry_id}")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
        data = response.get_json()
        self.assertTrue(data["status"])

    def test_api_views__empty(self):
        connection = self.initialize_database()
        connection.close()

        client = app.test_client()
        response = client.get("/api/views")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)

    def test_api_views__not_empty(self):
        connection = self.initialize_database()

        views = SearchView(connection = connection)
        view_id = views.add()
        view = views.get(id=view_id)

        connection.close()

        client = app.test_client()
        response = client.get("/api/views")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.is_json)
