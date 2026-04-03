from tests.dbtestcase import DbTestCase
from src.entryrules import EntryRules
from src.sources import Sources
from src.backgroundjobs import BackgroundJob
from src.jobhandlers import *


class ProcessSourceJobHandlerTest(DbTestCase):
    def test_run(self):
        database_name = "test.db"
        db = self.create_db_connection(database_name)
        db.entry_rules.truncate()
        db.sources_table.truncate()
        db.entries_table.truncate()

        rules = EntryRules(connection=db)
        test_link = "https://google.com"
        result = rules.add_entry_rule(test_link)

        sources = Sources(connection=db)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link)

        self.assertEqual(sources.count(), 1)

        self.assertTrue(source_id is not None)

        job_id = BackgroundJob(connection=db).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))

        job = BackgroundJob(connection=db).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = db, job=job, table_name = database_name)
        handler.run()

        self.assertEqual(sources.count(), 0)
