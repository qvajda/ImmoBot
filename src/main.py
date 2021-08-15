from pyhocon import ConfigFactory
from immoBot import ImmoBot
from immoBot import allSearchersFactory

if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/myConf.conf")
    bot = ImmoBot(conf, allSearchersFactory)
    bot.start()
