from webtoolkit import RemoteServer


class Wizard(object):
    def __init__(self, connection):
        self.connection = connection

    def init(self, config_entry):
        from .controller import Controller

        controller = Controller(self.connection)
        controller.update_configuration(config_entry)
        # self.init_sources(init_sources)

        location = RemoteServer.get_remote_server_location()
        if not location:
            location = "http://127.0.0.1:3000"

        if RemoteServer.is_remote_server_ok(location):
            json_data["remote_webtools_server_location"] = location
            ConfigurationEntry.get_table().update_json_data(config_entry.id, json_data)

    def init_sources(self, init_sources):
        if init_sources is None:
            return

        for source_url in init_sources:
            sources = Sources(self.connection)
            sources.set(source_url)

