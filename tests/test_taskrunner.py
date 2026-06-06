import unittest
from datetime import datetime, timedelta

from linkarchivetools.model import (
    Sources,
    SourceData,
    BackgroundJob,
)
from tests.dbtestcase import DbTestCase
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

        connection.configurationentry.truncate()

        self.assertEqual(connection.configurationentry.count(), 0)

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

    def test_check_sources(self):
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

        runner = TaskRunner(self.database_name)
        runner.connect()

        # call tested function
        runner.check_sources()

        self.assertEqual(BackgroundJob(connection=connection).count(), 2)

    def test_check_sources__time(self):
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

        source_1 = sources.get(source_id_1)
        source_2 = sources.get(source_id_2)

        data = SourceData(connection)
        data.mark_read(source_1)
        data.mark_read(source_2)

        source_data_1 = data.get_source_data(source_1)
        source_data_2 = data.get_source_data(source_2)

        date_fetched_1 = datetime.now() - timedelta(days=1)
        date_fetched_2 = datetime.now() - timedelta(days=2)

        data.get_table().update_json_data(source_data_1.id, {"date_fetched" : date_fetched_1})
        data.get_table().update_json_data(source_data_2.id, {"date_fetched" : date_fetched_2})

        runner = TaskRunner(self.database_name)
        runner.connect()

        # call tested function
        runner.check_sources()

        self.assertEqual(BackgroundJob(connection=connection).count(), 2)

        jobs = list(BackgroundJob(connection=connection).get_where())
        self.assertEqual(jobs[0].subject, str(source_2.id))
        self.assertEqual(jobs[1].subject, str(source_1.id))
