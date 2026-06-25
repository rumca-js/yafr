from datetime import datetime, timedelta
from datetime import timezone

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
    def create_environment__two_sources(self):
        sources = Sources(connection=self.connection)

        # Create two sources
        source_id_1 = sources.set(
            source_url="https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM",
            source_type=Sources.SOURCE_TYPE_RSS,
        )
        source_id_2 = sources.set(
            source_url="https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM2",
            source_type=Sources.SOURCE_TYPE_RSS,
        )

        self.source1 = sources.get(source_id_1)
        self.source2 = sources.get(source_id_2)

        job_id = BackgroundJob(connection=self.connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id_1)
        )
        self.job = BackgroundJob(connection=self.connection).get(job_id)
        return self.job

    def add_entry(self, link, source):
        json_data = {}
        json_data["link"] = link
        json_data["title"] = link
        json_data["source_id"] = source.id

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)
        return controller.get(entry_id)

    def test_run__parse__no_social_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://page-with-two-links.com"

        datetime_start = datetime.now()

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(entry_controller.count(), 2)

        entries = list(entry_controller.get_where({}))
        self.assertEqual(len(entries), 2)
        self.assertTrue(
            entries[0].link == "https://link1.com"
            or entries[1].link == "https://link1.com"
        )
        self.assertTrue(
            entries[0].link == "https://link2.com"
            or entries[1].link == "https://link2.com"
        )

        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        source = sources.get(source_id)
        self.assertTrue(source)

        self.assertEqual(sd_controller.count(), 1)
        source_data = sd_controller.get_source_data(source)
        self.assertTrue(source_data)
        self.assertTrue(source_data.date_fetched)
        self.assertTrue(source_data.date_fetched > datetime_start)

    def test_run__rss__reads_entries(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        datetime_start = datetime.now()

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertTrue(entry_controller.count() > 0)

    def test_run__rss__reads_entries__sets_language_age(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        datetime_start = datetime.now()

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        json_data = {}
        json_data["language"] = 'it'
        json_data["age"] = 5
        sources.get_table().update_json_data(source_id, json_data=json_data)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertTrue(entry_controller.count() > 0)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        for entry in entry_controller.get_where({}):
            self.assertEqual(entry.language, 'it')
            self.assertEqual(entry.age, 5)

    def test_run__rss__creates_source_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        datetime_start = datetime.now()

        test_link = "https://www.youtube.com/feeds/videos.xml?channel_id=SAMTIMESAMTIMESAMTIMESAM"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        entry_controller = Entries(connection=connection)
        self.assertEqual(entry_controller.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertTrue(entry_controller.count() > 0)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        source = sources.get(source_id)
        self.assertTrue(source)

        self.assertEqual(sd_controller.count(), 1)
        source_data = sd_controller.get_source_data(source)
        self.assertTrue(source_data)
        self.assertTrue(source_data.date_fetched)
        self.assertTrue(source_data.date_fetched > datetime_start)

    def test_run__rss__updates_source_data(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        source = sources.get(source_id)
        self.assertEqual(source.source_type, Sources.SOURCE_TYPE_RSS)

        sd_controller = SourceData(connection)
        source_data_id = sd_controller.mark_read(source)
        self.assertTrue(source_data_id)
        old_date_fetched = datetime.now() - timedelta(days=2)
        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": old_date_fetched}
        )

        self.assertEqual(sd_controller.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
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

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)
        self.assertEqual(sd_controller.count(), 1)
        self.assertEqual(controller.count(), 1)

        source = sources.get(source_id)
        self.assertEqual(source.source_type, Sources.SOURCE_TYPE_RSS)

    def test_run__rss__updates__source(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        test_link = "https://page-with-language.com"

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_RSS
        )

        sd_controller = SourceData(connection)
        self.assertEqual(sd_controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(sources.count(), 1)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        source = sources.get(source_id)

        self.assertEqual(source.source_type, Sources.SOURCE_TYPE_RSS)
        self.assertEqual(source.title, "Page with a 'it' language")
        self.assertEqual(source.language, "it")

    def test_run__remove(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://google.com"

        rules = EntryRules(connection=connection)
        result = rules.add_entry_rule(test_link, block=True)

        sources = Sources(connection=connection)
        self.assertEqual(sources.count(), 0)

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
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

        source_id = sources.set(
            source_url=test_link, source_type=Sources.SOURCE_TYPE_PARSE
        )
        self.assertTrue(source_id is not None)
        self.assertEqual(sources.count(), 1)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source_id)
        )
        self.assertTrue(job_id is not None)
        self.assertEqual(BackgroundJob(connection=connection).count(), 1)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = ProcessSourceJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.close()

        self.assertEqual(BackgroundJob(connection=connection).count(), 0)

    def test_get_newest_entry__none(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        newest = handler.get_newest_entry(self.source1)
        self.assertIsNone(newest)

    def test_get_newest_entry__one_entry(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        # 2. Test when there is a single entry for source1
        entry_controller = Entries(connection=self.connection)

        now = datetime.now()
        entry_id_1 = entry_controller.add(
            {
                "link": "https://link1.com",
                "title": "Link 1",
                "source_id": self.source1.id,
                "date_published": now - timedelta(hours=2),
            }
        )

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        newest = handler.get_newest_entry(self.source1)
        self.assertIsNotNone(newest)
        self.assertEqual(newest.id, entry_id_1)

    def test_get_newest_entry__multiple_entries(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        entry_controller = Entries(connection=self.connection)
        now = datetime.now()

        # 3. Test when there are multiple entries for source1
        entry_id_2 = entry_controller.add(
            {
                "link": "https://link2.com",
                "title": "Link 2",
                "source_id": self.source1.id,
                "date_published": now - timedelta(hours=1),
            }
        )
        entry_id_3 = entry_controller.add(
            {
                "link": "https://link3.com",
                "title": "Link 3",
                "source_id": self.source1.id,
                "date_published": now - timedelta(hours=3),
            }
        )

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        newest = handler.get_newest_entry(self.source1)
        self.assertIsNotNone(newest)
        self.assertEqual(newest.id, entry_id_2)

        # 4. Test when there are entries for another source (source2) that are even newer
        entry_id_4 = entry_controller.add(
            {
                "link": "https://link4.com",
                "title": "Link 4",
                "source_id": self.source2.id,
                "date_published": now,
            }
        )

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        newest = handler.get_newest_entry(self.source1)
        self.assertIsNotNone(newest)
        self.assertEqual(newest.id, entry_id_2)

        newest_source2 = handler.get_newest_entry(self.source2)
        self.assertIsNotNone(newest_source2)
        self.assertEqual(newest_source2.id, entry_id_4)

    def test_is_new_entry__no_source_data__no_entry(self):

        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        sd_controller = SourceData(self.connection)

        # 1. No source data exists -> returns True
        self.assertTrue(handler.is_new_entry(self.source1, []))

    def test_is_new_entry__no_source_data__entry(self):

        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        sd_controller = SourceData(self.connection)

        now = datetime.now() - timedelta(minutes=11)
        now_utc = now.replace(tzinfo=timezone.utc)
        new_entries = [
            {
                "link": "https://link1.com",
                "date_published": now_utc - timedelta(hours=1),
            },
            {
                "link": "https://link3.com",
                "date_published": now_utc + timedelta(minutes=10),
            },
        ]

        # 1. No source data exists -> returns True
        self.assertTrue(handler.is_new_entry(self.source1, new_entries))

    def test_is_new_entry__source_data__date_fetched__is_none__no_entry(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        sd_controller = SourceData(self.connection)

        # 2. Source data exists, but date_fetched is None -> returns True
        source_data_id = sd_controller.mark_read(self.source1)
        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": None}
        )
        self.assertTrue(handler.is_new_entry(self.source1, []))

    def test_is_new_entry__source_data_date_fetched__no_entry(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        sd_controller = SourceData(self.connection)

        # 3. Source data exists, date_fetched is set, but entries is empty -> returns False
        now = datetime.now()
        source_data_id = sd_controller.mark_read(self.source1)
        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": now}
        )
        self.assertFalse(handler.is_new_entry(self.source1, []))

    def test_is_new_entry__source_data_date_fetched__entries__older(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        sd_controller = SourceData(self.connection)
        source_data_id = sd_controller.mark_read(self.source1)
        now = datetime.now()
        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": now}
        )

        # 4. Entries exist, but none of them are newer than date_fetched -> returns False
        now_utc = now.replace(tzinfo=timezone.utc)
        old_entries = [
            {
                "link": "https://link1.com",
                "date_published": now_utc - timedelta(hours=1),
            },
            {
                "link": "https://link2.com",
                "date_published": now_utc - timedelta(minutes=30),
            },
        ]
        self.assertFalse(handler.is_new_entry(self.source1, old_entries))

    def test_is_new_entry__source_data_date_fetched__newer_entry(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        now = datetime.now() - timedelta(minutes=11)
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        source_data_id = sd_controller.mark_read(self.source1)

        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": now}
        )

        # 5. At least one entry is newer than date_fetched -> returns True
        new_entries = [
            {
                "link": "https://link1.com",
                "date_published": now_utc - timedelta(hours=1),
            },
            {
                "link": "https://link3.com",
                "date_published": now_utc + timedelta(minutes=10),
            },
        ]
        self.assertTrue(handler.is_new_entry(self.source1, new_entries))

    def test_is_new_entry__source_data_date_fetched__entry_no_date_published(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        source_data_id = sd_controller.mark_read(self.source1)
        sd_controller.get_table().update_json_data(
            id=source_data_id, json_data={"date_fetched": now}
        )

        # 6. At least one entry doesn't have date_published -> returns True
        missing_date_entries = [
            {
                "link": "https://link1.com",
                "date_published": now_utc - timedelta(hours=1),
            },
            {"link": "https://link4.com"},
        ]

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )
        self.assertTrue(handler.is_new_entry(self.source1, missing_date_entries))

    def test_check_if_old_source_checked_once_a_day__no_data(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 0)

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        sources = Sources(self.connection)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        status = handler.check_if_old_source_checked_once_a_day(sources, self.source1)
        self.assertFalse(status)

    def test_check_if_old_source_checked_once_a_day__data(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 0)

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        sd_controller.mark_read(self.source1)
        sources = Sources(self.connection)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        status = handler.check_if_old_source_checked_once_a_day(sources, self.source1)
        self.assertFalse(status)

    def test_check_if_old_source_checked_once_a_day__data__entry(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()
        entry = self.add_entry("https://google.com", self.source1)

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 1)

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        sd_controller.mark_read(self.source1)
        sources = Sources(self.connection)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        status = handler.check_if_old_source_checked_once_a_day(sources, self.source1)
        self.assertFalse(status)

    def test_check_if_old_source_checked_once_a_day__data__entry_with_date_publish__recent(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        link = "https://google.com"
        json_data = {}
        json_data["link"] = link
        json_data["title"] = link
        json_data["source_id"] = self.source1.id
        json_data["date_published"] = datetime.now()

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 1)

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        sd_controller.mark_read(self.source1)
        sources = Sources(self.connection)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        status = handler.check_if_old_source_checked_once_a_day(sources, self.source1)
        self.assertFalse(status)

    def test_check_if_old_source_checked_once_a_day__data__entry_with_date_publish__old(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()

        job = self.create_environment__two_sources()

        link = "https://google.com"
        json_data = {}
        json_data["link"] = link
        json_data["title"] = link
        json_data["source_id"] = self.source1.id
        json_data["date_published"] = datetime.now() - timedelta(days=50)

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 1)

        now = datetime.now()
        now_utc = now.replace(tzinfo=timezone.utc)

        sd_controller = SourceData(self.connection)
        sd_controller.mark_read(self.source1)
        sources = Sources(self.connection)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )

        status = handler.check_if_old_source_checked_once_a_day(sources, self.source1)
        self.assertTrue(status)

    def test_is_in_db__empty(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()
        job = self.create_environment__two_sources()

        controller = Entries(connection=self.connection)
        self.assertEqual(controller.count(), 0)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )
        status = handler.is_in_db("https://google.com")
        self.assertFalse(status)

    def test_is_in_db__non_empty__true(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()
        job = self.create_environment__two_sources()

        link = "https://google.com"
        json_data = {}
        json_data["link"] = link
        json_data["title"] = link

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 1)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )
        status = handler.is_in_db("https://google.com")
        self.assertTrue(status)

    def test_is_in_db__non_empty__false(self):
        self.connection = self.initialize_database()
        self.disable_web_pages()
        job = self.create_environment__two_sources()

        link = "https://google.com"
        json_data = {}
        json_data["link"] = link
        json_data["title"] = link

        controller = Entries(connection=self.connection)
        entry_id = controller.add(entry_json=json_data)

        entry_controller = Entries(connection=self.connection)
        self.assertEqual(entry_controller.count(), 1)

        handler = ProcessSourceJobHandler(
            connection=self.connection, job=job, table_name=self.database_name
        )
        status = handler.is_in_db("https://linkedin.com")
        self.assertFalse(status)


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

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id)
        )
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = UpdateLinkJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
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

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link
        )
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
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

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link, cfg=cfg
        )
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)

    def test_run__date_published(self):
        connection = self.initialize_database()
        self.disable_web_pages()

        test_link = "https://www.youtube.com/watch?v=date_published"

        controller = Entries(connection=connection)
        self.assertEqual(controller.count(), 0)

        job_id = BackgroundJob(connection=connection).create_single_job(
            job_name=BackgroundJob.JOB_LINK_ADD, subject=test_link
        )
        self.assertTrue(job_id is not None)

        job = BackgroundJob(connection=connection).get(job_id)
        self.assertTrue(job)

        handler = AddLinkJobHandler(
            connection=connection, job=job, table_name=self.database_name
        )
        # call test function
        handler.run()

        self.assertEqual(controller.count(), 1)

        entries = controller.get_where({})
        entries = list(entries)

        self.assertEqual(len(entries), 1)
        self.assertTrue(entries[0].date_published != None)
