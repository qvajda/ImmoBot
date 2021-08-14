from pyhocon import ConfigFactory
from typing import Dict


class DetailFinder():
    def __init__(self, conf: ConfigFactory):
        self.conf = conf

    def findFor(self, props: Dict[str, str]):
        return props
