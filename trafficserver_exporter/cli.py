#!/usr/bin/env python

import argparse
import logging
from prometheus_client import REGISTRY
from .collector import TrafficServerCollector
from .http import start_http_server


ARGS = argparse.ArgumentParser(
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    description="Traffic Server exporter for Prometheus")
ARGS.add_argument(
    '--endpoint', dest='endpoint', default='http://127.0.0.1/_stats',
    help="Traffic Server's stats_over_http plugin URL")
ARGS.add_argument(
    '--addr', dest='addr', default='', help='Address to bind and listen on')
ARGS.add_argument(
    '--port', dest='port', default=9122, help='Port to bind and listen on')
ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level',
    default=0, help='Verbose logging (repeat for more verbosity)')

log = logging.getLogger(__name__)


def main():
    """Main program.

    Parse arguments, start webserver to serve /metrics.
    """
    args = ARGS.parse_args()

    if args.level >= 2:
        logging.basicConfig(level=logging.DEBUG)
    elif args.level == 1:
        logging.basicConfig(level=logging.INFO)
    elif args.level == 0:
        logging.basicConfig(level=logging.WARNING)

    log.debug('Starting HTTP server')
    httpd_thread = start_http_server(args.port, addr=args.addr)
    log.debug('Registering collector')
    REGISTRY.register(TrafficServerCollector(args.endpoint))
    log.info('Listening on :{port}'.format(port=args.port))

    # Wait for the webserver
    httpd_thread.join()


if __name__ == '__main__':
    main()
