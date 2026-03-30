from datetime import datetime


class EntryUrlInterface(object):
    def __init__(self, url=None, source=None):
        self.source = source
        self.url = url

    def get_entry_json(self):
        url = self.url
        source = self.source

        entry = {}
        entry["link"] = url.url
        entry["date_created"] = datetime.now()
        entry["title"] = url.get_title()
        entry["description"] = url.get_description()
        entry["status_code"] = url.get_status_code()
        entry["thumbnail"] = url.get_thumbnail()

        if source:
            entry["source_id"] = source.id
            entry["source_url"] = source.url

        return entry
