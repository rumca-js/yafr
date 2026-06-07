from tests.dbtestcase import DbTestCase
from linkarchivetools.model import Entries
from main import app


class MainActionsTest(DbTestCase):
    def add_entry(self):
        json_data = {}
        json_data["link"] = "https://www.google.com"
        json_data["title"] = "Google"

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)
        return entry_id

    def test_entry_bookmark(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        self.assertTrue(entry_id)
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry-bookmark?id={entry_id}")

        # redirect
        self.assertEqual(response.status_code, 302)

    def test_entry_unbookmark(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        self.assertTrue(entry_id)
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry-unbookmark?id={entry_id}")

        self.assertEqual(response.status_code, 302)

    def test_entry_check_later(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.get(f"/entry-check-later?id={entry_id}")

        self.assertEqual(response.status_code, 200)

    def test_entry_vote(self):
        connection = self.initialize_database()

        entry_id = self.add_entry()
        connection.close()

        client = app.test_client()
        response = client.post(f"/entry-vote?id={entry_id}", data={"entry-vote": "1"})

        self.assertEqual(response.status_code, 200)
