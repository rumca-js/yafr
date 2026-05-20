from tests.dbtestcase import DbTestCase
from linkarchivetools.model.entryrules import EntryRules


class EntryRulesTest(DbTestCase):
    def test_add_entry_rule(self):
        connection = self.create_db_connection("test.db")
        connection.entry_rules.truncate()

        rules = EntryRules(connection=connection)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        # call tested function
        result = rules.add_entry_rule(test_link)

        self.assertEqual(rules.count(), 1)
        self.assertTrue(result is not None)
        
        connection.close()

    def test_is_url_blocked__true(self):
        connection = self.create_db_connection("test.db")
        connection.entry_rules.truncate()

        rules = EntryRules(connection=connection)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        rules.add_entry_rule(test_link)

        # call tested function
        self.assertTrue(rules.is_url_blocked(test_link))

        connection.close()

    def test_is_url_blocked__false(self):
        connection = self.create_db_connection("test.db")
        connection.entry_rules.truncate()

        rules = EntryRules(connection=connection)

        self.assertEqual(rules.count(), 0)

        test_link = "https://google.com"

        # call tested function
        self.assertFalse(rules.is_url_blocked(test_link))

        connection.close()
