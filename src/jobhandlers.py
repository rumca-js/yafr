import subprocess
import time
import json
from datetime import datetime

from webtoolkit import (
   UrlLocation,
   PageRequestObject,
   ContentLinkParser,
   HTTP_STATUS_CODE_SERVER_TOO_MANY_REQUESTS,
   HTTP_STATUS_TOO_MANY_REQUESTS,
)

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
   BackgroundJob,
   BlockEntry,
   ReflectedTable,
)

from .controller import Controller
from .entryurlinterface import EntryUrlInterface
from .controller import Controller
from .urlhandler import UrlHandler


class GenericJobHandler(object):
    def __init__(self, connection, job, table_name):
        self.connection = connection
        self.job = job
        self.table_name = table_name

    def get_cfg(self):
        if not self.job:
            return {}

        cfg = {}
        if self.job.args != "":
            try:
                cfg = json.loads(self.job.args)
            except ValueError as E:
                pass
            except TypeError as E:
                pass
        return cfg

    def close(self):
        self.connection.backgroundjob.delete(id=self.job.id)

    def run(self):
        """
        @return True, if job has been processed correctly and should be removed
        """
        return True


class ProcessSourceJobHandler(GenericJobHandler):

    def run(self):
        source_id = int(self.job.subject)
        sources = Sources(self.connection)
        source = sources.get(id=source_id)

        if not source:
            AppLogging(self.connection).debug(f"Source id: {source_id} Could not find source")
            return True

        self.update_source_type(source)

        source = sources.get(id=source_id)

        if not source.enabled:
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is not enabled")
            return True

        blocks = BlockEntry(self.connection)
        if blocks.is_blocked(source.url):
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is blocked by block rules")
            sources = Sources(connection=self.connection)
            sources.delete(id=source.id)
            return True

        rules = EntryRules(self.connection)
        if rules.is_url_blocked(source.url):
            AppLogging(self.connection).debug(f"Source id: {source_id} Source is blocked by entry rules")
            sources = Sources(connection=self.connection)
            sources.delete(id=source.id)
            return True

        sources_data = SourceData(self.connection)
        if not sources_data.is_update_needed(source):
            now = datetime.now()
            AppLogging(self.connection).debug(f"{source.url}: Update not needed @ {now}")
            return True

        return self.check_source(source)

    def update_source_type(self, source):
        if not source.source_type:
            config_entry = ConfigurationEntry(self.connection).get()
            if config_entry.initialization_type == ConfigurationEntry.CONFIGURATION_SEARCH_ENGINE:
                sources = Sources(connection=self.connection)
                sources.get_table().update_json_data(source.id, json_data={"source_type":Sources.SOURCE_TYPE_PARSE})

            else:
                sources = Sources(connection=self.connection)
                sources.get_table().update_json_data(source.id, json_data={"source_type":Sources.SOURCE_TYPE_RSS})

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
            return False

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
        if source.source_type == Sources.SOURCE_TYPE_RSS:
            return self.handle_valid_response__rss(source, url, response)
        elif source.source_type == Sources.SOURCE_TYPE_PARSE:
            return self.handle_valid_response__links(source, url, response)
        elif not source.source_type:
            config_entry = ConfigurationEntry(self.connection).get()
            if config_entry.initialization_type == ConfigurationEntry.CONFIGURATION_SEARCH_ENGINE:
                return self.handle_valid_response__links(source, url, response)
            else:
                return self.handle_valid_response__rss(source, url, response)

    def handle_valid_response__links(self, source, url, response):
        source_properties = url.get_properties()

        sources = Sources(self.connection)
        sources.set(source.url, source_properties, source_type=source.source_type)

        links = self.get_links(url)
        entries = Entries(connection=self.connection)

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
                BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL, subject=str(entry_id))

    def get_links(self, url):
        # TODO this should be from configuration
        accept_link_arguments = False

        response = url.get_response()
        if response:
            text = response.get_text()

            parser = ContentLinkParser(url.url, text)
            links = parser.get_links()

            if not accept_link_arguments:
                result = []
                for link in links:
                    location = UrlLocation(url=link)
                    new_location = location.get_no_arg_link()
                    new_location_str = new_location.url

                    if new_location_str:
                        wh = new_location_str.find("#")
                        if wh >= 0: 
                            new_location_str = new_location_str[:wh]

                    result.append(new_location_str)

                links = result

            result = []
            for link in links:
                location = UrlLocation(link)
                cleaned_location = location.get_clean()
                result.append(cleaned_location.url)

            return result

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
        source_entries_json = url.get_entries()

        sources = Sources(self.connection)
        sources.set(source.url, source_properties)

        entries = Entries(self.connection)

        entries_where = entries.get_table().get_where({"source_id" : source.id})
        entry_ids = []
        for entry in entries_where:
            is_entry_in_source_now = False
            for json_entry in source_entries_json:
                json_entry_link = json_entry.get("link")
                if entry.link == json_entry_link:
                    is_entry_in_source_now = True
                    break

            if not is_entry_in_source_now and self.is_entry_to_be_removed(entry):
                entry_ids.append(entry.id)

        for entry_id in entry_ids:
            print("Removing ID:{}".format(entry_id))
            entries.delete(id=entry_id)

        for source_entry_json in source_entries_json:
            entry_json_link = source_entry_json.get("link")
            if self.is_in_db(entry_json_link):
                continue

            if self.is_entry_ok(source_entry_json, source):
                entries.add(source_entry_json, source)
                self.on_added_entry(source_entry_json)

    def is_in_db(self, entry_link):
        entries = Entries(self.connection)

        entries_where = entries.get_table().get_where({"link" :  entry_link})
        entries_where = list(entries_where)
        if len(entries_where) > 0:
            return True
        return False


class UpdateLinkJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)

        try:
            entry_id = int(self.job.subject)
        except Exception as E:
            AppLogging(self.connection).exc(E)
            return

        entry = entries.get(id=entry_id)
        return self.update_entry(entry)

    def update_entry(self, entry):
        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        response = url.get_response()
        if response is None:
            AppLogging(self.connection).error(f"URL:{enry.link} Response is None")
            return False

        json_data = {}
        json_data["date_update_last"] = datetime.now()

        if not entry.title:
            json_data["title"] = url.get_title()
        if not entry.description:
            json_data["description"] = url.get_description()
        if url.get_thumbnail():
            json_data["thumbnail"] = url.get_thumbnail()
        if url.get_author():
            json_data["author"] = url.get_author()
        if url.get_album():
            json_data["album"] = url.get_album()
        if not entry.date_created:
            json_data["date_created"] = datetime.now()
        if not entry.date_published and url.get_date_published():
            json_data["date_published"] = url.get_date_published()

        json_data["status_code"] = url.get_status_code()
        json_data["contents_hash"] = url.get_hash()
        json_data["body_hash"] = url.get_body_hash()
        json_data["meta_hash"] = url.get_meta_hash()

        if response.is_invalid():
            json_data["date_dead_since"] = datetime.now()
        else:
            json_data["date_dead_since"] = None

        if entry.link.endswith("/"):
            json_data["link"] = entry.link[:-1]

        self.connection.entries_table.update_json_data(id=entry.id, json_data=json_data)

        config_entry = ConfigurationEntry(self.connection).get()
        if config_entry.enable_social_data and config_entry.entry_update_fetches_social_data:
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL, subject=str(entry.id))

        return True


class ResetLinkJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)
        try:
            entry_id = int(self.job.subject)
        except Exception as E:
            AppLogging(self.connection).exc(E)
            return

        entry = entries.get(id=entry_id)
        return self.reset_entry(entry)

    def reset_entry(self, entry):
        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        response = url.get_response()
        if response is None:
            AppLogging(self.connection).error("URL:{enry.link} Response is None")
            return False

        json_data = {}
        json_data["date_updated"] = datetime.now()

        if url.get_title():
            json_data["title"] = url.get_title()
        if url.get_description():
            json_data["description"] = url.get_description()
        if url.get_thumbnail():
            json_data["thumbnail"] = url.get_thumbnail()
        if url.get_author():
            json_data["author"] = url.get_author()
        if url.get_album():
            json_data["album"] = url.get_album()
        if not entry.date_created:
            json_data["date_created"] = datetime.now()
        if not entry.date_published and url.get_date_published():
            json_data["date_published"] = url.get_date_published()

        json_data["status_code"] = url.get_status_code()
        json_data["contents_hash"] = url.get_hash()
        json_data["body_hash"] = url.get_body_hash()
        json_data["meta_hash"] = url.get_meta_hash()

        if response.is_invalid():
            json_data["date_dead_since"] = datetime.now()
        else:
            json_data["date_dead_since"] = None

        if entry.link.endswith("/"):
            json_data["link"] = entry.link[:-1]

        self.connection.entries_table.update_json_data(id=entry.id, json_data=json_data)

        config_entry = ConfigurationEntry(self.connection).get()
        if config_entry.enable_social_data and config_entry.entry_update_fetches_social_data:
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL, subject=str(entry.id))

        return True


class DownloadSocialDataJobHandler(GenericJobHandler):
    def run(self):
        entries = Entries(self.connection)

        try:
            entry_id = int(self.job.subject)
        except Exception as E:
            AppLogging(self.connection).exc(E)
            return

        entry = entries.get(id=entry_id)
        return self.download_social_Data(entry)

    def download_social_Data(self, entry):
        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        social_properties = url.get_social_properties()
        if social_properties is None:
            AppLogging(self.connection).error(f"URL:{entry.link} Social properties are None")
            return False

        if self.is_all_none(social_properties):
            AppLogging(self.connection).error(f"URL:{entry.link} Social properties are all None")
            return False

        controller = SocialData(self.connection)
        controller.add(entry_id = entry.id, social_data = social_properties)

        return True

    def is_all_none(self, json_obj):
        """
        Returns indication if json object elements are all true
        """
        # indicator of unsupported on crawler buddy
        all_values_are_none = True
        for key, value in json_obj.items():
            if value is not None:
                all_values_are_none = False

        return all_values_are_none


class AddLinkJobHandler(GenericJobHandler):
    def run(self):
        link_url = self.job.subject

        cfg = self.get_cfg()

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

        bookmarked = cfg.get("bookmarked")
        if bookmarked:
            entry_json["bookmarked"] = True

        entries.add(entry_json)
        return True


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

        self.add_backgroundjob_history()
        return True

    def add_backgroundjob_history(self):
        self.connection.backgroundjobhistory.truncate()

        json_data = {}
        json_data["job"] = BackgroundJob.JOB_CLEANUP
        json_data["task"] = ""
        json_data["subject"] = ""
        json_data["args"] = ""
        json_data["date_created"] = datetime.now()

        self.connection.backgroundjobhistory.insert_json_data(json_data=json_data)
