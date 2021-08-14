from pyhocon import ConfigFactory
from selenium import webdriver
from typing import Dict
from browser import launch_selenium


class DetailFinder():
    def __init__(self, conf: ConfigFactory):
        self.conf = conf

    def findFor(self, props: Dict[str, str]):
        return props


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
        return detail

    def findFor(self, props: Dict[str, str]):
        if len(props) == 0:
            return props
        browser = launch_selenium(self.conf)
        detailed = {prop: self.__findDetail__(url, browser) for
                    prop, url in props.items()}
        browser.quit()
        return detailed


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    immoweb_detail = ImmowebDetailFinder(conf["general"])
    test_id = "9355678"
    test_url = "https://www.immoweb.be/en/classified/house/for-sale/saint-josse-ten-noode/1030/9355678"
    detailed = immoweb_detail.findFor(props={test_id: test_url, })
    for prop, detail in detailed.items():
        print(f"{prop=} :")
        print(detail)
