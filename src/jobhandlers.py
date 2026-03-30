import subprocess
import time
from datetime import datetime

from webtoolkit import (
   BaseUrl,
   RemoteUrl,
   UrlLocation,
   RemoteServer,
   PageRequestObject,
   HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
   HTTP_STATUS_TOO_MANY_REQUESTS,
)

from .controller import Controller
from .sources import Sources
from .entries import Entries
from .sourcedata import SourceData
from .socialdata import SocialData
from .applogging import AppLogging
from .entryrules import EntryRules
from .entryurlinterface import EntryUrlInterface
from .controller import Controller
from .urlhandler import UrlHandler
from .configurationentry import ConfigurationEntry


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
        if source is not None:
            self.check_source(source)
        # source might have been removed

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
            AppLogging(self.connection).error(f"URL:{source.url} No response")

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
                AppLogging(self.connection).error(f"URL:{source.url} No response")
                return

            return url

    def handle_valid_response(self, source, url, response):
        source_properties = url.get_properties()

        sources = Sources(self.connection)
        sources.set(source.url, source_properties)
        sources.delete_entries(source)

        entries = url.get_entries()
        for entry in entries:
            if self.is_entry_ok(entry, source):
                entries = Entries(self.connection)
                entries.add(entry, source)
                self.on_added_entry(entry)

    def on_added_entry(self, entry):
        rules = EntryRules(self.connection).get_rules_for(entry=entry)
        for rule in rules:
            if not rule.enabled:
                continue

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

    def process_source(self, index, source_id, source_count):
        sources = Sources(self.connection)
        source = sources.get(id=source_id)

        if not source:
            AppLogging(self.connection).debug(f"Source id: {source_id} Could not find source")
            return False

        if not source.enabled:
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is not enabled")
            return False

        rules = EntryRules(self.connection)
        if rules.is_entry_rule_triggered(source.url):
            sources = Sources(connection=self.connection)
            sources.delete(id=source.id)
            return False

        sources_data = SourceData(self.connection)

        if not sources_data.is_update_needed(source):
            now = datetime.now()
            AppLogging(self.connection).debug(f"{source.url}: Update not needed @ {now}")
            return False

        AppLogging(self.connection).debug(f"{index}/{source_count} {source.url} {source.title}: Reading")
        self.check_source(source)

        #writer = SourceWriter(connection=self.connection, source=source)
        #writer.write()

        AppLogging(self.connection).debug(f"{index}/{source_count} {source.url} {source.title}: Reading DONE")
        time.sleep(1)

        return True

    def get_source_url(self, source):
        handler = UrlHandler(connection=self.connection, link=source.url)
        url = handler.get_link_url()
        if not url:
            AppLogging(self.connection).notify(f"Removing invalid source:{source.url}")
            sources = Sources(self.connection)
            sources.delete(id=source.id)
        return url


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
            AppLogging(self.connection).error("URL:{enry.link} Response is None")
            return

        json_data = {}
        json_data["date_update_last"] = datetime.now()

        if not entry.title:
            json_data["title"] = url.get_title()
        if not entry.description:
            json_data["description"] = url.get_description()
        json_data["status_code"] = url.get_status_code()
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
        ##TODO implement rest

        self.connection.entries_table.update_json_data(id=entry.id, json_data=json_data)

        config_entry = ConfigurationEntry(self.connection).get()
        if config_entry.enable_social_data and config_entry.entry_update_fetches_social_data:
            controller = Controller(self.connection)
            controller.add_social_data(entry)


class CleanupJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)
        entries.cleanup()
        sources_data = SourceData(self.connection)
        sources_data.cleanup()
