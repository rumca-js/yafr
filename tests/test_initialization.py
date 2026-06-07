from tests.dbtestcase import DbTestCase
from main import app
from linkarchivetools.model import ConfigurationEntry

class InitializationWizardTest(DbTestCase):
    def test_initialization_wizard_get(self):
        self.create_db_connection("test_init_get.db")
        client = app.test_client()
        response = client.get("/initialization-wizard")
        self.assertEqual(response.status_code, 200)
        self.assertIn(b"Initialization Wizard", response.data)
        self.connection.close()

    def test_initialization_wizard_post(self):
        connection = self.create_db_connection("test_init_post.db")
        # Ensure it's clean
        connection.configurationentry.truncate()
        
        client = app.test_client()
        response = client.post("/initialization-wizard", data={
            "initialization_type": "rss_reader",
            "display_type": "accordion"
        })
        
        self.assertEqual(response.status_code, 302) # Redirect to search
        
        # Verify DB
        config = connection.configurationentry.get_first()
        self.assertIsNotNone(config)
        self.assertTrue(config.initialized)
        self.assertEqual(config.initialization_type, "rss_reader")
        self.assertEqual(config.display_type, "accordion")
        self.connection.close()

    def test_initialization_wizard_post_existing(self):
        connection = self.create_db_connection("test_init_existing.db")
        # Ensure it exists but not initialized
        from src.controller import Controller
        Controller(connection).add_configuration()

        client = app.test_client()

        response = client.post("/initialization-wizard", data={
            "initialization_type": "search_engine",
            "display_type": "gallery"
        })
        
        self.assertEqual(response.status_code, 302)
        
        config = connection.configurationentry.get_first()
        self.assertTrue(config.initialized)
        self.assertEqual(config.initialization_type, "search_engine")
        self.assertEqual(config.display_type, "gallery")
        self.connection.close()

    def test_redirect_to_wizard(self):
        connection = self.create_db_connection("test_redirect.db")
        connection.configurationentry.truncate() # Ensure not initialized
        
        client = app.test_client()
        response = client.get("/search")
        
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.location.endswith("/initialization-wizard"))
        self.connection.close()

    def test_no_redirect_for_scripts(self):
        connection = self.create_db_connection("test_no_redirect.db")
        connection.configurationentry.truncate()
        
        client = app.test_client()
        response = client.get("/scripts/ui.js") # ui.js exists in scripts/
        
        self.assertEqual(response.status_code, 200)
        self.connection.close()
