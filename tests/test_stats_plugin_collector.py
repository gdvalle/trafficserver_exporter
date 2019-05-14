import sys
from os import path

import prometheus_client

from trafficserver_exporter.collector import StatsPluginCollector


def test_metric_parser(stats_json):
    metrics_file_path = path.join(path.dirname(sys.modules['trafficserver_exporter'].__file__), 'metrics.yaml')
    collector = StatsPluginCollector("", metrics_file_path)
    for metric in collector.parse_metrics(stats_json["global"]):
        assert isinstance(metric, prometheus_client.core.Metric)
