from datetime import datetime

from linkarchivetools.model import (
   AppLogging,
   BackgroundJob,
   ConfigurationEntry,
)

from .urlhandler import UrlHandler


class EntryUpdater(object):
    def __init__(self, connection, entry):
        self.entry = entry
        self.connection=connection

    def update_data(self, entry):
        """
        Does not check manual status. If job was added needs to be performed
        """
        entry = self.entry

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

        # TODO does not work
        #if config_entry.entry_update_download_audio:
        #    BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_DOWNLOAD_SOCIAL, subject=str(entry.id))

    def reset_data(self, entry):
        """
        Does not check manual status. If job was added needs to be performed
        """
        entry = self.entry

        handler = UrlHandler(connection=self.connection, link=entry.link)
        url = handler.get_link_url()
        response = url.get_response()
        if response is None:
            AppLogging(self.connection).error("URL:{enry.link} Response is None")
            return False

        json_data = {}
        json_data["date_update_last"] = datetime.now()

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


class EntriesUpdater(object):
    def __init__(self, connection):
        self.connection = connection

    def get_generic_entries(self):
        config_entry = ConfigurationEntry(self.connection).get()
        number_of_update_entries = config_entry.number_of_update_entries

        if not number_of_update_entries:
            return

        # TODO should be part of configuration
        days_to_update = 5

        date_cutoff = datetime.now() - timedelta(days=days_to_update)

        table = self.connection.entries_table.get_table()
        entries_select = (select(table)
                          .order_by(table.c.page_rating_votes.desc())
                          .where(
                              and_(
                                 (or_(table.c.date_update_last.is_(None),
                                 table.c.date_update_last < date_cutoff),
                                  table.c.manual_status_code != 0)
                              )
                          )
                          .limit(number_of_update_entries)
                         )

        entries = self.connection.connection.execute(entries_select)
        return list(entries)

    def update(self):
        entries = self.get_generic_entries()

        for entry in entry_objs:
            BackgroundJob(self.connection).create_single_job(job_name=BackgroundJob.JOB_LINK_UPDATE_DATA, subject=str(entry.id))
