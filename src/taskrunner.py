import re
import time
from datetime import datetime, timedelta, timezone
import traceback
from sqlalchemy import select, or_

from webtoolkit import (
   RemoteUrl,
   RemoteServer,
)
from linkarchivetools.model import (
    DbConnection,
    SourceData,
    Sources,
    Entries,
    AppLogging,
    BackgroundJob,
    ConfigurationEntry,
)

from .controller import Controller
from .system import System
from .jobhandlers import *


class TaskRunner(object):
    def __init__(self, table_name):
        self.connection = None
        self.controller = None
        self.table_name = table_name

        system = System.get_object()
        system.set_thread_ok()

        self.start_reading = True

    def start(self, init_sources=None):
        """
        Called from a thread
        """
        try:
            self.connection = DbConnection(self.table_name)
            self.controller = Controller(connection=self.connection)

            config_entry = ConfigurationEntry(self.connection).get()
            if not config_entry.initialized:
                self.setup_start()
                self.init_sources(init_sources)

            self.controller.close()
            self.connection.close()

            self.process_jobs()
        except Exception as e:
            traceback.print_exc()

    def reset_config(self):
        config = ConfigurationEntry(self.connection)
        config_entry = config.get()

        json_data = {}
        json_data["initialized"] = True
        json_data["enable_social_data"] = False
        json_data["new_entries_fetch_social_data"] = False
        json_data["entry_update_fetches_social_data"] = False

        config.get_table().update_json_data(id=config_entry.id, json_data=json_data)

    def init_sources(self, init_sources):
        for source_url in init_sources:
            sources = Sources(self.connection)
            sources.set(source_url)

    def setup_start(self):
        self.reset_config()

    def process_jobs(self):
        print("Starting reading")

        system = System.get_object()

        while True:
            try:
                self.start_reading = False

                self.connection = DbConnection(self.table_name)
                self.controller = Controller(connection=self.connection)

                if not self.is_crawling_server_ok():
                    AppLogging(self.connection).error("Crawling server error")
                    self.connection.close()
                    time.sleep(60)
                    continue
                AppLogging(self.connection).debug("Crawling server OK")

                system.set_thread_ok()

                self.handle_one_job()

                if self.connection.backgroundjob.count() == 0:
                    self.check_sources()

                if self.connection.backgroundjob.count() == 0:
                    self.add_update_jobs()
                    BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_CLEANUP)

                    AppLogging(self.connection).debug("Sleeping")
                    self.connection.close()

                    time.sleep(10)
                    continue

                self.connection.close()

            except Exception as E:
                traceback.print_exc()
                time.sleep(10)

    def get_job(self):
        order_by = self.connection.backgroundjob.get_table().c.date_created
        jobs = self.connection.backgroundjob.get_where(order_by=[order_by])
        for job in jobs:
            return job

    def check_sources(self):
        """
        First read unread sources.
        The add jobs in order of reading need.
        """
        sd_controller = SourceData(self.connection)
        sources = Sources(self.connection)

        for source in sources.get_table().get_where():
            source_data = sd_controller.get_source_data(source)
            if not source_data:
                job = BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source.id))

        table = sd_controller.get_table().get_table()
        order_by = [table.c.date_fetched.asc()]
        for sd in sd_controller.get_table().get_where(order_by=order_by):
            source = sources.get_table().get(id=sd.source_obj_id)
            if source:
                if sd_controller.is_update_needed(source):
                    job = BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source.id))

    def handle_one_job(self):
        job = self.get_job()
        if not job:
            return False

        handler = self.job2handler(job)

        if not handler:
            raise IOError("Unsupported job")

        if handler:
            AppLogging(self.connection).debug(f"Running job {job.job} ID:{job.id}")
            handler.run()
            handler.close()
            AppLogging(self.connection).debug(f"Running job {job.job} ID:{job.id} DONE")

            return True
        
    def job2handler(self, job):
        if job.job == BackgroundJob.JOB_PROCESS_SOURCE:
            return ProcessSourceJobHandler(connection = self.connection, job=job, table_name = self.table_name)
        elif job.job == BackgroundJob.JOB_CLEANUP:
            return CleanupJobHandler(connection = self.connection, job=job, table_name = self.table_name)
        elif job.job == BackgroundJob.JOB_LINK_UPDATE_DATA:
            return UpdateLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)
        elif job.job == BackgroundJob.JOB_LINK_RESET_DATA:
            return ResetLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)
        elif job.job == BackgroundJob.JOB_LINK_ADD:
            return AddLinkJobHandler(connection = self.connection, job=job, table_name = self.table_name)

    def add_update_jobs(self):
        config_entry = ConfigurationEntry(self.connection).get()
        number_of_update_entries = config_entry.number_of_update_entries

        if not number_of_update_entries:
            return

        days_to_update = 5

        date_cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_update)

        table = self.connection.entries_table.get_table()
        entries_select = (select(table)
                          .order_by(table.c.page_rating_votes.desc())
                          .where(or_(table.c.date_update_last.is_(None),
                                 table.c.date_update_last < date_cutoff)
                          )
                          .limit(number_of_update_entries)
                         )

        entries = self.connection.connection.execute(entries_select)
        entry_objs = list(entries)

        for entry in entry_objs:
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry.id))

    def is_crawling_server_ok(self):
        config = self.connection.configurationentry.get()
        location = config.remote_webtools_server_location
        if location:
            request = PageRequestObject(location)
            url = RemoteServer(remote_server=location)
            if not url.get_pingj(url = location):
                return False
        return True
