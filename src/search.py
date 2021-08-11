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
from typing import List


def launch_selenium() -> webdriver:
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options,
                               executable_path="/usr/bin/geckodriver")
    driver.implicitly_wait(5)
    return driver


class Searcher(ABC):
    def __init__(self):
        pass

    def __enter__(self):
        self.browser = launch_selenium()
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
    def __init__(self):
        super().__init__()
        # TODO read these params from a config file
        search_config = {"postalCodes": [1050,
                                         1040,
                                         1000,
                                         1030,
                                         1060,
                                         1210,
                                         1200,
                                         1160,
                                         1180,
                                         1170],
                         "minPrice": 350000,
                         "maxPrice": 540000,
                         "countries": 'BE',
                         "orderBy": 'newest'}
        search_config["postalCodes"] = ','.join([str(pc)
                                                 for pc in
                                                 search_config["postalCodes"]])
        base_url = 'https://www.immoweb.be/en/search/house/for-sale?'
        # hard code 'newest' search param
        # to avoid listing old properties by mistake
        if "orderBy" not in search_config:
            search_config["orderBy"] = "newest"
        url_params = '&'.join(["%s=%s" % item for
                               item in search_config.items()])
        self.url = base_url + url_params
        # TODO replace print with proper log
        print(f"Immoweb serach {self.url=}")
        self.maxpages = 1

    def __enter__(self):
        self.shelf = shelve.open("./shelves/immoweb")
        if "prevs" not in self.shelf:
            self.shelf["prevs"] = set()
        super().__enter__()
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.shelf.close()
        # no particular treatment in case of exceptions
        super().__exit__(exception_type, exception_value, traceback)

    def search_all(self):
        ids = []
        for page in range(1, self.maxpages + 1):
            self.browser.get(f"{self.url}&page={str(page)}")
            xpath = "//article[starts-with(@id, 'classified_')]"
            results = self.browser.find_elements_by_xpath(xpath)
            if len(results) == 0:
                print(f"No results found fitting {xpath=}")
            else:
                # take only the numerical part of IDs
                # immoweb search results IDs follow format 'classified_XXXXXXX'
                ids += [result.get_attribute('id').split("_")[1]
                        for result in results]
        return ids

    def search_new(self):
        all_ids = self.search_all()
        prevs = self.shelf["prevs"]
        new_ids = [i for i in all_ids if i not in prevs]
        if len(new_ids) > 0:
            print(f"Found {len(new_ids)} new properties on Immoweb: {new_ids}")
        else:
            print("No new properties found on Immoweb :(")
        prevs = set(list(prevs) + all_ids)
        self.shelf["prevs"] = prevs
        self.shelf.sync()
        return new_ids


if __name__ == '__main__':
    with ImmowebSearcher() as immoweb:
        immoweb.search_new()
