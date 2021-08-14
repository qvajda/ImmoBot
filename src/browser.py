from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from pyhocon import ConfigFactory


def launch_selenium(conf: ConfigFactory) -> webdriver:
    options = Options()
    options.headless = True
    driver = webdriver.Firefox(options=options,
                               executable_path=conf["gecko_path"])
    driver.implicitly_wait(5)
    return driver
