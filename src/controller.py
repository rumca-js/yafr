from pathlib import Path
from datetime import datetime

from linkarchivetools.model import (
   Entries,
   SocialData,
   Sources,
   SourceData,
   EntryRules,
   BackgroundJob,
)
from .urlhandler import UrlHandler



def read_line_things(input_text):
    sources = [
        line.strip()
        for line in input_text.splitlines()
        if line.strip()
    ]

    sources = set(sources)
    sources = list(sources)

    return sources


class Controller(object):
    def __init__(self, connection):
        self.connection = connection

    def add_sources(self, source_urls):
        self.start_reading = True

        sources = Sources(self.connection)

        for source_url in source_urls:
            if sources.exists(source_url=source_url):
                continue

            if not self.is_url_blocked(source_url):
                sources.set(source_url)

    def add_links(self, link_urls):
        self.start_reading = True

        entries = Entries(connection=self.connection)

        for link_url in link_urls:
            if entries.exists(link=link_url):
                continue

            if not self.is_url_blocked(link_url):
                BackgroundJob(connection=self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_ADD, subject=link_url)

    def is_url_blocked(self, url):
        entry_rules = EntryRules(self.connection)
        for rule in entry_rules.get_rules_for(url=url):
            if rule.block:
                return True

        return False

    def add_sources_text(self, raw_text):
        source_urls = read_line_things(raw_text)
        self.add_sources(source_urls)

    def add_links_text(self, raw_text):
        links_urls = read_line_things(raw_text)
        self.add_links(links_urls)

    def truncate(self):
        self.connection.entries_table.truncate()
        self.connection.sources_table.truncate()

    def print(self):
        for entry in self.connection.entries_table.get_entries():
            self.print_entry(entry)

    def print_entry(self, entry):
        print(entry.title)
        print(entry.link)

    def close(self):
        if self.connection:
            self.connection.close()
            self.connection = None
