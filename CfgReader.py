# Module allowing to read parameters from .cfg files

import configparser
from pprint import pprint


class CfgFileParser:
    # Read the LkdParse.cfg file to get parameters
    Config = {}

    def file_reader(self, filename):
        # Open the file
        config = configparser.ConfigParser()
        config.read(filename)
        # Iterate over sections and create nested dictionaries to store key-value pairs
        for section in config.sections():
            self.Config[section] = {}
            for key in config[section]:
                self.Config[section][key] = config[section][key]
        return self.Config


if __name__ == '__main__':
    cfg_reader = CfgFileParser()
    test = cfg_reader.file_reader('CAM4Config.cfg')
    pprint(test)
