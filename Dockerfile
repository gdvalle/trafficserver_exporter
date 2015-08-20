FROM       alpine:3.2
MAINTAINER Greg Dallavalle <greg.dallavalle@gmail.com>
EXPOSE     9211
ENTRYPOINT ["/usr/bin/trafficserver_exporter"]

ENV APPPATH /app
ADD . $APPPATH
WORKDIR $APPATH
RUN apk add --update python \
    && python setup.py install \
    && rm /var/cache/apk/*
