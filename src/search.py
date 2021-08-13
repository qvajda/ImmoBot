#!/usr/bin/python3
# Usage:
# - Fill in the settings, then run with `python3 ImmowebScraper.py`.
# - First run won't send any mails (or you'd get dozens at once).
# Requirements:
# - python3
# - selenium
# - phantomjs

from selenium import webdriver
from selenium.webdriver.firefox.options import Options
import shelve
from abc import ABC, abstractmethod
from pyhocon import ConfigFactory
from typing import List


def launch_selenium(conf: ConfigFactory) -> webdriver:
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options,
                               executable_path=conf["gecko_path"])
    driver.implicitly_wait(5)
    return driver


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


class ImmowebSearcher(Searcher):
    def __init__(self, conf: ConfigFactory):
        super().__init__(conf)
        search_config = dict(self.conf["immoweb.search"])
        # turn postal codes config into a single string
        search_config["postalCodes"] = ','.join([str(pc)
                                                 for pc in
                                                 search_config["postalCodes"]])
        # hard code 'newest' search param
        # to avoid listing old properties by mistake
        if "orderBy" not in search_config:
            search_config["orderBy"] = "newest"
        url_params = '&'.join(["%s=%s" % item for
                               item in search_config.items()])
        self.url = self.conf["immoweb.search_url"] + url_params
        # TODO replace print with proper log
        print(f"Immoweb search {self.url=}")
        self.maxpages = 1

    def __enter__(self):
        shelve_dir = self.conf["general.shelve_dir"]
        self.shelf = shelve.open(f"{shelve_dir}immoweb")
        if "prevs" not in self.shelf:
            self.shelf["prevs"] = {}
        super().__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.shelf.close()
        # no particular treatment in case of exceptions
        super().__exit__(exception_type, exception_value, traceback)

    def search_all(self):
        properties = {}

        def find_id(element):
            """
            Take only the numerical part of IDs
            Immoweb search results IDs follow format 'classified_XXXXXXX'
            """
            return element.get_attribute('id').split("_")[1]

        def find_link(element):
            """
            Link to property on Immoweb is in the only <a> block
            """
            return element.find_element_by_tag_name("a").get_attribute("href")

        for page in range(1, self.maxpages + 1):
            self.browser.get(f"{self.url}&page={str(page)}")
            xpath = "//article[starts-with(@id, 'classified_')]"
            results = self.browser.find_elements_by_xpath(xpath)
            if len(results) == 0:
                print(f"No results found fitting {xpath=}")
            else:
                properties.update({find_id(result): find_link(result)
                                   for result in results})
        return properties

    def search_new(self):
        all_properties = self.search_all()
        prevs = self.shelf["prevs"]
        new_properties = {k: v for
                          k, v in all_properties.items() if
                          k not in prevs}
        if len(new_properties) > 0:
            print(f"Found {len(new_properties)} new properties on Immoweb:"
                  f"{list(new_properties.keys())}")
            prevs.update(new_properties)
            self.shelf["prevs"] = prevs  # TODO check if this line is needed
            self.shelf.sync()
        else:
            print("No new properties found on Immoweb")
        return new_properties


def searchFactory(conf: ConfigFactory) -> Searcher:
    return ImmowebSearcher(conf)


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    with ImmowebSearcher(conf) as immoweb:
        immoweb.search_new()
