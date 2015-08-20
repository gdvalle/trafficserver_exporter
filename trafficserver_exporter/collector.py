#!/usr/bin/env python

from prometheus_client import Metric
import logging
import json
import requests

HTTP_VERBS = ('GET', 'HEAD', 'POST', 'PUT', 'PUSH', 'DELETE', 'PURGE')
HTTP_VERBS_LOWER = tuple([v.lower() for v in HTTP_VERBS])

TS_RESPONSE_CODES = ('100', '101', '1xx', '200', '201', '202', '203', '204',
                     '205', '206', '2xx', '300', '301', '302', '303', '304',
                     '305', '307', '3xx', '400', '401', '402', '403', '404',
                     '405', '406', '407', '408', '409', '410', '411', '412',
                     '413', '414', '415', '416', '4xx', '500', '501', '502',
                     '503', '504', '505', '5xx')

log = logging.getLogger(__name__)


class TrafficServerCollector(object):
    def __init__(self, endpoint):
        self._endpoint = endpoint
        self.log = log

    def get_json(self):
        return json.loads(
            requests.get(self._endpoint).content.decode('UTF-8'))['global']

    def collect(self):
        self.log.debug('Beginning collection')

        self.log.debug('Fetching JSON: {0}'.format(self._endpoint))
        data = self.get_json()

        self.log.debug('Gathering metrics')
        for metric in self.parse_metrics(data):
            yield metric

        self.log.debug('Collection complete')

    def parse_metrics(self, data):
        # Counter for server restarts
        metric = Metric(
            'trafficserver_restart_count',
            'Count of traffic_server restarts.',
            'counter')
        metric.add_sample(
            'trafficserver_restart_count',
            value=data['proxy.node.restarts.proxy.restart_count'],
            labels={})
        yield metric

        #
        # HTTP
        #
        # Connections
        metric = Metric(
            'trafficserver_http_connections_total',
            'HTTP connection count.',
            'counter')
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_client_connections'],
            labels={'source': 'client'})
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_server_connections'],
            labels={'source': 'server'})
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_parent_proxy_connections'],
            labels={'source': 'parent_proxy'})
        yield metric

        # Incoming requests
        metric = Metric(
            'trafficserver_http_requests_incoming',
            'Incoming HTTP requests.',
            'gauge')
        metric.add_sample(
            'trafficserver_http_requests_incoming',
            value=data['proxy.process.http.incoming_requests'],
            labels={})
        yield metric

        # Client aborts
        metric = Metric(
            'trafficserver_http_client_aborts_total',
            'HTTP client aborts.',
            'counter')
        metric.add_sample(
            'trafficserver_http_client_aborts_total',
            value=data['proxy.process.http.err_client_abort_count_stat'],
            labels={})
        yield metric

        # Connect fails
        metric = Metric(
            'trafficserver_http_connect_fail_total',
            'HTTP connect failures.',
            'counter')
        metric.add_sample(
            'trafficserver_http_connect_fail_total',
            value=data['proxy.process.http.err_connect_fail_count_stat'],
            labels={})
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
            labels={'source': 'user_agent'})
        metric.add_sample(
            'trafficserver_transactions_total',
            value=data[('proxy.node.http.'
                        'origin_server_total_transactions_count')],
            labels={'source': 'origin_server'})
        yield metric

        # Transaction time spent, total
        metric = Metric(
            'trafficserver_transactions_time_total',
            'Total HTTP transaction time.',
            'counter')
        metric.add_sample(
            'trafficserver_transactions_time_total',
            value=data['proxy.process.http.total_transactions_time'],
            labels={})
        yield metric

        # Transaction time spent, hits
        metric = Metric(
            'trafficserver_hit_transaction_time_total',
            'Total cache hit transaction time.',
            'counter')
        metric.add_sample(
            'trafficserver_hit_transaction_time_total',
            value=data['proxy.process.http.transaction_totaltime.hit_fresh'],
            labels={'state': 'fresh'})
        metric.add_sample(
            'trafficserver_hit_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.'
                        'hit_revalidated')],
            labels={'state': 'revalidated'})
        yield metric

        # Transaction time spent, misses
        metric = Metric(
            'trafficserver_miss_transaction_time_total',
            'Total cache miss transaction time.',
            'counter')
        metric.add_sample(
            'trafficserver_miss_transaction_time_total',
            value=data['proxy.process.http.transaction_totaltime.miss_cold'],
            labels={'state': 'cold'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.'
                        'miss_not_cacheable')],
            labels={'state': 'not_cacheable'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.'
                        'miss_changed')],
            labels={'state': 'changed'})
        metric.add_sample(
            'trafficserver_miss_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.'
                        'miss_client_no_cache')],
            labels={'state': 'no_cache'})
        yield metric

        # Transaction time spent, errors
        metric = Metric(
            'trafficserver_error_transaction_time_total',
            'Total cache error transaction time.',
            'counter')
        metric.add_sample(
            'trafficserver_error_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.errors.'
                        'aborts')],
            labels={'state': 'abort'})
        metric.add_sample(
            'trafficserver_error_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.errors.'
                        'possible_aborts')],
            labels={'state': 'possible_abort'})
        metric.add_sample(
            'trafficserver_error_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.errors.'
                        'connect_failed')],
            labels={'state': 'connect_failed'})
        metric.add_sample(
            'trafficserver_error_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.errors.'
                        'other')],
            labels={'state': 'other'})
        yield metric

        # Transaction time spent, other
        metric = Metric(
            'trafficserver_other_transaction_time_total',
            'Total other/unclassified transaction time.',
            'counter')
        metric.add_sample(
            'trafficserver_error_transaction_time_total',
            value=data[('proxy.process.http.transaction_totaltime.other.'
                        'unclassified')],
            labels={'state': 'unclassified'})
        yield metric

        # Transaction count, hits
        metric = Metric(
            'trafficserver_http_transaction_hits_total',
            'HTTP transaction hit counts.',
            'counter')
        metric.add_sample(
            'trafficserver_http_transaction_hits_total',
            value=data[('proxy.process.http.transaction_counts.'
                        'hit_fresh')],
            labels={'state': 'fresh'})
        metric.add_sample(
            'trafficserver_http_transaction_hits_total',
            value=data[('proxy.process.http.transaction_counts.'
                        'hit_revalidated')],
            labels={'state': 'revalidated'})
        yield metric

        # Transaction count, misses
        metric = Metric(
            'trafficserver_http_transaction_misses_total',
            'HTTP transaction miss counts.',
            'counter')
        metric.add_sample(
            'trafficserver_http_transaction_misses_total',
            value=data[('proxy.process.http.transaction_counts.'
                        'miss_cold')],
            labels={'state': 'cold'})
        metric.add_sample(
            'trafficserver_http_transaction_misses_total',
            value=data[('proxy.process.http.transaction_counts.'
                        'miss_not_cacheable')],
            labels={'state': 'not_cacheable'})
        metric.add_sample(
            'trafficserver_http_transaction_misses_total',
            value=data[('proxy.process.http.transaction_counts.'
                        'miss_changed')],
            labels={'state': 'changed'})
        yield metric

        # Transaction count, errors
        metric = Metric(
            'trafficserver_http_transaction_errors_total',
            'HTTP transaction error counts.',
            'counter')
        metric.add_sample(
            'trafficserver_http_transaction_errors_total',
            value=data[('proxy.process.http.transaction_counts.errors.'
                        'aborts')],
            labels={'state': 'abort'})
        metric.add_sample(
            'trafficserver_http_transaction_errors_total',
            value=data[('proxy.process.http.transaction_counts.errors.'
                        'possible_aborts')],
            labels={'state': 'possible_abort'})
        metric.add_sample(
            'trafficserver_http_transaction_errors_total',
            value=data[('proxy.process.http.transaction_counts.errors.'
                        'connect_failed')],
            labels={'state': 'connect_failed'})
        metric.add_sample(
            'trafficserver_http_transaction_errors_total',
            value=data[('proxy.process.http.transaction_counts.errors.'
                        'other')],
            labels={'state': 'other'})
        yield metric

        # Transaction count, errors
        metric = Metric(
            'trafficserver_http_transaction_others_total',
            'HTTP transaction other/unclassified counts.',
            'counter')
        metric.add_sample(
            'trafficserver_http_transaction_others_total',
            value=data[('proxy.process.http.transaction_counts.other.'
                        'unclassified')],
            labels={'state': 'unclassified'})
        yield metric

        # HTTP Responses
        metric = Metric(
            'trafficserver_http_responses_total',
            'HTTP responses.',
            'counter')
        for code in TS_RESPONSE_CODES:
            key = 'proxy.process.http.{code}_responses'.format(code=code)
            metric.add_sample(
                'trafficserver_http_responses_total',
                value=data[key],
                labels={'code': code})
        yield metric

        # HTTP Requests
        metric = Metric(
            'trafficserver_http_requests_total',
            'HTTP requests.',
            'counter')
        for method in HTTP_VERBS_LOWER:
            key = 'proxy.process.http.{method}_requests'.format(method=method)
            metric.add_sample(
                'trafficserver_http_requests_total',
                value=data[key],
                labels={'method': method})
        yield metric

        # Invalid requests
        metric = Metric(
            'trafficserver_client_requests_invalid_total',
            'Invalid client requests.',
            'counter')
        metric.add_sample(
            'trafficserver_client_requests_invalid_total',
            value=data['proxy.process.http.invalid_client_requests'],
            labels={})
        yield metric

        # Requests without Host header
        metric = Metric(
            'trafficserver_client_requests_missing_host_hdr_total',
            'Client requests missing host header.',
            'counter')
        metric.add_sample(
            'trafficserver_client_requests_missing_host_hdr_total',
            value=data['proxy.process.http.missing_host_hdr'],
            labels={})
        yield metric

        # Request size
        metric = Metric(
            'trafficserver_http_request_size_bytes_total',
            'HTTP request size.',
            'counter')
        metric.add_sample(
            'trafficserver_http_request_size_bytes_total',
            value=data['proxy.node.http.user_agent_total_request_bytes'],
            labels={'source': 'user_agent'})
        metric.add_sample(
            'trafficserver_http_request_size_bytes_total',
            value=data['proxy.node.http.origin_server_total_request_bytes'],
            labels={'source': 'origin_server'})
        metric.add_sample(
            'trafficserver_http_request_size_bytes_total',
            value=data['proxy.node.http.parent_proxy_total_request_bytes'],
            labels={'source': 'parent_proxy'})
        yield metric

        # Response size
        metric = Metric(
            'trafficserver_http_response_size_bytes_total',
            'HTTP response size.',
            'counter')
        metric.add_sample(
            'trafficserver_http_response_size_bytes_total',
            value=data['proxy.node.http.user_agent_total_response_bytes'],
            labels={'source': 'user_agent'})
        metric.add_sample(
            'trafficserver_http_response_size_bytes_total',
            value=data['proxy.node.http.origin_server_total_response_bytes'],
            labels={'source': 'origin_server'})
        metric.add_sample(
            'trafficserver_http_response_size_bytes_total',
            value=data['proxy.node.http.parent_proxy_total_response_bytes'],
            labels={'source': 'parent_proxy'})
        yield metric

        # Cache hits
        metric = Metric(
            'trafficserver_http_cache_hits_total',
            'HTTP cache hit count.',
            'counter')
        metric.add_sample(
            'trafficserver_http_cache_hits_total',
            value=data['proxy.process.http.cache_hit_fresh'],
            labels={'state': 'fresh'})
        metric.add_sample(
            'trafficserver_http_cache_hits_total',
            value=data['proxy.process.http.cache_hit_stale_served'],
            labels={'state': 'stale'})
        metric.add_sample(
            'trafficserver_http_cache_hits_total',
            value=data['proxy.process.http.cache_hit_ims'],
            labels={'state': 'ims'})
        metric.add_sample(
            'trafficserver_http_cache_hits_total',
            value=data['proxy.process.http.cache_hit_revalidated'],
            labels={'state': 'revalidated'})
        yield metric

        # Cache misses
        metric = Metric(
            'trafficserver_http_cache_misses_total',
            'HTTP cache miss count.',
            'counter')
        metric.add_sample(
            'trafficserver_http_cache_misses_total',
            value=data['proxy.process.http.cache_miss_cold'],
            labels={'state': 'cold'})
        metric.add_sample(
            'trafficserver_http_cache_misses_total',
            value=data['proxy.process.http.cache_miss_changed'],
            labels={'state': 'changed'})
        metric.add_sample(
            'trafficserver_http_cache_misses_total',
            value=data['proxy.process.http.cache_miss_client_no_cache'],
            labels={'state': 'client_no_cache'})
        metric.add_sample(
            'trafficserver_http_cache_misses_total',
            value=data['proxy.process.http.cache_miss_ims'],
            labels={'state': 'ims'})
        yield metric

        #
        # Cache
        #
        # RAM Cache hits
        metric = Metric(
            'trafficserver_ram_cache_hits_total',
            'RAM cache hit count.',
            'counter')
        metric.add_sample(
            'trafficserver_ram_cache_hits_total',
            value=data['proxy.process.cache.ram_cache.hits'],
            labels={})
        yield metric

        # RAM Cache hits
        metric = Metric(
            'trafficserver_ram_cache_misses_total',
            'RAM cache miss count.',
            'counter')
        metric.add_sample(
            'trafficserver_ram_cache_misses_total',
            value=data['proxy.process.cache.ram_cache.misses'],
            labels={})
        yield metric

        # Cache avail
        metric = Metric(
            'trafficserver_cache_avail_size',
            'Total cache available.',
            'gauge')
        metric.add_sample(
            'trafficserver_cache_avail_size',
            value=data['proxy.process.cache.bytes_total'],
            labels={})
        yield metric

        # Cache used
        metric = Metric(
            'trafficserver_cache_used',
            'Total cache used.',
            'gauge')
        metric.add_sample(
            'trafficserver_cache_used',
            value=data['proxy.process.cache.bytes_used'],
            labels={})
        yield metric

        # RAM Cache avail
        metric = Metric(
            'trafficserver_http_ram_cache_avail_size',
            'RAM cache available.',
            'gauge')
        metric.add_sample(
            'trafficserver_http_ram_cache_avail_size',
            value=data['proxy.process.cache.ram_cache.total_bytes'],
            labels={})
        yield metric

        # RAM Cache used
        metric = Metric(
            'trafficserver_http_ram_cache_used',
            'RAM cache used.',
            'gauge')
        metric.add_sample(
            'trafficserver_http_ram_cache_used',
            value=data['proxy.process.cache.ram_cache.bytes_used'],
            labels={})
        yield metric
