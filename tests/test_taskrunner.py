from tests.dbtestcase import DbTestCase
import unittest

from linkarchivetools.model.sources import Sources
from linkarchivetools.model.backgroundjobs import BackgroundJob
from src.taskrunner import TaskRunner


class Source():
    def __init__(self):
        self.url = ""
        self.xpath = ""


class TaskRunnerTest(DbTestCase):

    def test_constructor(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        # call tested function
        runner = TaskRunner(self.database_name)

    def test_setup_start(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        runner = TaskRunner(self.database_name)
        runner.connect()

        # call tested function
        runner.setup_start()

        runner.close()

        self.assertEqual(connection.configurationentry.count(), 1)

    def test_get_job(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        sources = Sources(connection=connection)

        test_link_1 = "https://google.com"
        test_link_2 = "https://youtube.com"

        source_id_1 = sources.set(source_url=test_link_1, source_type=Sources.SOURCE_TYPE_PARSE)
        source_id_2 = sources.set(source_url=test_link_2, source_type=Sources.SOURCE_TYPE_PARSE)
        self.assertTrue(source_id_1 is not None)
        self.assertTrue(source_id_2 is not None)
        self.assertEqual(sources.count(), 2)

        job_id_1 = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id_1))
        job_id_2 = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id_2))

        self.assertTrue(job_id_1)
        self.assertTrue(job_id_2)

        job_1 = self.connection.backgroundjob.get(job_id_1)
        job_2 = self.connection.backgroundjob.get(job_id_2)
        self.assertTrue(job_1)
        self.assertTrue(job_2)

        self.assertEqual(BackgroundJob(connection=connection).count(), 2)

        runner = TaskRunner(self.database_name)
        runner.connect()

        # call tested function
        job = runner.get_job()

        runner.close()

        self.assertTrue(job)
        self.assertEqual(job, job_1)
