from tests.dbtestcase import DbTestCase
from src.entryrules import EntryRules


class EntryRulesTest(DbTestCase):
    def test_add_entry_rule(self):
        db = self.create_db_connection("test.db")
        db.entry_rules.truncate()

        rules = EntryRules(connection=db)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        # call tested function
        result = rules.add_entry_rule(test_link)

        self.assertEqual(rules.count(), 1)
        self.assertTrue(result is not None)
        
        db.close()

    def test_is_url_blocked__true(self):
        db = self.create_db_connection("test.db")
        db.entry_rules.truncate()

        rules = EntryRules(connection=db)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        rules.add_entry_rule(test_link)

        # call tested function
        self.assertTrue(rules.is_url_blocked(test_link))

        db.close()

    def test_is_url_blocked__false(self):
        db = self.create_db_connection("test.db")
        db.entry_rules.truncate()

        rules = EntryRules(connection=db)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        # call tested function
        self.assertFalse(rules.is_url_blocked(test_link))

        db.close()
