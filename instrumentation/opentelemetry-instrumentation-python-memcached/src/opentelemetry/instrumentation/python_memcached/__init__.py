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

"""

Usage
-----

The OpenTelemetry ``python-memcached`` integration traces python-memcached client operations

Usage
-----

.. code-block:: python

    from opentelemetry.instrumentation.python_memcached import PythonMemcachedInstrumentor

    PythonMemcachedInstrumentor().instrument()

    import memcache
    client = memcache.Client(['127.0.0.1:11211'])
    client.set('some_key', 'some_value')

API
---
"""

import logging
from typing import Collection

import memcache
from wrapt import wrap_function_wrapper as _wrap

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.python_memcached.package import _instruments
from opentelemetry.instrumentation.python_memcached.version import __version__
from opentelemetry.instrumentation.utils import unwrap
from opentelemetry.semconv.trace import NetTransportValues, SpanAttributes
from opentelemetry.trace import SpanKind, get_tracer

logger = logging.getLogger(__name__)


COMMANDS = [
    "set",
    "set_multi",
    "add",
    "replace",
    "append",
    "prepend",
    "cas",
    "get",
    "get_multi",
    "gets",
    "delete",
    "delete_multi",
    "incr",
    "decr",
    "touch",
    "get_stats",
    "get_slabs",
    "get_slab_stats",
    "flush_all",
]


def _set_connection_attributes(span, instance):
    if not span.is_recording():
        return
    for key, value in _get_address_attributes(instance).items():
        span.set_attribute(key, value)


def _with_tracer_wrapper(func):
    """Helper for providing tracer for wrapper functions."""

    def _with_tracer(tracer, cmd):
        def wrapper(wrapped, instance, args, kwargs):
            # prevent double wrapping
            if hasattr(wrapped, "__wrapped__"):
                return wrapped(*args, **kwargs)

            return func(tracer, cmd, wrapped, instance, args, kwargs)

        return wrapper

    return _with_tracer


@_with_tracer_wrapper
def _wrap_cmd(tracer, cmd, wrapped, instance, args, kwargs):
    with tracer.start_as_current_span(
        cmd, kind=SpanKind.CLIENT, attributes={}
    ) as span:
        try:
            if span.is_recording():
                if not args:
                    vals = ""
                else:
                    vals = _get_query_string(args[0])

                query = f"{cmd}{' ' if vals else ''}{vals}"
                span.set_attribute(SpanAttributes.DB_STATEMENT, query)

                _set_connection_attributes(span, instance)
        except Exception as ex:
            logger.warning(
                "Failed to set attributes for python-memcached span %s", str(ex)
            )

        return wrapped(*args, **kwargs)


def _get_query_string(arg):
    """Return the query values given the first argument to a python-memcached command.

    If there are multiple query values, they are joined together
    space-separated.
    """
    keys = ""

    if isinstance(arg, dict):
        arg = list(arg)

    if isinstance(arg, str):
        keys = arg
    elif isinstance(arg, bytes):
        keys = arg.decode()
    elif isinstance(arg, list) and len(arg) >= 1:
        if isinstance(arg[0], str):
            keys = " ".join(arg)
        elif isinstance(arg[0], bytes):
            keys = b" ".join(arg).decode()

    return keys


def _get_address_attributes(instance):
    """Attempt to get host and port from Client instance."""
    address_attributes = {}
    address_attributes[SpanAttributes.DB_SYSTEM] = "memcached"

    # python-memcached Client contains servers attribute which is a list of _Host objects
    # Each _Host object has ip, port, and address attributes
    if hasattr(instance, "servers") and instance.servers:
        first_server = instance.servers[0]
        if hasattr(first_server, "ip") and hasattr(first_server, "port"):
            address_attributes[SpanAttributes.NET_PEER_NAME] = first_server.ip
            address_attributes[SpanAttributes.NET_PEER_PORT] = first_server.port
            address_attributes[SpanAttributes.NET_TRANSPORT] = (
                NetTransportValues.IP_TCP.value
            )
        elif hasattr(first_server, "address"):
            if isinstance(first_server.address, tuple) and len(first_server.address) == 2:
                host, port = first_server.address
                address_attributes[SpanAttributes.NET_PEER_NAME] = host
                address_attributes[SpanAttributes.NET_PEER_PORT] = port
                address_attributes[SpanAttributes.NET_TRANSPORT] = (
                    NetTransportValues.IP_TCP.value
                )

    return address_attributes


class PythonMemcachedInstrumentor(BaseInstrumentor):
    """An instrumentor for python-memcached See `BaseInstrumentor`"""

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        tracer_provider = kwargs.get("tracer_provider")
        tracer = get_tracer(
            __name__,
            __version__,
            tracer_provider,
            schema_url="https://opentelemetry.io/schemas/1.11.0",
        )

        for cmd in COMMANDS:
            _wrap(
                "memcache",
                f"Client.{cmd}",
                _wrap_cmd(tracer, cmd),
            )

    def _uninstrument(self, **kwargs):
        for command in COMMANDS:
            unwrap(memcache.Client, f"{command}")