from datetime import datetime, timedelta

from linkarchivetools.model import (
   EntryRules,
   Entries,
   Sources,
   SourceData,
   BackgroundJob,
)
from src.jobhandlers import *
from tests.dbtestcase import DbTestCase


class ProcessSourceJobHandlerTest(DbTestCase):
    def test_run__parse__no_social_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://page-with-two-links.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(entry_controller.count(), 2)

        entries = list(entry_controller.get_where({}))
        self.assertEqual(len(entries), 2)
        self.assertTrue(entries[0].link == "https://link1.com" or entries[1].link == "https://link1.com")
        self.assertTrue(entries[0].link == "https://link2.com" or entries[1].link == "https://link2.com")

        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        self.assertEqual(sd_controller.count(), 1)

    def test_run__rss__no_social_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertTrue(entry_controller.count() > 0)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)
        self.assertEqual(sd_controller.count(), 1)

    def test_run__rss__updates_social_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS)
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        source = sources.get(source_id)
        self.assertEqual(source.source_type, Sources.SOURCE_TYPE_RSS)

        sd_controller = SourceData(connection)
        source_data_id = sd_controller.mark_read(source)
        self.assertTrue(source_data_id)
        old_date_fetched = datetime.now() - timedelta(days=2)
        sd_controller.get_table().update_json_data(id=source_data_id, json_data={"date_fetched" : old_date_fetched})

        self.assertEqual(sd_controller.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)
        self.assertEqual(sd_controller.count(), 1)

        sourcedata = sd_controller.get(source_data_id)
        self.assertTrue(sourcedata.date_fetched > old_date_fetched)

    def test_run__unknown_source(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        controller = ConfigurationEntry(connection=connection)
        self.assertEqual(controller.count(), 1)

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        source_id = sources.set(source_url=test_link, source_type="")
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id))
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)
        self.assertEqual(sd_controller.count(), 1)
        self.assertEqual(controller.count(), 1)

        source = sources.get(source_id)
        self.assertEqual(source.source_type, Sources.SOURCE_TYPE_PARSE)

    def test_run__remove(self):
        connection = self.initialize_database()
        self.disable_web_pages()

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

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 0)

        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

    def test_close(self):
        connection = self.initialize_database()
        self.disable_web_pages()

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

        handler = ProcessSourceJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.close()

        self.assertEqual(BackgroundJob(connection=connection).count(), 0)


class UpdateLinkJobHandlerTest(DbTestCase):
    def test_run(self):
        connection = self.initialize_database()
        self.disable_web_pages()

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

        handler = UpdateLinkJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)


class AddLinkJobHandlerTest(DbTestCase):
    def test_run(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        controller = Entries(connection=connection)
        self.assertEqual(controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link)
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)

        entries = controller.get_where({})
        entries = list(entries)

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].title)
        self.assertTrue(entries[0].description)
        self.assertTrue(entries[0].date_created)

    def test_run__cfg(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        controller = Entries(connection=connection)
        self.assertEqual(controller.count(), 0)

        cfg = {}
        cfg["bookmarked"] = True

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link, cfg=cfg)
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)

    def test_run__date_published(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://www.youtube.com/watch?v=date_published"

        controller = Entries(connection=connection)
        self.assertEqual(controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link)
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(connection = connection, job=job, table_name = self.database_name)
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)

        entries = controller.get_where({})
        entries = list(entries)

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].date_published != None)
