#!/usr/bin/env python

from prometheus_client import Metric
import requests


class TrafficServerCollector(object):
    def __init__(self, endpoint):
        self._endpoint = endpoint

    def collect(self):
        # Fetch the JSON
        data = requests.get(self._endpoint).json()['global']

        # Counter for server restarts
        metric = Metric(
            'trafficserver_restart_count',
            'Count of traffic_server restarts',
            'counter')
        metric.add_sample(
            'trafficserver_restart_count',
            value=data['proxy.node.restarts.proxy.restart_count'],
            labels={})
        yield metric

        #
        # Cache
        #
        metric = Metric(
            'trafficserver_cache_misses_total',
            'Cache MISS total',
            'counter')
        metric.add_sample(
            'trafficserver_cache_misses_total',
            value=data['proxy.node.cache_total_misses'],
            labels={})
        yield metric

        metric = Metric(
            'trafficserver_cache_hits_total',
            'Cache HIT total',
            'counter')
        metric.add_sample(
            'trafficserver_cache_hits_total',
            value=data['proxy.node.cache_total_hits'],
            labels={})
        yield metric

        #
        # HTTP
        #
        metric = Metric(
            'trafficserver_http_connections_total',
            'Connection count',
            'counter')
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_client_connections'],
            labels={'type': 'client'})
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_server_connections'],
            labels={'type': 'server'})
        metric.add_sample(
            'trafficserver_http_connections_total',
            value=data['proxy.process.http.total_parent_proxy_connections'],
            labels={'type': 'parent_proxy'})
        yield metric
