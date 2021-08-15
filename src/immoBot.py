import telegram_send as ts
from pyhocon import ConfigFactory
from typing import Callable
import schedule
import time
from search import Searcher
from search import MultiSearcher
from immoweb import immowebFactory
from immovlan import immovlanFactory
from realo import realoFactory


def allSearchersFactory(conf: ConfigFactory) -> Searcher:
    return MultiSearcher(conf, [immowebFactory(conf),
                                immovlanFactory(conf),
                                realoFactory(conf)])


class ImmoBot():
    def __init__(self,
                 conf: ConfigFactory,
                 searchFactory: Callable[[ConfigFactory], Searcher]):
        self.searchFactory = searchFactory
        self.conf = conf

    def job(self, searcher: Searcher) -> None:
        search_results = searcher.search_new()
        if len(search_results) > 0:
            print("Found new property(ies) and sending them to telegram...")
            messages = [f"New property found {k}\n{v!s}"
                        for k, v in search_results.items()]
            ts.send(messages=messages)
            print("... property(ies) sent")

    def start(self) -> None:
        print("Starting ImmoBot")
        with self.searchFactory(self.conf) as searcher:
            try:
                schedule.every(self.conf["general.bot.frequency"])\
                        .minutes.do(self.job, searcher)
                schedule.run_all()
                while True:
                    schedule.run_pending()
                    time.sleep(self.conf["general.bot.sleep"])
            except KeyboardInterrupt:
                print("ImmoBot closing down")


if __name__ == '__main__':
    conf = ConfigFactory.parse_file("configuration/template.conf")
    bot = ImmoBot(conf, immowebFactory)
    bot.start()
