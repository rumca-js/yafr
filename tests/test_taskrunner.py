
import unittest
from src.taskrunner import TaskRunner

class Source():
    def __init__(self):
        self.url = ""
        self.xpath = ""

class TaskRunnerTest(unittest.TestCase):

    def test_is_entry_ok(self):
        runner = TaskRunner("Table")

        """
        entry = {}
        entry["link"] = "https://youtube.com"

        source = Source()

        # call tested function
        self.assertTrue(runner.is_entry_ok(entry, source))

        source.xpath = ".*youtube.com.*"

        # call tested function
        self.assertTrue(runner.is_entry_ok(entry, source))

        source.xpath = ".*github.com.*"

        # call tested function
        self.assertFalse(runner.is_entry_ok(entry, source))
        """
