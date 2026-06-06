from tests.dbtestcase import DbTestCase
from linkarchivetools.model import Entries
from main import app


class MainUiTest(DbTestCase):
    def add_entry(self):
        json_data = {}
        json_data["link"] = "https://www.google.com"
        json_data["title"] = "Google"

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)
        return entry_id

    def test_root_redirect(self):
        client = app.test_client()
        response = client.get("/")
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.headers["Location"].endswith("/search"))

    def test_search_page(self):
        self.create_db_connection("test.db")
        self.connection.close()
        client = app.test_client()
        response = client.get("/search")
        self.assertEqual(response.status_code, 200)

    def test_sources_page(self):
        self.create_db_connection("test.db")
        self.connection.close()
        client = app.test_client()
        response = client.get("/sources")
        self.assertEqual(response.status_code, 200)

    def test_entry_page(self):
        connection = self.create_db_connection("test.db")
        connection.truncate()
        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry?id={entry_id}")
        self.assertEqual(response.status_code, 200)

    def test_status_page(self):
        self.create_db_connection("test.db")
        self.connection.close()
        client = app.test_client()
        response = client.get("/status")
        self.assertEqual(response.status_code, 200)

    def test_admin_page(self):
        self.create_db_connection("test.db")
        self.connection.close()
        client = app.test_client()
        response = client.get("/admin")
        self.assertEqual(response.status_code, 200)
