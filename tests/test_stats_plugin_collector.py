import unittest
import os
import json

from trafficserver_exporter.collector import StatsPluginCollector


SCRIPT_DIR, _ = os.path.split(__file__)
DATA_DIR = os.path.join(SCRIPT_DIR, 'data')

STATS_JSON = os.path.join(DATA_DIR, 'stats_over_http.json')


class StatsPluginCollectorTestCase(unittest.TestCase):
    def setUp(self):
        with open(STATS_JSON) as f:
            self.stats_json = json.loads(f.read())

    def test_metric_parser(self):
        collector = StatsPluginCollector('')
        collector.parse_metrics(self.stats_json['global'])
