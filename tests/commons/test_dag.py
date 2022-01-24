from pathlib import Path

import pytest
from ploomber.spec import DAGSpec

from soopervisor.commons.dag import _product_prefixes_from_spec

simple = """
tasks:
  - source: tasks/load.py
    product: output/load.ipynb
"""

absolute = """
tasks:
  - source: tasks/load.py
    product: /path/to/output/load.ipynb

  - source: tasks/clean.py
    product: output/load.ipynb
"""

multiple_products = """
tasks:
  - source: tasks/load.py
    product:
      nb: output/load.ipynb
      data: data/load.csv
"""

sql_products = """
tasks:
  - source: tasks/select.sql
    product: [schema, name, table]

  - source: tasks/query.sql
    product: data/dump.csv

  - source: tasks/more.sql
    product:
     one: /path/to/data/dump.csv
     another: output/dump.csv

  - source: tasks/another.sql
    product:
      one: [schema, name, table]
      two: [schema, another, table]
"""


@pytest.mark.parametrize('spec, expected', [
    [simple, {'output'}],
    [absolute, {'output'}],
    [multiple_products, {'data', 'output'}],
    [sql_products, {'data', 'output'}],
])
def test_product_prefixes_from_spec(tmp_empty, spec, expected):
    Path('pipeline.yaml').write_text(spec)

    spec = DAGSpec('pipeline.yaml')

    assert _product_prefixes_from_spec(spec) == expected
