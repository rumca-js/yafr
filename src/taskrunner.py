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
from .wizard import Wizard


class TaskRunner(object):
    def __init__(self, table_name):
        self.connection = None
        self.controller = None
        self.table_name = table_name

        system = System.get_object()
        system.set_thread_ok()

        self.start_reading = True

    def start(self):
        """
        Called from a thread
        """
        try:
            self.connect()

            controller = Controller(self.connection)
            controller.add_configuration()

            config_entry = ConfigurationEntry(self.connection).get()
            if not config_entry.initialized:
                wizard = Wizard(self.connection)
                wziard.init(config_entry)

            self.close()

            self.process_jobs()
        except Exception as e:
            traceback.print_exc()

    def setup_start(self):
        controller = Controller(self.connection)
        controller.add_configuration()
        controller.update_configuration(ConfigurationEntry(self.connection).get())

    def connect(self):
        self.connection = DbConnection(self.table_name)
        self.controller = Controller(connection=self.connection)

    def close(self):
        self.connection.close()
        self.controller.close()

    def process_jobs(self):
        print("Starting reading")

        system = System.get_object()

        while True:
            try:
                self.start_reading = False

                self.connect()

                if not self.is_crawling_server_ok():
                    system = System.get_object()
                    system.set_crawling_server_fail()

                    AppLogging(self.connection).error("Crawling server error")
                    self.close()
                    time.sleep(60)
                    continue
                else:
                    system = System.get_object()
                    system.set_crawling_server_ok()

                AppLogging(self.connection).debug("Crawling server OK")

                self.handle_one_job()

                if self.connection.backgroundjob.count() == 0:
                    self.check_sources()

                if self.is_time_to_clean():
                    self.add_update_jobs()
                    BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_CLEANUP)

                    AppLogging(self.connection).debug("Sleeping 10 sec")
                    self.close()
                    system.set_thread_ok()
                    time.sleep(10)
                    continue


                if self.connection.backgroundjob.count() == 0:
                    AppLogging(self.connection).debug("Sleeping 60 sec")
                    self.close()
                    system.set_thread_ok()
                    time.sleep(60)
                    continue

                system.set_thread_ok()

                self.connection.close()

            except Exception as E:
                if self.connection:
                    self.connection.close()
                    self.connection = None

                traceback.print_exc()
                time.sleep(10)

    def is_time_to_clean(self):
        job_history = self.get_job_history()

        if not job_history:
            return True

        if not job_history.date_created:
            return True

        """
        TODO
        if BackgroundJob(self.connection).is_job(job_name = BackgroundJob.JOB_CLEANUP):
            return False
        """
        jobs = self.connection.backgroundjob.get_where({"job" : BackgroundJob.JOB_CLEANUP})
        for job in jobs:
            return False

        return datetime.now() - job_history.date_created > timedelta(days=1)

    def get_job(self):
        order_by = self.connection.backgroundjob.get_table().c.date_created.asc()
        jobs = self.connection.backgroundjob.get_where(order_by=[order_by])
        for job in jobs:
            return job

    def get_job_history(self):
        order_by = self.connection.backgroundjobhistory.get_table().c.date_created.asc()
        jobs = self.connection.backgroundjobhistory.get_where(order_by=[order_by])
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

            for item in range(1, 4):
                if handler.run():
                    break
                AppLogging(self.connection).debug(f"Job: {job.job} ID:{job.id} error")

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
        elif job.job == BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL:
            return DownloadSocialDataJobHandler(connection = self.connection, job=job, table_name = self.table_name)

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
