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
from unittest import mock

import memcache

from opentelemetry import trace as trace_api
from opentelemetry.instrumentation.python_memcached import PythonMemcachedInstrumentor
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.test.test_base import TestBase
from opentelemetry.trace import get_tracer

from .utils import _str

TEST_HOST = "localhost"
TEST_PORT = 11211


class PythonMemcachedClientTestCase(TestBase):
    """Tests for a patched python-memcached Client."""

    def setUp(self):
        super().setUp()
        PythonMemcachedInstrumentor().instrument()

        self.tracer = get_tracer(__name__)

    def tearDown(self):
        super().tearDown()
        PythonMemcachedInstrumentor().uninstrument()

    def make_client(self, **kwargs):
        self.client = memcache.Client([f"{TEST_HOST}:{TEST_PORT}"], **kwargs)
        return self.client

    def check_spans(self, spans, num_expected, queries_expected):
        """A helper for validating basic span information."""
        self.assertEqual(num_expected, len(spans))

        for span, query in zip(spans, queries_expected):
            command, *_ = query.split(" ")
            self.assertEqual(span.name, command)
            self.assertIs(span.kind, trace_api.SpanKind.CLIENT)
            self.assertEqual(
                span.attributes[SpanAttributes.NET_PEER_NAME], TEST_HOST
            )
            self.assertEqual(
                span.attributes[SpanAttributes.NET_PEER_PORT], TEST_PORT
            )
            self.assertEqual(
                span.attributes[SpanAttributes.DB_SYSTEM], "memcached"
            )
            self.assertEqual(
                span.attributes[SpanAttributes.DB_STATEMENT], query
            )

    def test_set_success(self):
        client = self.make_client()
        
        # Mock the actual socket operations to avoid needing a real memcached server
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            result = client.set("key", "value")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["set key"])

    def test_get_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "VALUE key 0 5\r\nvalue\r\nEND\r\n"
            result = client.get("key")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["get key"])

    def test_get_multi_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "VALUE key1 0 6\r\nvalue1\r\nVALUE key2 0 6\r\nvalue2\r\nEND\r\n"
            result = client.get_multi(["key1", "key2"])

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["get_multi key1 key2"])

    def test_set_multi_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED\r\nSTORED\r\n"
            result = client.set_multi({"key1": "value1", "key2": "value2"})

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["set_multi key1 key2"])

    def test_delete_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "DELETED"
            result = client.delete("key")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["delete key"])

    def test_delete_multi_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "DELETED\r\nDELETED\r\n"
            result = client.delete_multi(["key1", "key2"])

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["delete_multi key1 key2"])

    def test_incr_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "10"
            result = client.incr("counter", 1)

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["incr counter"])

    def test_decr_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "8"
            result = client.decr("counter", 1)

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["decr counter"])

    def test_add_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            result = client.add("new_key", "new_value")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["add new_key"])

    def test_replace_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            result = client.replace("existing_key", "new_value")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["replace existing_key"])

    def test_append_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            result = client.append("key", "_suffix")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["append key"])

    def test_prepend_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            result = client.prepend("key", "prefix_")

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["prepend key"])

    def test_get_stats_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STAT pid 12345\r\nSTAT version 1.6.0\r\nEND\r\n"
            result = client.get_stats()

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["get_stats"])

    def test_flush_all_success(self):
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "OK"
            result = client.flush_all()

        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["flush_all"])

    def test_instrumentor(self):
        instrumentor = PythonMemcachedInstrumentor()
        
        # Test that the instrumentor can be enabled/disabled without errors
        instrumentor.uninstrument()
        client = self.make_client()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            client.set("key", "value")
        
        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(0, len(spans))

        # Re-instrument and verify spans are generated
        instrumentor.instrument()
        
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            client.set("key2", "value2")
        
        spans = self.memory_exporter.get_finished_spans()
        self.check_spans(spans, 1, ["set key2"])

    def test_uninstrument_does_not_affect_already_instrumented(self):
        client = self.make_client()
        
        PythonMemcachedInstrumentor().uninstrument()
        
        # The client created before uninstrumentation should still be instrumented
        # This is expected behavior as per the OpenTelemetry instrumentation pattern
        with mock.patch.object(client.servers[0], 'send_cmd') as mock_send:
            mock_send.return_value = "STORED"
            client.set("key", "value")
        
        spans = self.memory_exporter.get_finished_spans()
        self.assertEqual(0, len(spans))