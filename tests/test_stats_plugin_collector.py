import os

import prometheus_client
from mock import Mock, patch

from trafficserver_exporter.collector import StatsPluginCollector
from trafficserver_exporter.trafficserver_exporter import PKG_METRICS_FILE


def test_metric_output(stats_json):
    # With some existing stats data
    fname, stats = stats_json
    registry = prometheus_client.registry.CollectorRegistry()
    # And the collector setup with the default metrics config
    collector = StatsPluginCollector("http://ats", PKG_METRICS_FILE)
    registry.register(collector)
    # With a mocked response that returns the stats data
    with patch.object(collector, "session") as mock_session:
        mock_response = Mock()
        mock_response.json.return_value = stats
        # If I generate metric output with that collector
        output = prometheus_client.generate_latest(registry).decode("utf-8")

    # I expect a proper HTTP request with the session
    mock_session.get.assert_called_once_with("http://ats", verify=True)

    if os.getenv("WRITE_METRIC_DATA"):
        with open("./tests/output/{}.prom".format(fname), "w") as f:
            f.write(output)

    # If I compare the output to a known valid set
    with open("./tests/output/{}.prom".format(fname), "r") as f:
        valid_lines = {l.strip() for l in f.readlines()}

    for line in output.split("\n"):
        if line and not any(
            (
                # With some variable metrics removed
                line.startswith("trafficserver_scrape_duration_seconds "),
                # And comments
                line.startswith("#"),
            )
        ):
            # I expect each metric line to match
            assert line in valid_lines
