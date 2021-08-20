from abc import ABC, abstractmethod
from pyhocon import ConfigFactory
from typing import List
from typing import Optional
from typing import Dict
import shelve
from logging import getLogger

from details import DetailFinder
from details import Details
from browser import launch_selenium


class Searcher(ABC):
    def __init__(self, conf: ConfigFactory,
                 detailFinder: Optional[DetailFinder] = None):
        self.conf = conf
        if detailFinder is None:
            detailFinder = DetailFinder(conf)
        self.detailFinder = detailFinder
        self.logger = getLogger()

    def __enter__(self):
        # startup selenium browser
        self.browser = launch_selenium(self.conf["general"])
        # open up connection to shelve
        shelve_dir = self.conf["general.shelve_dir"]
        self.shelf = shelve.open(f"{shelve_dir}{self.name}")
        if "prevs" not in self.shelf:  # first time setup
            self.shelf["prevs"] = {}
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.shelf.close()
        self.browser.quit()
        # no particular treatment in case of exceptions

    @property
    @abstractmethod
    def name(self):
        pass

    @abstractmethod
    def search_all(self) -> List[str]:
        """
          Method to search properties on given immo provider
          and find all the latest listings.
          Properties IDs and urls are returned
        """
        pass

    def search_new(self) -> Dict[str, Details]:
        """
          Method to search properties on given immo provider
          and find only the new listings not previously found.
          IDs and full details are returned.
        """
        all_properties = self.search_all()
        prevs = self.shelf["prevs"]
        new_properties = {k: v for
                          k, v in all_properties.items() if
                          k not in prevs}
        if len(new_properties) > 0:
            self.logger.info(
                f"Found {len(new_properties)} new properties on {self.name}:"
                f"{list(new_properties.keys())}")
            prevs.update(new_properties)
            self.shelf["prevs"] = prevs  # TODO check if this line is needed
            self.shelf.sync()
        else:
            self.logger.info(f"No new properties found on {self.name}")
            if self.conf[f"{self.name}.test_send"]:
                self.logger.debug(
                    "Test sending with one of the latest seen properties")
                new_properties = {k: v
                                  for k, v in
                                  list(all_properties.items())[0:1]}
        return self.detailFinder.findFor(new_properties)

    def forget(self, properties: List[str]) -> None:
        """
        Forgets ever seeing the given properties.
        When searching for new properties, these forgotten properties
        will reappear again.
        """
        prevs_sanitized = {prop: v for prop, v in
                           self.shelf["prevs"].items() if
                           prop not in properties}
        forgotten = [prop for prop in self.shelf["prevs"] if
                     prop not in prevs_sanitized]
        self.logger.debug(f"The following {self.name} "
                          f"properties about to be {forgotten = }")
        self.shelf["prevs"] = prevs_sanitized
        self.shelf.sync()


class MultiSearcher(Searcher):
    name = "MultiSearcher"

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
            searcher.__exit__(exception_type, exception_value, traceback)
        # no particular treatment in case of exceptions

    def search_all(self) -> List[str]:
        res = {}
        for searcher in self.searchers:
            res.update(searcher.search_all())
        return res

    def search_new(self) -> Dict[str, Details]:
        res = {}
        for searcher in self.searchers:
            res.update(searcher.search_new())
        return res

    def forget(self, properties: List[str]) -> None:
        for searcher in self.searchers:
            searcher.forget(properties)
