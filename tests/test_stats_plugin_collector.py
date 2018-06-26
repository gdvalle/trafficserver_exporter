import prometheus_client

from trafficserver_exporter.collector import StatsPluginCollector


def test_metric_parser(stats_json):
    collector = StatsPluginCollector("")
    for metric in collector.parse_metrics(stats_json["global"]):
        assert isinstance(metric, prometheus_client.core.Metric)
