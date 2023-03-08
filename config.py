import os
import yaml

config_file_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
with open(config_file_path) as config_file:
    config = yaml.load(config_file, Loader=yaml.FullLoader)