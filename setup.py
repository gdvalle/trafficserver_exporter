from setuptools import setup

setup(
    name="trafficserver_exporter",
    version="0.0.1",
    author="Greg Dallavalle",
    description="Traffic Server stats_over_http exporter for Prometheus",
    long_description=__doc__,
    scripts=["scripts/trafficserver_exporter"],
    install_requires=[
        'prometheus_client',
        'requests',
    ],
    packages=['trafficserver_exporter'],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: Apache Software License",
    ],
)
