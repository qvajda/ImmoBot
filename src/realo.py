from selenium import webdriver
from pyhocon import ConfigFactory
from typing import Optional
from typing import List
import copy
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait as wait

from logging_utils import initLogging
from details import DetailFinder
from details import Details
from details import CompleteDetails
from details import SeleniumDetailFinder
from search import Searcher
from search import MultiSearcher


class RealoDetailFinder(SeleniumDetailFinder):
    def __findDetail__(self, url: str, browser: webdriver) -> Details:
        browser.get(url)
        xpath = "//div[@class='property__container']"
        results = browser.find_elements_by_xpath(xpath)
        if len(results) == 0:
            self.logger.warn(
                f"Can't find Realo formatted details for {url=}")
            return Details(url)
        info = results[0]
        self.logger.debug(f"Found some details for {url=}")
        address_xpath = ".//h1[@class='address']"
        address = info.find_element_by_xpath(address_xpath)\
                      .get_attribute("innerHTML").strip()
        price_xpath = ".//span[@itemprop = 'price']"
        price_elem = info.find_element_by_xpath(price_xpath)
        price = int(price_elem.get_attribute("innerHTML").strip())
        features_xpath = ".//div[@class = 'component-property-features']"
        features = info.find_element_by_xpath(features_xpath).text.split("\n")

        def get_value_at_line_starting_with(lines: List[str],
                                            prefix: str) -> str:
            relevant_line = [line.strip() for line in lines
                             if line.startswith(prefix)][0]
            return relevant_line.split(" ")[-1]
        bedrooms = int(get_value_at_line_starting_with(features, "Bedrooms"))
        area = int(get_value_at_line_starting_with(features,
                                                   "Habitable area")[:-2])
        # TODO add agency name, PEB, garden size, bathrooms
        return CompleteDetails(url, price, address, bedrooms, area)


class SingleRealoSearcher(Searcher):
    """
    Realo website only allows to look for one location at a time.
    To go around this, the realo searcher is split between a searcher
    handling one location and one orchestrating multiple
    single location searchers.

    This is the single location realo searcher class.
    """
    name = "realo"

    def __init__(self, conf: ConfigFactory,
                 detailFinder: Optional[DetailFinder] = None):
        if detailFinder is None:
            detailFinder = RealoDetailFinder(conf)
        super().__init__(conf, detailFinder)
        if detailFinder is None:
            self.detailFinder = RealoDetailFinder(conf)
        else:
            self.detailFinder = detailFinder
        search_config = dict(self.conf["realo.search"])
        # turn postal codes config into a single string
        postalCode = self.conf["realo.postalCode"]
        self.name = f"realo{postalCode}"
        # dirty hack to keep conf sane
        self.conf.put(f"realo{postalCode}", self.conf["realo"])
        url_params = '&'.join(["%s=%s" % item for
                               item in search_config.items()])
        self.url = f"{self.conf['realo.search_url']}{postalCode}?{url_params}"
        # TODO replace print with proper log
        self.logger.debug(f"Realo search {self.url=}")

    def search_all(self):
        properties = {}

        def find_id(element):
            """
            Take only the ID.
            Realo search results IDs can be found directly in the container
            """
            return element.get_attribute('id')

        def find_link(element):
            """
            Link to property on Realo is directly in the container
            but it is a relative link so we need to add back the root.
            """
            return f"https://www.realo.be{element.get_attribute('data-href')}"
        self.browser.get(f"{self.url}")
        # Realo being quite slow, we wait until at least an element has loaded

        list_xpath = "//div[@class = 'module-listings']"
        list_of_properties = wait(self.browser, 5).until(
            EC.presence_of_element_located((By.XPATH, list_xpath)))
        # JavaScript Executor to stop page load
        # as otherwise realo keeps loading
        self.browser.execute_script("window.stop();")
        xpath = ".//div[@data-scope = 'componentEstateGridItem']"
        # TODO handle error if no list of properties
        results = list_of_properties.find_elements_by_xpath(xpath)
        if len(results) == 0:
            self.logger.warn(f"No results found fitting {xpath=}")
        else:
            properties.update({find_id(result): find_link(result)
                               for result in results})
        return properties


class RealoSearcher(MultiSearcher):
    """
    Realo website only allows to look for one location at a time.
    To go around this, the realo searcher is split between a searcher
    handling one location and one orchestrating multiple
    single location searchers.

    This is the orchestrator realo searcher class.
    """
    name = "Realo"

    def __init__(self, conf: ConfigFactory,
                 detailFinder: Optional[DetailFinder] = None):
        postalCodes = conf["realo.search.postalCodes"]
        searchers = []

        def copyConfForSingleLocation(conf: ConfigFactory,
                                      postalCode: int) -> ConfigFactory:
            cp_conf = copy.deepcopy(conf)
            cp_conf.pop("realo.search.postalCodes")
            cp_conf.put("realo.postalCode", postalCode)
            return cp_conf
        searchers = [SingleRealoSearcher(copyConfForSingleLocation(conf,
                                                                   postalCode),
                                         detailFinder)
                     for postalCode in postalCodes]

        super().__init__(conf, searchers)


def realoFactory(conf: ConfigFactory) -> Searcher:
    return RealoSearcher(conf)


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/myConf.conf")
    initLogging(conf)
    realo_detail = RealoDetailFinder(conf)
    test_id = "103682"
    test_url = "https://www.realo.be/en/rue-prince-royal-21-1050-ixelles-elsene/103682?l=244615180"
    detailed = realo_detail.findFor(props={test_id: test_url, })
    for prop, detail in detailed.items():
        print(f"{prop=} :")
        print(detail)
    # with RealoSearcher(conf) as realo:
    #     print(realo.search_new())
