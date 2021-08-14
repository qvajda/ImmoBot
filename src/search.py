from abc import ABC, abstractmethod
from pyhocon import ConfigFactory
from typing import List
from browser import launch_selenium


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


class MultiSearcher(Searcher):
    def __init__(self, conf: ConfigFactory,
                 searchers: List[Searcher]):
        super().__init__(conf)
        self.searchers = searchers

    def __enter__(self):
        for searcher in self.searchers:
            searcher.__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        for searcher in self.searchers:
            searcher.__exit__()
        # no particular treatment in case of exceptions

    def search_all(self) -> List[str]:
        res = {}
        for searcher in self.searchers:
            res.update(searcher.search_all())
        return res

    def search_new(self) -> List[str]:
        res = {}
        for searcher in self.searchers:
            res.update(searcher.search_new())
        return res
