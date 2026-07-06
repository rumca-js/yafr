from webtoolkit import (
   BaseUrl,
   RemoteUrl,
   PageRequestObject,
)

from linkarchivetools.model import EntryRules, AppLogging


class UrlHandler(object):
    def __init__(self, connection, link):
        self.connection = connection
        self.link = link

    def get_link_url(self):
        link = self.link

        request = PageRequestObject(link)
        request.timeout_s = 300

        config = self.connection.configurationentry.get()
        try:
            if self.is_remote_server() or self.is_config_remote_server():
                # TODO dates are strings
                location = config.remote_webtools_server_location
                if not location:
                    location = RemoteUrl.get_remote_server_location()

                url = RemoteUrl(request=request, remote_server_location=location, client_id=config.instance_title)
                url.url = request.url # TODO remove it
            else:
                url = BaseUrl(request=request)
            return url
        except Exception as E:
            AppLogging(self.connection).exc(E, f"Cannot obtain data for:{link}")

    def is_config_remote_server(self):
        config = self.connection.configurationentry.get()
        if config.remote_webtools_server_location is None:
            return False
        if config.remote_webtools_server_location == "":
            return False
        if config.remote_webtools_server_location == "None":
            return False
        return True

    def is_remote_server(self):
        return RemoteUrl.get_remote_server_location()

    def is_blocked(self):
        blocks = BlockEntry(self.connection)
        if blocks.is_blocked(self.link):
            return True

        rules = EntryRules(self.connection)
        if rules.is_url_blocked(self.link):
            return True
        return False

    def is_valid(self):
        rules = EntryRules(self.connection)
        if rules.is_url_blocked():
            return False

        return True

    def is_invalid(self):
        rules = EntryRules(self.connection)
        if rules.is_url_blocked():
            return True

        return False

    def get_social_properties(self):
        location = RemoteUrl.get_remote_server_location()
        url = RemoteUrl(request=request, remote_server_location=location)
        return url.get_social_properties()
