from pathlib import Path
from datetime import datetime

from .backgroundjobs import BackgroundJob
from .sourcedata import SourceData
from .entries import Entries
from .sources import Sources
from .entryrules import EntryRules
from .socialdata import SocialData
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

        for source_url in source_urls:
            if not self.is_url_blocked(source_url):
                sources = Sources(self.connection)
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

    def add_social_data(self, entry):
        link = entry.link
        entry_id = entry.id

        social_data_info = self.link_to_social_data(link)
        if social_data_info:
            social_data = SocialData(self.connection)
            social_data.add(entry_id, social_data_info)

    def link_to_social_data(self, link):
        handler = UrlHandler(connection=self.connection, link=link)
        url = handler.get_link_url()
        social_data_info = url.get_social_properties()
        return social_data_info

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
