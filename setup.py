"""
trafficserver_exporter
----------------------

An Apache Traffic Server metrics exporter for Prometheus.  Uses the
stats_over_http plugin to translate JSON data into Prometheus format.

"""

from setuptools import setup

setup(
    name='trafficserver_exporter',
    version='0.0.1',
    author='Greg Dallavalle',
    description='Traffic Server metrics exporter for Prometheus',
    long_description=__doc__,
    entry_points={
        'console_scripts': [
            'trafficserver_exporter=trafficserver_exporter.__main__:main'
        ],
    },
    install_requires=[
        'prometheus_client>=0.0.11',
        'requests>=2.0.0'
    ],
    keywords='prometheus monitoring trafficserver',
    packages=['trafficserver_exporter'],
    classifiers=[
        'Development Status :: 3 - Alpha',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.6',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.2',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Intended Audience :: Information Technology',
        'Intended Audience :: System Administrators',
        'Topic :: System :: Monitoring',
        'Topic :: System :: Networking :: Monitoring',
        'License :: OSI Approved :: Apache Software License',
    ],
    license='Apache Software License 2.0',
)
