# Copyright The OpenTelemetry Authors
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import os
from unittest import mock

import opensearchpy
import opensearchpy.exceptions
from opensearchpy import OpenSearch
from pytest import mark

import opentelemetry.instrumentation.opensearch
from opentelemetry import trace
from opentelemetry.instrumentation.opensearch import (
    OpenSearchInstrumentor,
)
from opentelemetry.instrumentation.opensearch.utils import sanitize_body
from opentelemetry.semconv._incubating.attributes.db_attributes import (
    DB_STATEMENT,
    DB_SYSTEM,
)
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace import StatusCode


def get_opensearch_client(*args, **kwargs):
    client = OpenSearch(*args, **kwargs)
    return client


@mock.patch("opensearchpy.connection.http_urllib3.Urllib3HttpConnection.perform_request")
class TestOpenSearchIntegration(TestBase):
    search_attributes = {
        DB_SYSTEM: "opensearch",
        "opensearch.url": "/test-index/_search",
        "opensearch.method": "GET",
        "opensearch.target": "test-index",
        DB_STATEMENT: str({"query": {"bool": {"filter": "?"}}}),
    }

    create_attributes = {
        DB_SYSTEM: "opensearch",
        "opensearch.url": "/test-index",
        "opensearch.method": "HEAD",
    }

    def setUp(self):
        super().setUp()
        self.tracer = self.tracer_provider.get_tracer(__name__)
        OpenSearchInstrumentor().instrument()

    def tearDown(self):
        super().tearDown()
        OpenSearchInstrumentor().uninstrument()

    def test_instrumentor(self, mock_perform_request):
        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.search(index="test-index", body={"query": {"bool": {"filter": {}}}})

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "OpenSearch/<target>/_search")
        # Check individual attributes since the order might be different
        self.assertEqual(span.attributes[DB_SYSTEM], "opensearch")
        self.assertEqual(span.attributes["opensearch.url"], "/test-index/_search")
        self.assertEqual(span.attributes["opensearch.method"], "POST")
        self.assertEqual(span.attributes["opensearch.target"], "test-index")
        self.assertIn(DB_STATEMENT, span.attributes)

    def test_simple_call(self, mock_perform_request):
        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.ping()

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "OpenSearch/")
        self.assertEqual(span.attributes[DB_SYSTEM], "opensearch")

    def test_call_with_body(self, mock_perform_request):
        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.index(
            index="test-index",
            id=1,
            body={"test": "data"},
        )

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "OpenSearch/test-index/_doc/:id")
        self.assertIn(DB_SYSTEM, span.attributes)
        self.assertEqual(span.attributes[DB_SYSTEM], "opensearch")

    def test_result_values_in_span_attributes(self, mock_perform_request):
        response_body = {
            "took": 2,
            "timed_out": False,
            "_shards": {"total": 5, "successful": 5, "skipped": 0, "failed": 0},
            "hits": {"total": {"value": 0, "relation": "eq"}, "max_score": None, "hits": []},
        }
        mock_perform_request.return_value = (200, {}, json.dumps(response_body))

        client = get_opensearch_client()
        client.search(index="test-index", body={"query": {"match_all": {}}})

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.attributes["opensearch.took"], "2")
        self.assertEqual(span.attributes["opensearch.timed_out"], "False")

    def test_url_sanitization(self, mock_perform_request):
        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.get(index="test-index", id="test-document-id")

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "OpenSearch/test-index/_doc/:id")
        self.assertEqual(span.attributes["opensearch.id"], "test-document-id")

    def test_search_sanitization(self, mock_perform_request):
        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.search(
            index="test-index",
            body={"query": {"bool": {"filter": {"term": {"status": "published"}}}}},
        )

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "OpenSearch/<target>/_search")
        self.assertEqual(span.attributes["opensearch.target"], "test-index")

    def test_exception_handling(self, mock_perform_request):
        mock_perform_request.side_effect = opensearchpy.exceptions.NotFoundError(
            404, "index_not_found_exception", {"error": {"type": "index_not_found_exception"}}
        )

        client = get_opensearch_client()
        try:
            client.get(index="non-existent-index", id="1")
        except opensearchpy.exceptions.NotFoundError:
            pass

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.status.status_code, StatusCode.ERROR)

    def test_prefix_override(self, mock_perform_request):
        OpenSearchInstrumentor().uninstrument()
        OpenSearchInstrumentor("MyCustomPrefix").instrument()

        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.ping()

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "MyCustomPrefix/")

    def test_env_prefix_override(self, mock_perform_request):
        OpenSearchInstrumentor().uninstrument()
        with mock.patch.dict(
            os.environ, {"OTEL_PYTHON_OPENSEARCH_NAME_PREFIX": "EnvPrefix"}
        ):
            OpenSearchInstrumentor().instrument()

        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.ping()

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.name, "EnvPrefix/")

    def test_request_hook(self, mock_perform_request):
        def request_hook(span, method, url, kwargs):
            if span and span.is_recording():
                span.set_attribute("custom.request.attribute", "request-value")

        OpenSearchInstrumentor().uninstrument()
        OpenSearchInstrumentor().instrument(request_hook=request_hook)

        mock_perform_request.return_value = (200, {}, {})

        client = get_opensearch_client()
        client.ping()

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.attributes["custom.request.attribute"], "request-value")

    def test_response_hook(self, mock_perform_request):
        def response_hook(span, response):
            if span and span.is_recording():
                span.set_attribute("custom.response.attribute", "response-value")

        OpenSearchInstrumentor().uninstrument()
        OpenSearchInstrumentor().instrument(response_hook=response_hook)

        mock_perform_request.return_value = (200, {}, {"test": "response"})

        client = get_opensearch_client()
        client.ping()

        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        span = spans[0]
        self.assertEqual(span.attributes["custom.response.attribute"], "response-value")

    def test_body_sanitization(self, mock_perform_request):
        test_body = {
            "query": {
                "bool": {
                    "filter": [{"term": {"status": "published"}}],
                    "should": [{"match": {"title": "test"}}],
                }
            }
        }

        sanitized = sanitize_body(test_body)
        expected = str({
            "query": {
                "bool": {
                    "filter": "?",
                    "should": "?",
                }
            }
        })
        self.assertEqual(sanitized, expected)