import subprocess
import time

from webtoolkit import (
   BaseUrl,
   RemoteUrl,
   PageRequestObject,
   HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
   HTTP_STATUS_TOO_MANY_REQUESTS,
)

from .sources import Sources
from .entries import Entries
from .sourcedata import SourceData
from .applogging import AppLogging
from .entryrules import EntryRules


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
            AppLogging(self.connection).error(f"URL:{source.url} No response")

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
        link = entry.get("link")
        if not link:
            return False

        if source.xpath:
            try:
                if re.search(source.xpath, link) is None:
                    return False
            except re.error as E:
                AppLogging(self.connection).exc(E, "Incorrect pattern")
                return False

        return True

    def get_source_url(self, source):
        if not source:
            return
        request = PageRequestObject(source.url)
        request.timeout_s = 300

        config = self.connection.configurationentry.get()
        try:
            if self.is_remote_server() or self.is_config_remote_server():
                # TODO dates are strings
                location = config.remote_webtools_server_location
                if not location:
                    location = RemoteUrl.get_remote_server_location()

                url = RemoteUrl(request=request, remote_server_location=location)
            else:
                url = BaseUrl(request=request)
            return url
        except:
            AppLogging(self.connection).notify(f"Removing invalid source:{source.url}")
            sources = Sources(self.connection)
            sources.delete(id=source.id)

    def is_remote_server(self):
        return RemoteUrl.get_remote_server_location()
    
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

    def is_config_remote_server(self):
        config = self.connection.configurationentry.get()
        if config.remote_webtools_server_location is None:
            return False
        if config.remote_webtools_server_location == "":
            return False
        if config.remote_webtools_server_location == "None":
            return False
        return True



class CleanupJobHandler(GenericJobHandler):
    def run(self):
        self.connection = DbConnection(self.table_name)
        self.controller = Controller(connection=self.connection)

        self.add_due_sources()

        entries = Entries(self.connection)
        entries.cleanup()
        sources_data = SourceData(self.connection)
        sources_data.cleanup()

        self.controller.close()
        self.connection.close()

    def add_due_sources(self):
        status = False

        sources = self.controller.get_sources_to_add()
        if sources:
            self.start_reading = True
            self.controller.add_sources(sources)
            status = True

        return status
