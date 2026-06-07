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

    def add_configuration(self):
        config = ConfigurationEntry(self.connection)
        if config.count() != 0:
            return

        json_data = {}
        json_data["instance_title"] = ""
        json_data["instance_description"] = ""
        json_data["instance_internet_location"] = ""
        json_data["favicon_internet_url"] = ""
        json_data["view_access_type"] = ""
        json_data["download_access_type"] = ""
        json_data["add_access_type"] = ""
        json_data["logging_level"] = 10
        json_data["initialized"] = False
        json_data["initialization_type"] = ConfigurationEntry.CONFIGURATION_SEARCH_ENGINE
        json_data["enable_background_jobs"] = True
        json_data["block_job_queue"] = False
        json_data["use_internal_scripts"] = False
        json_data["auto_store_thumbnails"] = False
        json_data["thread_memory_threshold"] = 0

        json_data["enable_keyword_support"] = False
        json_data["enable_domain_support"] = False
        json_data["enable_file_support"] = False
        json_data["enable_link_archiving"] = False
        json_data["enable_source_archiving"] = False
        json_data["enable_crawling"] = False
        json_data["enable_social_data"] = False

        json_data["accept_dead_links"] = False
        json_data["accept_ip_links"] = False
        json_data["accept_domain_links"] = False
        json_data["accept_non_domain_links"] = False
        json_data["accept_unknown_links"] = False
        #json_data["accept_onion_links"] = False
        json_data["accept_same_hashes"] = False

        json_data["auto_crawl_sources"] = False
        json_data["auto_scan_new_entries"] = False
        json_data["auto_scan_updated_entries"] = False
        json_data["new_entries_merge_data"] = False
        json_data["new_entries_use_clean_data"] = False
        json_data["new_entries_fetch_social_data"] = False
        json_data["browse_entries_fetch_social_data"] = False
        json_data["browse_entry_fetch_social_data"] = False

        json_data["entry_update_via_internet"] = False
        json_data["entry_update_fetches_social_data"] = False
        json_data["log_remove_entries"] = False
        json_data["auto_create_sources"] = False
        json_data["default_source_state"] = False

        json_data["prefer_https_links"] = False
        json_data["prefer_non_www_links"] = False
        json_data["keep_social_data"] = False
        json_data["sources_refresh_period"] = 0
        json_data["days_to_move_to_archive"] = 0
        json_data["days_to_remove_links"] = 0
        json_data["days_to_remove_stale_entries"] = 0
        json_data["days_to_check_std_entries"] = 0
        json_data["days_to_check_stale_entries"] = 0
        json_data["days_to_remove_social_data"] = 0
        json_data["remove_entry_vote_threshold"] = 0
        json_data["number_of_update_entries"] = 0

        json_data["number_of_update_entries"] = 0
        json_data["remote_webtools_server_location"] = ""

        json_data["track_user_actions"] = False
        json_data["track_user_searches"] = False
        json_data["track_user_navigation"] = False
        json_data["max_user_entry_visit_history"] = 500
        json_data["max_number_of_user_search"] = 500
        json_data["vote_min"] = 500
        json_data["vote_max"] = 500
        json_data["number_of_comments_per_day"] = 500

        json_data["time_zone"] = ""
        json_data["show_icons"] = True
        json_data["thumbnails_as_icons"] = True
        json_data["small_icons"] = True
        json_data["local_icons"] = True
        json_data["highlight_bookmarks"] = True
        #json_data["click_behavior_modal_window"] = True
        json_data["links_per_page"] = True
        json_data["sources_per_page"] = True
        json_data["max_links_per_page"] = True
        json_data["max_sources_per_page"] = True
        json_data["max_number_of_related_links"] = True
        json_data["entries_visit_alpha"] = 1.0
        json_data["entries_dead_alpha"] = 1.0
        json_data["debug_mode"] = False
        json_data["cleanup_time"] = datetime.now().time()

        #config = ConfigurationEntry(self.connection)
        return self.connection.configurationentry.insert_json_data(json_data)

    def update_configuration(self, config_entry):
        json_data = {}
        json_data["initialized"] = True
        json_data["enable_social_data"] = False
        json_data["new_entries_fetch_social_data"] = False
        json_data["entry_update_fetches_social_data"] = False
        json_data["initialization_type"] = ConfigurationEntry.CONFIGURATION_SEARCH_ENGINE

        return self.connection.configurationentry.update_json_data(id=config_entry.id, json_data=json_data)

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
