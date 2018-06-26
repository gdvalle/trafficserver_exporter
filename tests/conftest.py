import glob
import json
import os

import pytest

DATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(os.path.realpath(__file__)), "data")
)

STATS_JSON_FILES = []
for fname in glob.glob("{}{}{}".format(DATA_DIR, os.sep, "*.json")):
    with open(fname) as f:
        STATS_JSON_FILES.append(json.loads(f.read()))


@pytest.fixture(scope="session", params=STATS_JSON_FILES)
def stats_json(request):
    return request.param
