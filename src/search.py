from abc import ABC, abstractmethod
from pyhocon import ConfigFactory
from typing import List
from browser import launch_selenium
from immoweb import ImmowebSearcher


class Searcher(ABC):
    def __init__(self, conf: ConfigFactory):
        self.conf = conf

    def __enter__(self):
        self.browser = launch_selenium(self.conf["general"])
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.browser.quit()
        # no particular treatment in case of exceptions

    @abstractmethod
    def search_all(self) -> List[str]:
        """
          Method to search properties on given immo provider
          and find all the latest listings
        """
        pass

    @abstractmethod
    def search_new(self) -> List[str]:
        """
          Method to search properties on given immo provider
          and find only the new listings not previously found
        """
        pass


def searchFactory(conf: ConfigFactory) -> Searcher:
    return ImmowebSearcher(conf)


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    with ImmowebSearcher(conf) as immoweb:
        immoweb.search_new()
