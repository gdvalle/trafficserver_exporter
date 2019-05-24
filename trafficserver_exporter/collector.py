"""Prometheus collector for Apache Traffic Server's stats_over_http plugin."""

import logging
import re
import time

import requests
import yaml
from prometheus_client import Metric

CACHE_VOLUMES = re.compile("^proxy.process.cache.volume_([0-9]+)")

LOG = logging.getLogger(__name__)


def _get_float_value(data, keys):
    """Fetch a value using a list of keys.  First present key wins.
    Used for backwards compatibility with older ATS versions.
    """
    for key in keys:
        try:
            value = float(data[key])
        except KeyError:
            pass
        else:
            return value

    raise KeyError("Keys not found in data: {}".format(",".join(keys)))


class StatsPluginCollector(object):
    """Collector for metrics from the stats_over_http plugin."""

    def __init__(self, endpoint, metrics_config_file, max_retries=0, ssl_verify=True):
        """Instantiate a new Collector for ATS stats."""
        self._endpoint = endpoint
        self._ssl_verify = ssl_verify
        self.log = LOG
        self.session = requests.Session()
        http_adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        for prefix in ("http://", "https://"):
            self.session.mount(prefix, http_adapter)
        with open(metrics_config_file, "rb") as metrics_file:
            self._metrics = yaml.safe_load(metrics_file.read())

    def get_json(self):
        """Query the ATS stats endpoint, return parsed JSON."""
        r = self.session.get(self._endpoint, verify=self._ssl_verify)
        return r.json()["global"]

    def collect(self):
        """Generator used to gather and return all metrics."""
        start_time = time.time()
        self.log.debug("Beginning collection")

        self.log.debug("Fetching JSON: {0}".format(self._endpoint))
        data = self.get_json()

        self.log.debug("Gathering metrics")
        for metric in self.parse_metrics(data):
            yield metric

        self.log.debug("Collection complete")
        yield self._get_scrape_duration_metric(start_time)

    def _get_scrape_duration_metric(self, start_time):
        metric = Metric(
            "trafficserver_scrape_duration_seconds",
            "Time the Traffic Server scrape took, in seconds.",
            "gauge",
        )
        metric.add_sample(
            "trafficserver_scrape_duration_seconds",
            value=time.time() - start_time,
            labels={},
        )
        return metric

    def parse_metrics(self, data):
        """Generator for trafficserver metrics."""

        for metric_name, metric_cfg in self._metrics.items():
            metric = Metric(
                metric_name, metric_cfg["documentation"], metric_cfg["type"]
            )
            for metric_value in metric_cfg["values"]:
                if isinstance(metric_value["value"], float):
                    value = metric_value["value"]
                else:
                    try:
                        value = float(data[metric_value["value"]])
                    except ValueError:
                        self.log.warning(
                            "Unable to convert metric %s value %s to float",
                            metric_name,
                            metric_value["value"],
                        )
                    except KeyError:
                        self.log.debug(
                            "Metric %s value %s not found",
                            metric_name,
                            metric_value["value"],
                        )
                        continue

                metric.add_sample(
                    metric_name, value=value, labels=metric_value["labels"]
                )
            yield metric

        for rt in ("request", "response"):
            metric_name = "trafficserver_{}_size_bytes_total".format(rt)
            metric = Metric(
                metric_name, "{} size in bytes.".format(rt.capitalize()), "counter"
            )

            try:
                user_bytes = _get_float_value(
                    data,
                    [
                        "proxy.process.http.user_agent_total_{}_bytes".format(rt),
                        "proxy.node.http.user_agent_total_{}_bytes".format(rt),
                    ],
                )
            except KeyError:
                # TS v8 with missing total.
                header_total = float(
                    data[
                        "proxy.process.http.user_agent_{}_header_total_size".format(rt)
                    ]
                )
                doc_total = float(
                    data[
                        "proxy.process.http.user_agent_{}_document_total_size".format(
                            rt
                        )
                    ]
                )
                user_bytes = header_total + doc_total

            metric.add_sample(
                metric_name,
                value=user_bytes,
                labels={"source": "user_agent", "protocol": "http"},
            )

            try:
                origin_bytes = _get_float_value(
                    data,
                    [
                        "proxy.process.http.origin_server_total_{}_bytes".format(rt),
                        "proxy.node.http.origin_server_total_{}_bytes".format(rt),
                    ],
                )
            except KeyError:
                # TS v8 with missing total.
                header_total = float(
                    data[
                        "proxy.process.http.origin_server_{}_header_total_size".format(
                            rt
                        )
                    ]
                )
                doc_total = float(
                    data[
                        "proxy.process.http.origin_server_{}_document_total_size".format(
                            rt
                        )
                    ]
                )
                origin_bytes = header_total + doc_total

            metric.add_sample(
                metric_name,
                value=origin_bytes,
                labels={"source": "origin_server", "protocol": "http"},
            )

            metric.add_sample(
                metric_name,
                value=_get_float_value(
                    data,
                    [
                        "proxy.process.http.parent_proxy_{}_total_bytes".format(rt),
                        "proxy.node.http.parent_proxy_total_{}_bytes".format(rt),
                    ],
                ),
                labels={"source": "parent_proxy", "protocol": "http"},
            )
            yield metric

        #
        # Cache
        #
        # Gather all cache volumes for cache statistics
        volumes = set()
        for key in data:
            if key.startswith("proxy.process.cache.volume_"):
                m = CACHE_VOLUMES.match(key)
                volumes.add(int(m.group(1)))

        # Create all cache volume metrics
        for volume in volumes:
            for metric in self._parse_volume_metrics(data, volume):
                yield metric

    def _parse_volume_metrics(self, data, volume):
        metric = Metric(
            "trafficserver_ram_cache_hits_total", "RAM cache hit count.", "counter"
        )
        metric.add_sample(
            "trafficserver_ram_cache_hits_total",
            value=float(data["proxy.process.cache.ram_cache.hits"]),
            labels={"volume": str(volume)},
        )
        yield metric

        metric = Metric(
            "trafficserver_cache_avail_size_bytes_total",
            "Total cache available.",
            "gauge",
        )
        metric.add_sample(
            "trafficserver_cache_avail_size_bytes_total",
            value=float(
                data["proxy.process.cache.volume_{0}.bytes_total".format(volume)]
            ),
            labels={"volume": str(volume)},
        )
        yield metric

        metric = Metric(
            "trafficserver_cache_used_bytes_total",
            "Total cache used in bytes.",
            "gauge",
        )
        metric.add_sample(
            "trafficserver_cache_used_bytes_total",
            value=float(
                data["proxy.process.cache.volume_{0}.bytes_used".format(volume)]
            ),
            labels={"volume": str(volume)},
        )
        yield metric

        metric = Metric(
            "trafficserver_cache_direntries", "Total cache direntries.", "gauge"
        )
        metric.add_sample(
            "trafficserver_cache_direntries",
            value=float(
                data["proxy.process.cache.volume_{0}.direntries.total".format(volume)]
            ),
            labels={"volume": str(volume)},
        )
        yield metric

        metric = Metric(
            "trafficserver_cache_used_direntries", "Cache direntries used.", "gauge"
        )
        metric.add_sample(
            "trafficserver_cache_used_direntries",
            value=float(
                data["proxy.process.cache.volume_{0}.direntries.used".format(volume)]
            ),
            labels={"volume": str(volume)},
        )
        yield metric

        metric = Metric(
            "trafficserver_cache_operations_total", "Cache operation count.", "counter"
        )
        for op in (
            "lookup",
            "read",
            "write",
            "update",
            "remove",
            "evacuate",
            "scan",
            "read_busy",
        ):
            for result in ("success", "failure"):
                k = "proxy.process.cache.volume_{volume}.{op}.{result}".format(
                    volume=volume, op=op, result=result
                )
                metric.add_sample(
                    "trafficserver_cache_operations_total",
                    value=float(data[k]),
                    labels={"volume": str(volume), "operation": op, "result": result},
                )
        yield metric
