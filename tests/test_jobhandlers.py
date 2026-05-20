from tests.dbtestcase import DbTestCase
from linkarchivetools.model.entryrules import EntryRules
from linkarchivetools.model.sources import Sources
from linkarchivetools.model.backgroundjobs import BackgroundJob
from src.jobhandlers import *


class ProcessSourceJobHandlerTest(DbTestCase):
    def test_run(self):
        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        rules = EntryRules(connection=connection)
        test_link = "https://google.com"
        result = rules.add_entry_rule(test_link)

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link)

        self.assertEqual(sources.count(), 1)

        self.assertTrue(source_id is not None)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 0)


class UpdateLinkJobHandlerTest(DbTestCase):
    def test_run(self):
        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        json_data = {}
        json_data["link"] = "https://www.google.com"
        json_data["title"] = "Google"

        controller = Entries(connection=connection)
        entry_id = controller.add(entry_json=json_data)
        self.assertTrue(entry_id is not None)

        self.assertEqual(controller.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id))
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = UpdateLinkJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)
