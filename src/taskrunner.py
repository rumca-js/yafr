import re
import time
from datetime import datetime, timedelta
import traceback

from webtoolkit import (
   RemoteUrl,
   RemoteServer,
)

from .dbconnection import DbConnection
from .controller import Controller
from .system import System
from .sourcedata import SourceData
from .sources import Sources
from .entries import Entries
from .applogging import AppLogging
from .jobhandlers import *
from .backgroundjobs import BackgroundJob
from .configurationentry import ConfigurationEntry


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

            self.setup_start()

            if init_sources:
                self.init_sources(init_sources)

            config_entry = ConfigurationEntry(self.connection)
            config_entry.reset()

            self.controller.close()
            self.connection.close()

            self.process_jobs()
        except Exception as e:
            traceback.print_exc()

    def init_sources(self, init_sources):
        for source_url in init_sources:
            sources = Sources(self.connection)
            sources.set(source_url)

    def setup_start(self):
        entries = Entries(self.connection)
        entries_len = entries.count()
        sources = Sources(self.connection)
        sources_len = sources.count()

        AppLogging(self.connection).info(f"Entries: {entries_len}")
        AppLogging(self.connection).info(f"Sources: {sources_len}")

    def process_jobs(self):
        print("Starting reading")

        while True:
            try:
                system = System.get_object()

                self.start_reading = False

                self.connection = DbConnection(self.table_name)
                self.controller = Controller(connection=self.connection)

                if not self.is_crawling_server_ok():
                    AppLogging(self.connection).error("Crawling server error")
                    time.sleep(60)

                # do the reading
                if not self.handle_one_job():
                    AppLogging(self.connection).debug("Sleeping")
                    time.sleep(10)

                self.connection.close()

                system.set_thread_ok()
            except Exception as E:
                AppLogging(self.connection).exc(E)
                time.sleep(10)

    def get_job(self):
        order_by = self.connection.backgroundjob.get_table().c.date_created
        jobs = self.connection.backgroundjob.get_where(order_by=[order_by])
        for job in jobs:
            return job

    def check_sources(self):
        sourcedata = SourceData(self.connection)

        source_ids = []
        for source in self.connection.sources_table.get_sources():
            this_source_data = sourcedata.get_source_data(source)

            if sourcedata.is_update_needed(source):
                job = BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_PROCESS_SOURCE, subject=str(source.id))

    def handle_one_job(self):
        job = self.get_job()
        if not job:
            self.add_update_jobs()
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_CLEANUP)
            self.check_sources()
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
        len_updated = 0
        desired_len = 5

        entries = Entries(self.connection)
        entry_objs = self.connection.entries_table.get_where({"date_update_last" : None}, limit=desired_len)
        for entry in entry_objs:
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry.id))
            len_updated += 1

        if len_updated < desired_len:
            # TODO older than

            #entry_objs = self.connection.entries_table.get_where({"date_update_last" : None}, limit=desired_len)
            #for entry in entry_objs:
            #    BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry.id))
            #    len_updated += 1
            pass

    def is_crawling_server_ok(self):
        config = self.connection.configurationentry.get()
        location = config.remote_webtools_server_location
        if location:
            request = PageRequestObject(location)
            url = RemoteServer(remote_server=location)
            if not url.get_pingj(url = location):
                return False
        return True
