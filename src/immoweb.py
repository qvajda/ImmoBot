from selenium import webdriver
from pyhocon import ConfigFactory
from typing import Optional

from logging_utils import initLogging
from details import DetailFinder
from details import Details
from details import CompleteDetails
from details import SeleniumDetailFinder
from search import Searcher


class ImmowebDetailFinder(SeleniumDetailFinder):
    def __findDetail__(self, url: str, browser: webdriver) -> Details:
        browser.get(url)
        xpath = "//div[@class ='classified__header-content']"
        results = browser.find_elements_by_xpath(xpath)
        if len(results) == 0:
            self.logger.warn(
                f"Can't find Immoweb formatted details for {url=}")
            return Details(url)
        self.logger.debug(f"Found some details for {url=}")
        infos = [line.strip() for line in results[0].text.split("\n")]
        address = infos[-2].replace("Ask for the exact address",
                                    "No exact address")
        price = [int(line[:-1].split(" ")[-1])
                 for line in infos if
                 line.endswith('€')][0]
        bedrooms_area_lines = [line.split('|')
                               for line in infos if
                               line.endswith('m²')]
        bedrooms = None
        area = None
        if len(bedrooms_area_lines) == 0:
            bedrooms = int([line.strip().split(" ")[0] for line in infos if
                            line.endswith("bedrooms")][0])
        else:
            bedrooms_area = bedrooms_area_lines[0]
            area = int(bedrooms_area.pop().strip().split(' ')[0])
            if len(bedrooms_area) > 0:
                bedrooms = int(bedrooms_area.pop().strip().split(' ')[0])
        # TODO add agency name, PEB, garden size, bathrooms
        return CompleteDetails(url, price, address, bedrooms, area)


class ImmowebSearcher(Searcher):
    name = "immoweb"

    def __init__(self, conf: ConfigFactory,
                 detailFinder: Optional[DetailFinder] = None):
        if detailFinder is None:
            detailFinder = ImmowebDetailFinder(conf)
        super().__init__(conf, detailFinder)
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
        self.logger.debug(f"Immoweb search {self.url=}")
        self.maxpages = 1

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
                self.logger.warn(f"No results found fitting {xpath=}")
            else:
                properties.update({find_id(result): find_link(result)
                                   for result in results})
        return properties


def immowebFactory(conf: ConfigFactory) -> Searcher:
    return ImmowebSearcher(conf)


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    initLogging(conf)
    # immoweb_detail = ImmowebDetailFinder(conf)
    # test_id = "9479036"
    # test_url = "https://www.immoweb.be/en/classified/apartment-block/for-sale/brussels-city/1000/9479036?searchId=61200b6c5e145"
    # detailed = immoweb_detail.findFor(props={test_id: test_url, })
    # for prop, detail in detailed.items():
    #     print(f"{prop=} :")
    #     print(detail)
    with immowebFactory(conf) as immoweb:
        immoweb.search_new()
