FROM       alpine:3.8
LABEL      maintainer="greg.dallavalle@gmail.com"
EXPOSE     9122
ENTRYPOINT ["/usr/bin/trafficserver_exporter"]

ENV APPPATH /app
WORKDIR $APPPATH

COPY setup.py .
COPY trafficserver_exporter ./trafficserver_exporter

RUN apk add --no-cache py3-setuptools ca-certificates \
    && python3 setup.py install \
    && cd / \
    && rm -r $APPPATH
