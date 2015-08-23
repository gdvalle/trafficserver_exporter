FROM       alpine:3.2
MAINTAINER Greg Dallavalle <greg.dallavalle@gmail.com>
EXPOSE     9122
ENTRYPOINT ["/usr/bin/trafficserver_exporter"]

ENV APPPATH /app
ADD . $APPPATH
WORKDIR $APPPATH
RUN apk add --update python py-setuptools ca-certificates \
    && python setup.py install \
    && rm /var/cache/apk/* \
    && cd / \
    && rm -r $APPPATH
