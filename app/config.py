import yaml


class Config:
    def __init__(self, config_path="config.yaml"):
        self.config_path = config_path
        self.config = self.load_config()

    def load_config(self):
        with open(self.config_path, 'r') as file:
            return yaml.safe_load(file)

    def get_setting(self, key):
        return self.config.get(key)

    def update_setting(self, key, value):
        self.config[key] = value
        with open(self.config_path, 'w') as file:
            yaml.dump(self.config, file)
