# trafficserver_exporter

An Apache Traffic Server metrics exporter for Prometheus.  Uses the stats_over_http plugin to translate JSON data into Prometheus format.


## Development
```
virtualenv venv
. venv/bin/activate
pip install -e .
python -m trafficserver_exporter.cli --endpoint=http://trafficserver/_stats
```


## Packaging Examples

### Debian
```
pip install stdeb
python setup.py --command-packages=stdeb.command bdist_deb
dpkg -i deb_dist/python-trafficserver-exporter_0.0.1-1_all.deb
```
