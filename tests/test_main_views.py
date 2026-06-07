from linkarchivetools.model import SearchView

from tests.dbtestcase import DbTestCase
from main import app

class MainViewsTest(DbTestCase):
    def add_view(self):
        json_data = {}
        json_data["name"] = "Test View"
        json_data["default"] = True
        json_data["priority"] = 1
        json_data["filter_statement"] = ""
        json_data["order_by"] = ""

        controller = SearchView(connection=self.connection)
        view_id = controller.add()
        return view_id

    def test_view_edit_get(self):
        self.initialize_database()
        view_id = self.add_view()
        self.connection.close()

        client = app.test_client()
        response = client.get(f"/view-edit?id={view_id}")
        self.assertEqual(response.status_code, 200)

    def test_view_edit_post(self):
        self.initialize_database()
        view_id = self.add_view()
        self.connection.close()

        client = app.test_client()
        response = client.post(f"/view-edit?id={view_id}", data={
            "name": "Updated View",
            "default": "False",
            "priority": "2",
            "filter_statement": "test",
            "order_by": "id"
        })
        self.assertEqual(response.status_code, 200)

    def test_view_add_post(self):
        self.initialize_database()
        self.connection.close()

        client = app.test_client()
        response = client.post("/view-add")
        self.assertEqual(response.status_code, 200)

    def test_view_remove(self):
        self.initialize_database()
        view_id = self.add_view()
        self.connection.close()

        client = app.test_client()
        response = client.get(f"/view-remove?id={view_id}")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Remove view", response.data)

    def test_remove_all_views(self):
        self.initialize_database()
        self.add_view()
        self.connection.close()

        client = app.test_client()
        response = client.get("/remove-all-views")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Remove Search views OK", response.data)
