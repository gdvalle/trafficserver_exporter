import argparse
import logging

from prometheus_client import REGISTRY, ProcessCollector

from .collector import StatsPluginCollector
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
    '--pidfile', dest='pidfile', default='/var/run/trafficserver/server.lock',
    help='Path to trafficserver PID file; used with --procstats')
ARGS.add_argument(
    '--no-procstats', dest='no_procstats', default=False, action='store_true',
    help='Disable process metric collection')
ARGS.add_argument(
    '-v', '--verbose', action='count', dest='level',
    default=0, help='Verbose logging (repeat for more verbosity)')

LOG = logging.getLogger(__name__)


def get_ts_pid(pidfile):
    try:
        with open(pidfile) as f:
            pid = f.readline()
    except EnvironmentError:
        LOG.warning('Unable to read pidfile; process metrics will fail!')
        pid = None
    return pid


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

    LOG.debug('Starting HTTP server')
    httpd_thread = start_http_server(args.port, addr=args.addr)

    LOG.debug('Registering StatsPluginCollector')
    REGISTRY.register(StatsPluginCollector(args.endpoint))

    if not args.no_procstats:
        LOG.debug('Registering ProcessCollector')
        REGISTRY.register(ProcessCollector(
            pid=lambda: get_ts_pid(args.pidfile),
            namespace='trafficserver'))

    LOG.info('Listening on :{port}'.format(port=args.port))

    # Wait for the webserver
    httpd_thread.join()
