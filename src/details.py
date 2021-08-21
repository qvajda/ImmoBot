from pyhocon import ConfigFactory
from typing import Dict
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from dataclasses import field
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException

from logging import getLogger

from browser import launch_selenium


@dataclass
class Details:
    url: str

    def __str__(self):
        return self.url


@dataclass
class CompleteDetails(Details):
    """Class representing details of an immo property."""
    price: int
    address: str
    bedrooms: int
    area: int
    price_per_sqm: float = field(init=False)
    # TODO add agency name, PEB, garden size, bathrooms

    def __post_init__(self):
        """ Post init method to compute fields derived
        from the values of others. """
        # TODO better deal with None values
        if self.price is None or self.area is None:
            self.price_per_sqm = -1.0
        else:
            self.price_per_sqm = self.price / self.area

    def __str__(self) -> str:
        return "\n".join([f"Address: {self.address}",
                          f"Price: {self.price}€",
                          f"Area: {self.area}m²",
                          f"Price per m²: {self.price_per_sqm:0.1f}€",
                          f"Bedrooms: {self.bedrooms}",
                          self.url])


class DetailFinder():
    def __init__(self, conf: ConfigFactory):
        self.conf = conf
        self.logger = getLogger()

    def findFor(self, props: Dict[str, str]) -> Dict[str, Details]:
        return {k: Details(v) for k, v in props.items()}


class SeleniumDetailFinder(DetailFinder, metaclass=ABCMeta):
    @abstractmethod
    def __findDetail__(self, url: str, browser: webdriver) -> Details:
        pass

    def findFor(self, props: Dict[str, str]) -> Dict[str, Details]:
        if len(props) == 0:
            return props
        browser = launch_selenium(self.conf["general"])
        detailed = {}
        for prop, url in props.items():
            try:
                detailed[prop] = self.__findDetail__(url, browser)
            except (NoSuchElementException, IndexError, ValueError):
                # These error types correspond to:
                # NoSuchElementException:
                #    Selenium not finding the expected element on the page
                # IndexError:
                #    The size of a text after splitting is too small
                #    e.g. not all element expected in the same text zone are
                #    present
                # ValueError:
                #    Text zone that was expected to only contain a number ha
                #    a different format than is handled
                #    e.g. instead of just the price, we have a
                #    'Starting price xxxx$' format
                self.logger.error("Unexcpected error encountered "
                                  f"while looking for details of {prop} "
                                  f"in page {url}")
                self.logger.exception("Exception: ")
                # Safely recover by using a less complete Details
                detailed[prop] = Details[url]
        browser.quit()
        return detailed
