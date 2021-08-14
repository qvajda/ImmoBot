from selenium import webdriver
from pyhocon import ConfigFactory
from typing import Dict
from typing import Optional

from browser import launch_selenium
from details import DetailFinder
from search import Searcher


class ImmowebDetailFinder(DetailFinder):
    def __findDetail__(self, url: str, browser: webdriver):
        browser.get(url)
        xpath = "//div[@class ='classified__header-content']"
        results = browser.find_elements_by_xpath(xpath)
        if len(results) == 0:
            print(f"Can't find Immoweb formatted details for {url=}")
            return url
        print(f"Found some details for {url=}")
        infos = [line.strip() for line in results[0].text.split("\n")]
        address = infos[-2].replace("Ask for the exact address",
                                    "No exact address")
        detail = f"{address = }\n"
        price = [int(line[:-1])
                 for line in infos if
                 line.endswith('€')][0]
        detail += f"{price = }€\n"
        bedrooms_area = [line.split('|')
                         for line in infos if
                         line.endswith('m²')][0]
        bedrooms = int(bedrooms_area[0].strip().split(' ')[0])
        detail += f"{bedrooms = }\n"
        area = int(bedrooms_area[1].strip().split(' ')[0])
        detail += f"{area = } sqm\n"
        price_per_sqm = price / area
        detail += f"{price_per_sqm = :.0f}€ \n"
        # TODO add agency name ?
        detail += url
        return detail

    def findFor(self, props: Dict[str, str]):
        if len(props) == 0:
            return props
        browser = launch_selenium(self.conf["general"])
        detailed = {prop: self.__findDetail__(url, browser) for
                    prop, url in props.items()}
        browser.quit()
        return detailed


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
        print(f"Immoweb search {self.url=}")
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
                print(f"No results found fitting {xpath=}")
            else:
                properties.update({find_id(result): find_link(result)
                                   for result in results})
        return properties


def immowebFactory(conf: ConfigFactory) -> Searcher:
    return ImmowebSearcher(conf)


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    # immoweb_detail = ImmowebDetailFinder(conf)
    # test_id = "9355678"
    # test_url = "https://www.immoweb.be/en/classified/house/for-sale/saint-josse-ten-noode/1030/9355678"
    # detailed = immoweb_detail.findFor(props={test_id: test_url, })
    # for prop, detail in detailed.items():
    #     print(f"{prop=} :")
    #     print(detail)
    with immowebFactory(conf) as immoweb:
        immoweb.search_new()