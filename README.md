# trafficserver_exporter

[![Linux build status](https://travis-ci.org/gdvalle/trafficserver_exporter.svg?branch=master)](https://travis-ci.org/gdvalle/trafficserver_exporter)

An Apache Traffic Server metrics exporter for Prometheus.  Uses the stats_over_http plugin to translate JSON data into Prometheus format.


## Development
```
virtualenv venv
. venv/bin/activate
pip install -e .
trafficserver_exporter -vv --endpoint=http://trafficserver/_stats
```
