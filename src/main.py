from pyhocon import ConfigFactory

from logging_utils import initLogging
from immoBot import ImmoBotTelegram
from immoBot import allSearchersFactory

if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/myConf.conf")
    initLogging(conf)
    bot = ImmoBotTelegram(conf, allSearchersFactory)
    bot.start()
