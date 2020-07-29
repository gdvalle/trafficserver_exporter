import threading

from prometheus_client.exposition import MetricsHandler

try:
    from http.server import HTTPServer
except ImportError:
    # Py2
    from BaseHTTPServer import HTTPServer


def start_http_server(port, addr=""):
    """Starts a HTTP server for prometheus metrics as a daemon thread."""

    class PrometheusMetricsServer(threading.Thread):
        def run(self):
            httpd = HTTPServer((addr, port), MetricsHandler)
            httpd.serve_forever()

    t = PrometheusMetricsServer()
    t.daemon = True
    t.start()
    return t
