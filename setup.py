from setuptools import setup

setup(
    name="trafficserver_exporter",
    version="0.0.1",
    author="Greg Dallavalle",
    description="Traffic Server metrics exporter for Prometheus",
    long_description=__doc__,
    entry_points={
        'console_scripts': [
            'trafficserver_exporter=trafficserver_exporter.cli'
        ],
    },
    install_requires=[
        "prometheus_client>=0.0.11",
        "requests>=2.0.0"
    ],
    packages=["trafficserver_exporter"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "Topic :: System :: Networking :: Monitoring",
        "License :: OSI Approved :: Apache Software License",
    ],
    license="Apache Software License 2.0",
)
