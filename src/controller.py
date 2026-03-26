from pathlib import Path
from datetime import datetime
from .sourcedata import SourceData
from .sources import Sources
from .entryrules import EntryRules


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

    def add_sources(self, sources):
        self.start_reading = True

        entry_rules = EntryRule(self.connection)
        for source_url in sources:
            if not entry_rules.is_entry_rule_triggered(source_url):
                sources = Sources(self.connection)
                sources.set(source_url)

    def add_sources_text(self, raw_text):
        # write raw_text to file
        output_path = Path("sources.txt")
        with output_path.open("a", encoding="utf-8", errors="ignore") as f:
            f.write("\n")
            f.write(raw_text)

    def get_sources_to_add(self):
        output_path = Path("sources.txt")
        if output_path.exists():
            raw_text = output_path.read_text(encoding="utf-8")
            if raw_text:
                sources = read_line_things(raw_text)
                output_path.unlink()
                return sources

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
