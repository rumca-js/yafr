import subprocess
import time
from datetime import datetime

from webtoolkit import (
   BaseUrl,
   RemoteUrl,
   UrlLocation,
   RemoteServer,
   PageRequestObject,
   ContentLinkParser,
   HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
   HTTP_STATUS_TOO_MANY_REQUESTS,
)

from .controller import Controller
from linkarchivetools.model import (
   Sources,
   Entries,
   SourceData,
   SocialData,
   AppLogging,
   EntryRules,
   EntryTags,
   ConfigurationEntry,
   CheckLater,
)

from .entryurlinterface import EntryUrlInterface
from .controller import Controller
from .urlhandler import UrlHandler


class GenericJobHandler(object):
    def __init__(self, connection, job, table_name):
        self.connection = connection
        self.job = job
        self.table_name = table_name

    def close(self):
        self.connection.backgroundjob.delete(id=self.job.id)

    def run(self):
        pass


class ProcessSourceJobHandler(GenericJobHandler):

    def run(self):
        source_id = int(self.job.subject)
        sources = Sources(self.connection)
        source = sources.get(id=source_id)

        if not source:
            AppLogging(self.connection).debug(f"Source id: {source_id} Could not find source")
            return False

        if not source.enabled:
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is not enabled")
            return False

        rules = EntryRules(self.connection)
        if rules.is_url_blocked(source.url):
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is blocked")
            sources = Sources(connection=self.connection)
            sources.delete(id=source.id)
            return False

        sources_data = SourceData(self.connection)
        if not sources_data.is_update_needed(source):
            now = datetime.now()
            AppLogging(self.connection).debug(f"{source.url}: Update not needed @ {now}")
            return False

        self.check_source(source)

    def check_source(self, source):
        url = self.get_response_real(source)

        if not url:
            return

        response = url.get_response()
        if response is not None:
            if response.is_valid():
                self.handle_valid_response(source, url, response)

                sourcedata = SourceData(self.connection)
                sourcedata.mark_read(source)
            else:
                AppLogging(self.connection).error(f"URL:{source.url} Response is invalid")
        else:
            AppLogging(self.connection).error(f"Source ID:{source.id} URL:{source.url} No response")

        return True

    def get_response_real(self, source):
        while True:
            url = self.get_source_url(source)
            if not url:
                return

            response = url.get_response()
            if response:
                if (response.get_status_code() == HTTP_STATUS_TOO_MANY_REQUESTS or
                    response.get_status_code() == HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS):
                    AppLogging(self.connection).debug("Retry of request")
                    continue
            if response is None:
                AppLogging(self.connection).error(f"Source ID:{source.id} URL:{source.url} No response")
                return

            return url

    def is_entry_to_be_removed(self, entry):
        if entry.bookmarked:
            return False

        check_later = CheckLater(self.connection)
        if check_later.get(entry_id = entry.id):
            return False

        return True

    def on_added_entry(self, entry_json):
        if EntryRules(self.connection).is_url_blocked(url=entry_json["link"]):
            return

            """
            if rule.script:
                subprocess.run(rule.script, shell=True, capture_output=True, text=True)
            """

    def is_entry_ok(self, entry, source):
        if entry is None:
            return False

        link = entry.get("link")
        if not link:
            return False

        if source.xpath and source.xpath != "":
            try:
                if re.search(source.xpath, link) is None:
                    return False
            except re.error as E:
                AppLogging(self.connection).exc(E, "Incorrect pattern")
                return False

        return True

    def on_done(self, response):
        pass

    def get_source_url(self, source):
        handler = UrlHandler(connection=self.connection, link=source.url)
        url = handler.get_link_url()
        if not url:
            AppLogging(self.connection).notify(f"Removing invalid source:{source.url}")
            sources = Sources(self.connection)
            sources.delete(id=source.id)
        return url

    def handle_valid_response(self, source, url, response):
        return self.handle_valid_response__rss(source, url, response):

    def handle_valid_response__links(self, source, url, response):
        source_properties = url.get_properties()

        sources = Sources(self.connection)
        sources.set(source.url, source_properties)

        links = self.get_links(url)
        entries = Entries(self.connection)

        for link in links:
            exists = self.connection.entries_table.exists(link=link)
            if not exists and UrlLocation(link).is_webpage_link():
                self.process_link(link, source)

    def process_link(self, link, source):
        entry_json = self.link_to_entry(link, source)
        if self.is_entry_ok(entry_json, source):
            entries = Entries(self.connection)
            entry_id = entries.add(entry_json, source)
            entry = entries.get(id=entry_id)

            config_entry = ConfigurationEntry(self.connection).get()
            if config_entry.enable_social_data and config_entry.new_entries_fetch_social_data:
                controller = Controller(self.connection)
                controller.add_social_data(entry)

    def get_links(self, url):
        response = url.get_response()
        if response:
            text = response.get_text()

            parser = ContentLinkParser(url.url, text)
            return parser.get_links()
        return []

    def link_to_entry(self, link, source):
        handler = UrlHandler(connection=self.connection, link=link)
        url = handler.get_link_url()
        url.get_response()

        entry_interface = EntryUrlInterface(url=url, source=source)
        entry = entry_interface.get_entry_json()

        return entry

    def handle_valid_response__rss(self, source, url, response):
        source_properties = url.get_properties()

        sources = Sources(self.connection)
        sources.set(source.url, source_properties)

        entries = Entries(self.connection)

        entries_where = entries.get_table().get_where({"source_id" : source.id})
        for entry in entries_where:
            if self.is_entry_to_be_removed(entry):
                entries.delete(id=entry.id)
            else:
                continue

        entry_jsons = url.get_entries()
        for entry_json in entry_jsons:
            if self.is_entry_ok(entry_json, source):
                entries.add(entry_json, source)
                self.on_added_entry(entry_json)


class UpdateLinkJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)

        try:
            entry_id = int(self.job.subject)
        except Exception as E:
            AppLogging(self.connection).exc(E)
            return

        entry = entries.get(id=entry_id)
        self.update_entry(entry)

    def update_entry(self, entry):
        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        response = url.get_response()
        if response is None:
            AppLogging(self.connection).error(f"URL:{enry.link} Response is None")
            return

        json_data = {}
        json_data["date_update_last"] = datetime.now()

        if not entry.title:
            json_data["title"] = url.get_title()
        if not entry.description:
            json_data["description"] = url.get_description()
        json_data["status_code"] = url.get_status_code()

        if response.is_invalid():
            json_data["date_dead_since"] = datetime.now()
        else:
            json_data["date_dead_since"] = None

        ##TODO implement rest

        self.connection.entries_table.update_json_data(id=entry.id, json_data=json_data)

        config_entry = ConfigurationEntry(self.connection).get()
        if config_entry.enable_social_data and config_entry.entry_update_fetches_social_data:
            controller = Controller(self.connection)
            controller.add_social_data(entry)


class ResetLinkJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)
        try:
            entry_id = int(self.job.subject)
        except Exception as E:
            AppLogging(self.connection).exc(E)
            return

        entry = entries.get(id=entry_id)
        self.reset_entry(entry)

    def reset_entry(self, entry):
        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        response = url.get_response()
        if response is None:
            AppLogging(self.connection).error("URL:{enry.link} Response is None")
            return

        json_data = {}
        json_data["date_updated"] = datetime.now()

        if url.get_title():
            json_data["title"] = url.get_title()
        if url.get_description():
            json_data["description"] = url.get_description()
        json_data["status_code"] = url.get_status_code()

        if response.is_invalid():
            json_data["date_dead_since"] = datetime.now()
        else:
            json_data["date_dead_since"] = None

        ##TODO implement rest

        self.connection.entries_table.update_json_data(id=entry.id, json_data=json_data)

        config_entry = ConfigurationEntry(self.connection).get()
        if config_entry.enable_social_data and config_entry.entry_update_fetches_social_data:
            controller = Controller(self.connection)
            controller.add_social_data(entry)


class AddLinkJobHandler(GenericJobHandler):
    def run(self):
        link_url = self.job.subject

        entries = Entries(connection=self.connection)
        if entries.exists(link=link_url):
            return

        handler = UrlHandler(connection=self.connection, link=link_url)
        url = handler.get_link_url()

        response = url.get_response()

        if not response.is_valid():
            AppLogging(self.connection).error(f"URL:{link_url} Response is not valid {response}")
            return

        if not url.is_valid():
            AppLogging(self.connection).error(f"URL:{link_url} Url object is not valid")
            return

        interface = EntryUrlInterface(url=url)
        entry_json = interface.get_entry_json()
        if not entry_json:
            AppLogging(self.connection).error(f"URL:{link_url} Link data are not valid")
            return

        entries.add(entry_json)


class CleanupJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)
        entries.cleanup()

        sources_data = SourceData(self.connection)
        sources_data.cleanup()

        social_data = SocialData(self.connection)
        social_data.cleanup()

        tags = EntryTags(self.connection)
        tags.cleanup()
