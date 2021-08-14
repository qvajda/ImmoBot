from pyhocon import ConfigFactory
from typing import Dict
from abc import ABCMeta, abstractmethod
from selenium import webdriver

from browser import launch_selenium


class DetailFinder():
    def __init__(self, conf: ConfigFactory):
        self.conf = conf

    def findFor(self, props: Dict[str, str]) -> Dict[str, str]:
        return props


class SeleniumDetailFinder(DetailFinder, metaclass=ABCMeta):
    @abstractmethod
    def __findDetail__(self, url: str, browser: webdriver) -> str:
        pass

    def findFor(self, props: Dict[str, str]) -> Dict[str, str]:
        if len(props) == 0:
            return props
        browser = launch_selenium(self.conf["general"])
        detailed = {prop: self.__findDetail__(url, browser) for
                    prop, url in props.items()}
        browser.quit()
        return detailed
