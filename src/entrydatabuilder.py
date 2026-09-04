from linkarchivetools.model import (
   Entries,
   BackgroundJob,
   EntryRules,
   ConfigurationEntry,
)
from .urlhandler import UrlHandler


class EntryDataBuilder(object):
    def __init__(self, connection=None):
        self.connection=connection
        self.errors = []

    def build_simple(self, link, source_is_auto=False, browser=None):
        self.link = link

        if not self.is_enabled_to_store_link():
            self.errors.append("Link not configured to be stored")
            return

        entries = Entries(connection=self.connection)
        if entries.exists(link=link):
            self.errors.append("Link already exists")
            return

        entry_json = {"link" : link}
        entry_id = entries.add(entry_json)
        if entry_id is None:
            self.errors.append("Could not add entry - Controller")

        if entry_id:
            config = self.connection.configurationentry.get()

            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry_id))
            if config.auto_scan_new_entries:
                BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_SCAN, subject=str(entry_id))
            if config.enable_link_archiving:
                BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_SAVE, subject=str(entry_id))

            return entry_id

    def is_enabled_to_store_link(self):
        link = self.link

        if not link:
            return False

        handler = UrlHandler(connection=self.connection, link=self.link)
        if not handler.is_accepted():
            self.errors.append("Link is not accepted")
            return False

        rule = handler.is_blocked()
        if rule:
            self.errors.append("Link is blocked by a rule")
            return False

        return True
