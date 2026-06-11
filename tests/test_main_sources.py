from tests.dbtestcase import DbTestCase
from linkarchivetools.model import Sources
from main import app


class MainSourcesTest(DbTestCase):
    def add_source(self):
        controller = Sources(connection=self.connection)
        source_id = controller.set(source_url="https://www.google.com")
        return source_id

    def test_source_fetch(self):
        connection = self.initialize_database()

        source_id = self.add_source()
        connection.close()

        client = app.test_client()
        response = client.get(f"/source-fetch?id={source_id}")

        self.assertEqual(response.status_code, 200)
