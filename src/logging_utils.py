import logging
from logging.config import dictConfig
from pyhocon import ConfigFactory


def initLogging(conf: ConfigFactory):
    """ Initialise logger from the config file"""
    log_conf = conf["logging"]
    # Convert levels from human readable config to their 'logging' equivalent
    log_conf.put("handlers.h.level",
                 getattr(logging,
                         log_conf["handlers.h.level"]))
    log_conf.put("root.level",
                 getattr(logging,
                         log_conf["root.level"]))
    dictConfig(log_conf)
