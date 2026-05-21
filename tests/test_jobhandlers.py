from tests.dbtestcase import DbTestCase
from linkarchivetools.model.entryrules import EntryRules
from linkarchivetools.model.sources import Sources
from linkarchivetools.model.backgroundjobs import BackgroundJob
from src.jobhandlers import *


class ProcessSourceJobHandlerTest(DbTestCase):
    def test_run__parse(self):
        self.disable_web_pages()

        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.backgroundjob.truncate()
        connection.blockentry.truncate()
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        self.use_remote_server(connection)

        test_link = "https://google.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)

        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

    def test_run__rss(self):
        self.disable_web_pages()

        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.backgroundjob.truncate()
        connection.blockentry.truncate()
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        self.use_remote_server(connection)

        test_link = "https://google.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

    def test_run__remove(self):
        self.disable_web_pages()

        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.backgroundjob.truncate()
        connection.blockentry.truncate()
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        self.use_remote_server(connection)

        test_link = "https://google.com"

        rules = EntryRules(connection=connection)
        result = rules.add_entry_rule(test_link, block=True)

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 0)

        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

    def test_close(self):
        self.disable_web_pages()

        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.backgroundjob.truncate()
        connection.blockentry.truncate()
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        self.use_remote_server(connection)

        test_link = "https://google.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = database_name)
        # call test function
        handler.close()

        self.assertEqual(BackgroundJob(connection=connection).count(), 0)


class UpdateLinkJobHandlerTest(DbTestCase):
    def test_run(self):
        self.disable_web_pages()

        database_name = "test.db"
        connection = self.create_db_connection(database_name)
        connection.entry_rules.truncate()
        connection.sources_table.truncate()
        connection.entries_table.truncate()

        self.use_remote_server(connection)

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
