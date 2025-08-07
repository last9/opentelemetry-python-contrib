OpenTelemetry OpenSearch Instrumentation
========================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opentelemetry-instrumentation-opensearch.svg
   :target: https://pypi.org/project/opentelemetry-instrumentation-opensearch/

This library allows tracing HTTP requests made by the
`opensearch-py <https://github.com/opensearch-project/opensearch-py>`_ library.

Usage
-----

.. code-block:: python

    from opentelemetry.instrumentation.opensearch import OpenSearchInstrumentor
    import opensearchpy

    # instrument opensearch
    OpenSearchInstrumentor().instrument()

    # Using opensearch as normal now will automatically generate spans
    client = opensearchpy.OpenSearch()
    client.index(index='my-index', id=1, body={'my': 'data', 'timestamp': '2023-01-01'})
    client.get(index='my-index', id=1)

API
---
.. automodule:: opentelemetry.instrumentation.opensearch
    :members:
    :undoc-members:
    :show-inheritance: