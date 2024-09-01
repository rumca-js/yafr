import argparse
import json

from .webtools import PageRequestObject
from .crawlers import CrawlerInterface


class ScriptCrawlerParser(object):
    """
    Headers can only be passed by input binary file
    """

    def parse(self):
        self.parser = argparse.ArgumentParser(description="Data analyzer program")
        self.parser.add_argument("--url", help="Directory to be scanned")
        self.parser.add_argument(
            "--timeout", default=10, type=int, help="Timeout expressed in seconds"
        )
        self.parser.add_argument("--ping", default=False, help="Ping only")
        self.parser.add_argument("--port", type=int, help="Port")
        self.parser.add_argument("--ssl-verify", default=False, help="SSL verify")

        # TODO implement
        self.parser.add_argument("--input-data", help="Input request file")
        self.parser.add_argument("-v", "--verbose", action="store_true", help="Verbose")

        self.parser.add_argument("-i", "--input", help="Requests binary file")
        self.parser.add_argument("-o", "--output-file", help="Response binary file")

        self.args = self.parser.parse_args()

    def is_valid(self):
        if "url" not in self.args:
            print("Url file not in args")
            return False

        if "output_file" not in self.args:
            print("Output file not in args")
            return False

        if self.args.url is None:
            print("Url file not in args")
            return False

        return True

    def get_request(self):
        r = PageRequestObject(self.args.url)
        r.timeout_s = self.args.timeout
        r.ping = self.args.ping

        return r


class ScriptCrawlerInterface(CrawlerInterface):
    """
    Interface that can be inherited by any browser, browser engine, crawler
    """

    def __init__(self, parser, request):
        super().__init__(request, parser.args.output_file, parser.args.port)