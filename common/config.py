import json
from pathlib import Path


class Config:
    def __init__(self, fp="instaloader.json"):
        self.fp = fp
        # Add path checking
        if self.fp:
            with open(Path(self.fp), 'r') as fcc_file:
                self.config_data = json.load(fcc_file)
        else:
            raise Exception("File path is empty")

    def get_telegram_token(self):
        return self.get_telegram_config()['token']

    def get_telegram_config(self):
        return self.config_data['telegram']

    def get_instaloader_config(self):
        return self.config_data['instaloader']

    def get_instaloader_param(self, param: str):
        return self.get_instaloader_config()[param]

    def get_custom_node(self, node_name):
        return self.config_data[node_name]
