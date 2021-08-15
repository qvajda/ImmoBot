from selenium import webdriver
from pyhocon import ConfigFactory
from typing import Optional

from details import DetailFinder
from details import Details
from details import SeleniumDetailFinder
from search import Searcher


class ImmovlanDetailFinder(SeleniumDetailFinder):
    def __findDetail__(self, url: str, browser: webdriver) -> Details:
        browser.get(url)
        xpath = "//div[@id = 'property-details']"
        results = browser.find_elements_by_xpath(xpath)
        if len(results) == 0:
            print(f"Can't find Immovlan formatted details for {url=}")
            return url
        info = results[0]
        print(f"Found some details for {url=}")
        street_xpath = ".//span[contains(@class, 'street-line')]"
        street = info.find_element_by_xpath(street_xpath)\
                     .get_attribute("innerHTML").strip()
        # TODO Exception handling if no address ?
        city_xpath = ".//span[contains(@class, 'city-line')]"
        city = info.find_element_by_xpath(city_xpath).text.strip()
        address = f"{city} | {street}"
        price_xpath = ".//span[contains(@class, 'price-label')]"
        price_elem = info.find_element_by_xpath(price_xpath)
        price = int(price_elem.text.strip().replace("\u202f", "")[:-1])
        text_xpath = ".//div[@class = 'ico-text']"
        bedroom_xpath = ".//div[contains(@class, 'NrOfBedrooms')]"
        bedroom_elem = info.find_element_by_xpath(bedroom_xpath)
        bedrooms = int(bedroom_elem.find_element_by_xpath(text_xpath)
                                   .get_attribute("innerHTML").strip())
        area_xpath = ".//div[contains(@class, 'LivableSurface')]"
        area_elem = info.find_element_by_xpath(area_xpath)
        area = int(area_elem.find_element_by_xpath(text_xpath)
                            .get_attribute("innerHTML")
                            .strip().split(" ")[0])
        # TODO add agency name, PEB, garden size, bathrooms
        return Details(price, address, url, bedrooms, area)


class ImmovlanSearcher(Searcher):
    name = "immovlan"

    def __init__(self, conf: ConfigFactory,
                 detailFinder: Optional[DetailFinder] = None):
        if detailFinder is None:
            detailFinder = ImmovlanDetailFinder(conf)
        super().__init__(conf, detailFinder)
        if detailFinder is None:
            self.detailFinder = ImmovlanDetailFinder(conf)
        else:
            self.detailFinder = detailFinder
        search_config = dict(self.conf["immovlan.search"])
        # turn postal codes config into a single string
        search_config["towns"] = ','.join([str(town)
                                           for town in
                                           search_config["towns"]])
        url_params = '&'.join(["%s=%s" % item for
                               item in search_config.items()])
        self.url = self.conf["immovlan.search_url"] + url_params
        # TODO replace print with proper log
        print(f"Immovlan search {self.url=}")
        self.maxpages = 1

    def search_all(self):
        properties = {}

        def find_id(element):
            """
            Take only the hash part of the ID
            Immovlan search results IDs can be found in the 'favorite' button
            """
            xpath = ".//button[@class='btn btn-favorite']"
            favorite_button = element.find_element_by_xpath(xpath)
            return favorite_button.get_attribute('data-value-id')

        def find_link(element):
            """
            Link to property on Immovlan is in any of the <a> tags
            """
            return element.find_element_by_tag_name("a").get_attribute("href")

        for page in range(1, self.maxpages + 1):
            self.browser.get(f"{self.url}&noindex={str(page)}")
            # Immovlan has its results lazily loaded so we need to wait
            xpath = "//article[@class='list-view-item mb-3 card card-border']"
            results = self.browser.find_elements_by_xpath(xpath)
            if len(results) == 0:
                print(f"No results found fitting {xpath=}")
            else:
                properties.update({find_id(result): find_link(result)
                                   for result in results})
        return properties


def immovlanFactory(conf: ConfigFactory) -> Searcher:
    return ImmovlanSearcher(conf, DetailFinder(conf))


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    immovlan_detail = ImmovlanDetailFinder(conf)
    test_id = "vam50427"
    test_url = "https://immo.vlan.be/en/detail/residence/for-sale/1040/etterbeek/vam50427"
    detailed = immovlan_detail.findFor(props={test_id: test_url, })
    for prop, detail in detailed.items():
        print(f"{prop=} :")
        print(detail)
    # with ImmovlanSearcher(conf) as immovlan:
    #     immovlan.search_new()
