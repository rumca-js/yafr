import json
from pathlib import Path
from datetime import datetime, timedelta


class SocialData(object):
    def __init__(self, connection):
        self.connection = connection

    def get(self, entry_id):
        social_datas = self.connection.socialdata.get_where({"entry_id" : entry_id})
        for social_data in social_datas:
            return social_data

    def add(self, entry_id, social_data):
        existing_social_data = self.get(entry_id)

        if existing_social_data:
            social_data["id"] = existing_social_data["id"]

        social_data["entry_id"] = entry_id
        social_data["date_updated"] = datetime.now()

        valid = self.is_valid(social_data)
        if not valid:
            return

        if existing_social_data:
            self.connection.socialdata.update_json_data(id=existing_social_data.id, json_data=social_data)
        else:
            self.connection.socialdata.insert_json_data(json_data=social_data)

    def is_valid(self, social_data_json):
        valid = False
        for key, value in social_data_json.items():
            if key is not None and value is not None:
                valid = True
        return valid

    def remove(self, entry_id):
        self.connection.social_data.delete_where({"entry_id" : entry_id})
