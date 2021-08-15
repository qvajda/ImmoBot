from pyhocon import ConfigFactory
from typing import Dict
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from dataclasses import field
from selenium import webdriver

from browser import launch_selenium


@dataclass
class Details:
    """Class representing details of an immo property."""
    price: int
    address: str
    url: str
    bedrooms: int
    area: int
    price_per_sqm: float = field(init=False)
    # TODO add agency name, PEB, garden size, bathrooms

    def __post_init__(self):
        self.price_per_sqm = self.price / self.area

    def __str__(self) -> str:
        return "\n".join([f"Address: {self.address}",
                          f"Price: {self.price}€",
                          f"Area: {self.area}m²",
                          f"Price per m²: {self.price_per_sqm:0.1f}€",
                          f"bedrooms: {self.bedrooms}",
                          self.url])


class DetailFinder():
    def __init__(self, conf: ConfigFactory):
        self.conf = conf

    def findFor(self, props: Dict[str, str]) -> Dict[str, str]:
        return props


class SeleniumDetailFinder(DetailFinder, metaclass=ABCMeta):
    @abstractmethod
    def __findDetail__(self, url: str, browser: webdriver) -> Details:
        pass

    def findFor(self, props: Dict[str, str]) -> Dict[str, Details]:
        if len(props) == 0:
            return props
        browser = launch_selenium(self.conf["general"])
        detailed = {prop: self.__findDetail__(url, browser) for
                    prop, url in props.items()}
        browser.quit()
        return detailed
