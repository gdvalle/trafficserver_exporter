# trafficserver_exporter

An Apache Traffic Server metrics exporter for Prometheus.  Uses the stats_over_http plugin to translate JSON data into Prometheus format.


## Development
```
virtualenv venv
. venv/bin/activate
pip install -e .
trafficserver_exporter -vv --endpoint=http://trafficserver/_stats
```
