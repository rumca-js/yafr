from tests.dbtestcase import DbTestCase
from linkarchivetools.model.entryrules import EntryRules
from linkarchivetools.model.sources import Sources
from linkarchivetools.model.backgroundjobs import BackgroundJob


class SourcesTest(DbTestCase):
    def test_set(self):
        database_name = "test.db"
        db = self.create_db_connection(database_name)
        db.entry_rules.truncate()
        db.sources_table.truncate()
        db.entries_table.truncate()

        sources = Sources(connection=db)
        self.assertEqual(sources.count(), 0)

        test_link = "https://google.com"

        # call tested function
        source_id = sources.set(source_url=test_link)

        self.assertEqual(sources.count(), 1)

        self.assertTrue(source_id is not None)
