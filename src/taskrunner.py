import re
import time
from datetime import datetime, timedelta
import traceback

from webtoolkit import (
   RemoteUrl,
)

from .dbconnection import DbConnection
from .controller import Controller
from .system import System
from .sourcedata import SourceData
from .sources import Sources
from .entries import Entries
from .applogging import AppLogging
from .jobhandlers import ProcessSourceJobHandler
from .backgroundjobs import BackgroundJob


class TaskRunner(object):
    def __init__(self, table_name):
        self.connection = None
        self.controller = None
        self.table_name = table_name

        system = System.get_object()
        system.set_thread_ok()

        self.waiting_due = None
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
                # do the reading
                if not self.handle_one_job():
                    AppLogging(self.connection).debug("Sleeping")
                    time.sleep(10)
                self.connection.close()

                system.set_thread_ok()
            except Exception as E:
                AppLogging(self.connection).exc(E)
                time.sleep(1)

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
            self.check_sources()
            return False

        handler = None
        if job.job == BackgroundJob.JOB_PROCESS_SOURCE:
            AppLogging(self.connection).debug("Processing source")
            handler = ProcessSourceJobHandler(connection = self.connection, job=job, table_name = self.table_name)
            AppLogging(self.connection).debug("Processing source DONE")
        else:
            raise IOError("Unsupported job")

        if handler:
            AppLogging(self.connection).debug(f"Running source process handler: job ID:{job.id}")
            handler.run()
            handler.close()
            AppLogging(self.connection).debug(f"Running source process handler: job ID:{job.id} DONE")

            return True
