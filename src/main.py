from pyhocon import ConfigFactory

from logging_utils import initLogging
from immoBot import ImmoBot
from immoBot import allSearchersFactory

if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/myConf.conf")
    initLogging(conf)
    bot = ImmoBot(conf, allSearchersFactory)
    bot.start()
