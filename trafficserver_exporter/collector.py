
"""Prometheus collector for Apache Traffic Server's stats_over_http plugin."""

import logging
import json
import re
import time

import requests
from prometheus_client import Metric


HTTP_VERBS = ('GET', 'HEAD', 'POST', 'PUT', 'PUSH', 'DELETE', 'PURGE')
HTTP_VERBS_LOWER = tuple([v.lower() for v in HTTP_VERBS])

TS_RESPONSE_CODES = ('100', '101', '1xx', '200', '201', '202', '203', '204',
                     '205', '206', '2xx', '300', '301', '302', '303', '304',
                     '305', '307', '3xx', '400', '401', '402', '403', '404',
                     '405', '406', '407', '408', '409', '410', '411', '412',
                     '413', '414', '415', '416', '4xx', '500', '501', '502',
                     '503', '504', '505', '5xx')

CACHE_VOLUMES = re.compile('^proxy.process.cache.volume_([0-9]+)')

LOG = logging.getLogger(__name__)


class StatsPluginCollector(object):
    """Collector for metrics from the stats_over_http plugin."""

    def __init__(self, endpoint, max_retries=0):
        """Instantiate a new Collector for ATS stats."""
        self._endpoint = endpoint
        self.log = LOG
        self.session = requests.Session()
        http_adapter = requests.adapters.HTTPAdapter(max_retries=max_retries)
        for prefix in ('http://', 'https://'):
            self.session.mount(prefix, http_adapter)

    def get_json(self):
        """Query the ATS stats endpoint, return parsed JSON."""
        return json.loads(
            requests.get(self._endpoint).content.decode('UTF-8'))['global']

    def collect(self):
        """Generator used to gather and return all metrics."""
        start_time = time.time()
        self.log.debug('Beginning collection')

        self.log.debug('Fetching JSON: {0}'.format(self._endpoint))
        data = self.get_json()

        self.log.debug('Gathering metrics')
        for metric in self.parse_metrics(data):
            yield metric

        self.log.debug('Collection complete')
        yield self._get_scrape_duration_metric(start_time)

    def _get_scrape_duration_metric(self, start_time):
        metric = Metric(
            'trafficserver_scrape_duration_seconds',
            'Time the Traffic Server scrape took, in seconds.',
            'gauge')
        metric.add_sample(
            'trafficserver_scrape_duration_seconds',
            value=time.time() - start_time,
            labels={})
        return metric

    def parse_metrics(self, data):
        """Generator for trafficserver metrics."""
        # Counter for server restarts
        metric = Metric(
            'trafficserver_restart_count',
            'Count of traffic_server restarts.',
            'counter')
        metric.add_sample(
            'trafficserver_restart_count',
            value=float(data['proxy.node.restarts.proxy.restart_count']),
            labels={})
        yield metric

        #
        # HTTP
        #
        # Connections
        metric = Metric(
            'trafficserver_connections_total',
            'Connection count.',
            'counter')
        metric.add_sample(
            'trafficserver_connections_total',
            value=float(data['proxy.process.http.total_client_connections']),
            labels={'source': 'client',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_connections_total',
            value=float(data['proxy.process.http.total_server_connections']),
            labels={'source': 'server',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_connections_total',
            value=float(
                data['proxy.process.http.total_parent_proxy_connections']),
            labels={'source': 'parent_proxy',
                    'protocol': 'http'})
        yield metric

        # Incoming requests
        metric = Metric(
            'trafficserver_requests_incoming',
            'Incoming requests.',
            'gauge')
        metric.add_sample(
            'trafficserver_requests_incoming',
            value=float(data['proxy.process.http.incoming_requests']),
            labels={'protocol': 'http'})
        yield metric

        # Client aborts
        metric = Metric(
            'trafficserver_error_client_aborts_total',
            'Client aborts.',
            'counter')
        metric.add_sample(
            'trafficserver_client_aborts_total',
            value=float(
                data['proxy.process.http.err_client_abort_count_stat']),
            labels={'protocol': 'http'})
        yield metric

        # Connect fails
        metric = Metric(
            'trafficserver_connect_failures_total',
            'Connect failures.',
            'counter')
        metric.add_sample(
            'trafficserver_connect_failures_total',
            value=float(
                data['proxy.process.http.err_connect_fail_count_stat']),
            labels={'protocol': 'http'})
        yield metric

        # Transaction count
        metric = Metric(
            'trafficserver_transactions_total',
            'Total transactions.',
            'counter')
        metric.add_sample(
            'trafficserver_transactions_total',
            value=data[('proxy.node.http.'
                        'user_agents_total_transactions_count')],
            labels={'source': 'user_agent',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transactions_total',
            value=float(data[
                'proxy.node.http.origin_server_total_transactions_count']),
            labels={'source': 'origin_server',
                    'protocol': 'http'})
        yield metric

        # Transaction time spent, total
        metric = Metric(
            'trafficserver_transactions_time_ms_total',
            'Total transaction time (ms).',
            'counter')
        metric.add_sample(
            'trafficserver_transactions_time_total',
            value=float(data['proxy.process.http.total_transactions_time']),
            labels={})
        yield metric

        # Transaction time spent, hits
        metric = Metric(
            'trafficserver_hit_transaction_time_ms_total',
            'Total cache hit transaction time (ms).',
            'counter')
        metric.add_sample(
            'trafficserver_hit_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.hit_fresh']),
            labels={'state': 'fresh',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_hit_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.hit_revalidated']),
            labels={'state': 'revalidated',
                    'protocol': 'http'})
        yield metric

        # Transaction time spent, misses
        metric = Metric(
            'trafficserver_miss_transaction_time_ms_total',
            'Total cache miss transaction time (ms).',
            'counter')
        metric.add_sample(
            'trafficserver_miss_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.miss_cold']),
            labels={'state': 'cold',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.miss_not_cacheable'
            ]),
            labels={'state': 'not_cacheable',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.miss_changed']),
            labels={'state': 'changed',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.miss_client_no_cache'
            ]),
            labels={'state': 'no_cache',
                    'protocol': 'http'})
        yield metric

        # Transaction time spent, errors
        metric = Metric(
            'trafficserver_error_transaction_time_ms_total',
            'Total cache error transaction time (ms).',
            'counter')
        metric.add_sample(
            'trafficserver_error_transaction_time_ms_total',
            value=float(data[
                'proxy.process.http.transaction_totaltime.errors.aborts']),
            labels={'state': 'abort',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_error_transaction_time_ms_total',
            value=float(data[('proxy.process.http.transaction_totaltime.'
                              'errors.possible_aborts')]),
            labels={'state': 'possible_abort',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_error_transaction_time_ms_total',
            value=float(data[('proxy.process.http.transaction_totaltime.'
                              'errors.connect_failed')]),
            labels={'state': 'connect_failed',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_error_transaction_time_ms_total',
            value=float(data[('proxy.process.http.transaction_totaltime.'
                              'errors.other')]),
            labels={'state': 'other',
                    'protocol': 'http'})
        yield metric

        # Transaction time spent, other
        metric = Metric(
            'trafficserver_other_transaction_time_ms_total',
            'Total other/unclassified transaction time (ms).',
            'counter')
        metric.add_sample(
            'trafficserver_other_transaction_time_ms_total',
            value=float(data[('proxy.process.http.transaction_totaltime.'
                              'errors.unclassified')]),
            labels={'state': 'unclassified',
                    'protocol': 'http'})
        yield metric

        # Transaction count, hits
        metric = Metric(
            'trafficserver_transaction_hits_total',
            'Transaction hit counts.',
            'counter')
        metric.add_sample(
            'trafficserver_transaction_hits_total',
            value=float(data[
                'proxy.process.http.transaction_counts.hit_fresh']),
            labels={'state': 'fresh',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_hits_total',
            value=float(data[
                'proxy.process.http.transaction_counts.hit_revalidated']),
            labels={'state': 'revalidated',
                    'protocol': 'http'})
        # Zero labels (misses)
        metric.add_sample(
            'trafficserver_transaction_hits_total',
            value=0.0,
            labels={'state': 'cold',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_hits_total',
            value=0.0,
            labels={'state': 'not_cacheable',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_hits_total',
            value=0.0,
            labels={'state': 'changed',
                    'protocol': 'http'})
        yield metric

        # Transaction count, misses
        metric = Metric(
            'trafficserver_transaction_misses_total',
            'Transaction miss counts.',
            'counter')
        metric.add_sample(
            'trafficserver_transaction_misses_total',
            value=float(data[
                'proxy.process.http.transaction_counts.miss_cold']),
            labels={'state': 'cold',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_misses_total',
            value=float(data[
                'proxy.process.http.transaction_counts.miss_not_cacheable']),
            labels={'state': 'not_cacheable',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_misses_total',
            value=float(data[
                'proxy.process.http.transaction_counts.miss_changed']),
            labels={'state': 'changed',
                    'protocol': 'http'})
        # Zero labels (hits)
        metric.add_sample(
            'trafficserver_transaction_misses_total',
            value=0.0,
            labels={'state': 'fresh',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_misses_total',
            value=0.0,
            labels={'state': 'revalidated',
                    'protocol': 'http'})
        yield metric

        # Transaction count, errors
        metric = Metric(
            'trafficserver_transaction_errors_total',
            'Transaction error counts.',
            'counter')
        metric.add_sample(
            'trafficserver_transaction_errors_total',
            value=float(data[('proxy.process.http.transaction_counts.errors.'
                             'aborts')]),
            labels={'state': 'abort',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_errors_total',
            value=float(data[('proxy.process.http.transaction_counts.errors.'
                              'possible_aborts')]),
            labels={'state': 'possible_abort',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_errors_total',
            value=float(data[('proxy.process.http.transaction_counts.errors.'
                              'connect_failed')]),
            labels={'state': 'connect_failed',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_transaction_errors_total',
            value=float(data[('proxy.process.http.transaction_counts.errors.'
                             'other')]),
            labels={'state': 'other',
                    'protocol': 'http'})
        yield metric

        # Transaction count, others
        metric = Metric(
            'trafficserver_transaction_others_total',
            'Transaction other/unclassified counts.',
            'counter')
        metric.add_sample(
            'trafficserver_transaction_others_total',
            value=float(data[('proxy.process.http.transaction_counts.other.'
                              'unclassified')]),
            labels={'state': 'unclassified',
                    'protocol': 'http'})
        yield metric

        # HTTP Responses
        metric = Metric(
            'trafficserver_responses_total',
            'Response count.',
            'counter')
        for code in TS_RESPONSE_CODES:
            key = 'proxy.process.http.{code}_responses'.format(code=code)
            metric.add_sample(
                'trafficserver_responses_total',
                value=float(data[key]),
                labels={'code': code,
                        'protocol': 'http'})
        yield metric

        # HTTP Requests
        metric = Metric(
            'trafficserver_requests_total',
            'Request count.',
            'counter')
        for method in HTTP_VERBS_LOWER:
            key = 'proxy.process.http.{method}_requests'.format(method=method)
            metric.add_sample(
                'trafficserver_requests_total',
                value=float(data[key]),
                labels={'method': method,
                        'protocol': 'http'})
        yield metric

        # Invalid requests
        metric = Metric(
            'trafficserver_client_requests_invalid_total',
            'Invalid client requests.',
            'counter')
        metric.add_sample(
            'trafficserver_client_requests_invalid_total',
            value=float(data['proxy.process.http.invalid_client_requests']),
            labels={'protocol': 'http'})
        yield metric

        # Requests without Host header
        metric = Metric(
            'trafficserver_client_requests_missing_host_hdr_total',
            'Client requests missing host header.',
            'counter')
        metric.add_sample(
            'trafficserver_client_requests_missing_host_hdr_total',
            value=float(data['proxy.process.http.missing_host_hdr']),
            labels={'protocol': 'http'})
        yield metric

        # Request size
        metric = Metric(
            'trafficserver_request_size_bytes_total',
            'Request size in bytes.',
            'counter')
        metric.add_sample(
            'trafficserver_request_size_bytes_total',
            value=float(data[
                'proxy.node.http.user_agent_total_request_bytes']),
            labels={'source': 'user_agent',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_request_size_bytes_total',
            value=float(data[
                'proxy.node.http.origin_server_total_request_bytes']),
            labels={'source': 'origin_server',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_request_size_bytes_total',
            value=float(data[
                'proxy.node.http.parent_proxy_total_request_bytes']),
            labels={'source': 'parent_proxy',
                    'protocol': 'http'})
        yield metric

        # Response size
        metric = Metric(
            'trafficserver_response_size_bytes_total',
            'Response size in bytes.',
            'counter')
        metric.add_sample(
            'trafficserver_response_size_bytes_total',
            value=float(data[
                'proxy.node.http.user_agent_total_response_bytes']),
            labels={'source': 'user_agent',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_response_size_bytes_total',
            value=float(data[
                'proxy.node.http.origin_server_total_response_bytes']),
            labels={'source': 'origin_server',
                    'protocol': 'http'})
        metric.add_sample(
            'trafficserver_response_size_bytes_total',
            value=float(data[
                'proxy.node.http.parent_proxy_total_response_bytes']),
            labels={'source': 'parent_proxy',
                    'protocol': 'http'})
        yield metric

        #
        # Cache
        #
        # Gather all cache volumes for cache statistics
        volumes = set()
        for key in data:
            if key.startswith('proxy.process.cache.volume_'):
                m = CACHE_VOLUMES.match(key)
                volumes.add(int(m.group(1)))

        # Create all cache volume metrics
        for volume in volumes:
            for metric in self._parse_volume_metrics(data, volume):
                yield metric

        metric = Metric(
            'trafficserver_ram_cache_misses_total',
            'RAM cache miss count.',
            'counter')
        metric.add_sample(
            'trafficserver_ram_cache_misses_total',
            value=float(data['proxy.process.cache.ram_cache.misses']),
            labels={})
        yield metric

        metric = Metric(
            'trafficserver_ram_cache_avail_size_bytes_total',
            'RAM cache available in bytes.',
            'gauge')
        metric.add_sample(
            'trafficserver_ram_cache_avail_size_bytes_total',
            value=float(data['proxy.process.cache.ram_cache.total_bytes']),
            labels={})
        yield metric

        metric = Metric(
            'trafficserver_ram_cache_used_bytes_total',
            'RAM cache used in bytes.',
            'gauge')
        metric.add_sample(
            'trafficserver_ram_cache_used_bytes_total',
            value=float(data['proxy.process.cache.ram_cache.bytes_used']),
            labels={})
        yield metric

    def _parse_volume_metrics(self, data, volume):
        metric = Metric(
            'trafficserver_ram_cache_hits_total',
            'RAM cache hit count.',
            'counter')
        metric.add_sample(
            'trafficserver_ram_cache_hits_total',
            value=float(data['proxy.process.cache.ram_cache.hits']),
            labels={'volume': str(volume)})
        yield metric

        metric = Metric(
            'trafficserver_cache_avail_size_bytes_total',
            'Total cache available.',
            'gauge')
        metric.add_sample(
            'trafficserver_cache_avail_size_bytes_total',
            value=float(data[
                'proxy.process.cache.volume_{0}.bytes_used'.format(volume)]),
            labels={'volume': str(volume)})
        yield metric

        metric = Metric(
            'trafficserver_cache_used_bytes_total',
            'Total cache used in bytes.',
            'gauge')
        metric.add_sample(
            'trafficserver_cache_used_bytes_total',
            value=float(data[
                'proxy.process.cache.volume_{0}.bytes_total'.format(volume)]),
            labels={'volume': str(volume)})
        yield metric

        metric = Metric(
            'trafficserver_cache_operations_total',
            'Cache operation count.',
            'counter')
        for op in ('lookup', 'read', 'write', 'update', 'remove',
                   'evacuate', 'scan', 'read_busy'):
            for result in ('success', 'failure'):
                k = 'proxy.process.cache.volume_{volume}.{op}.{result}'.format(
                    volume=volume, op=op, result=result)
                metric.add_sample(
                    'trafficserver_cache_operations_total',
                    value=float(data[k]),
                    labels={'volume': str(volume),
                            'operation': op,
                            'result': result})
        yield metric
