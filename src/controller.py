from pathlib import Path
from datetime import datetime

from linkarchivetools.model import (
   Entries,
   SocialData,
   Sources,
   SourceData,
   EntryRules,
   BackgroundJob,
   ConfigurationEntry,
   SearchView,
   AppLogging,
)
from .entrydatabuilder import EntryDataBuilder



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

    def initialize(self):
        self.setup_views()

    def setup_views(self):
        views = SearchView(self.connection)
        if self.connection.searchview.count() == 0:
            view_id = views.add()
            json_data = {
                "name": "Default",
                "default": True,
                "priority": 1,
                "filter_statement": "",
                "order_by": "-date_published"
            }
            self.connection.searchview.update_json_data(id=view_id, json_data=json_data)

    def add_configuration(self):
        config = ConfigurationEntry(self.connection)
        if config.count() != 0:
            return

        config.get()

    def update_configuration(self, config_entry):
        json_data = {}
        json_data["initialized"] = True
        json_data["enable_social_data"] = False
        json_data["new_entries_fetch_social_data"] = False
        json_data["entry_update_fetches_social_data"] = False
        json_data["initialization_type"] = ConfigurationEntry.CONFIGURATION_SEARCH_ENGINE

        config = ConfigurationEntry(self.connection)
        return config.update(json_data)

    def add_sources(self, source_urls):
        sources = Sources(self.connection)
        source_ids = []

        for source_url in source_urls:
            if sources.exists(source_url=source_url):
                continue

            if not self.is_url_blocked(source_url):
                source_id = sources.set(source_url)
                source_ids.append(source_id)

        return source_ids

    def get_link(self, link):
        entries = Entries(connection=self.connection)
        for entry in entries.get_table().get_where({"link" : link}):
            return entry.id

    def add_links(self, link_urls):
        link_ids = []
        for link_url in link_urls:
            entry = self.get_link(link_url)
            if entry:
                link_ids.append(entry.id)
            else:
                builder = EntryDataBuilder(self.connection)
                link_id = builder.build_simple(link_url)
                link_ids.append(link_id)

                for error in builder.errors:
                    AppLogging(self.connection).error(error)

        return link_ids

    def is_url_blocked(self, url):
        entry_rules = EntryRules(self.connection)
        for rule in entry_rules.get_rules_for(url=url):
            if rule.block:
                return True

        return False

    def add_sources_text(self, raw_text):
        source_urls = read_line_things(raw_text)
        return self.add_sources(source_urls)

    def add_links_text(self, raw_text):
        links_urls = read_line_things(raw_text)
        return self.add_links(links_urls)

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
