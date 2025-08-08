OpenTelemetry Django Functions Auto-Instrumentation
==================================================

|pypi|

.. |pypi| image:: https://badge.fury.io/py/opentelemetry-instrumentation-django-functions.svg
   :target: https://pypi.org/project/opentelemetry-instrumentation-django-functions/

This library automatically instruments Django functions and middleware to create internal spans for detailed tracing.
It extends the standard Django instrumentation by providing granular visibility into Django application internals.

Installation
------------

::

    pip install opentelemetry-instrumentation-django-functions


Usage
-----

.. code:: python

    from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor

    # Auto-instrument all Django functions
    DjangoFunctionsInstrumentor().instrument()

    # Or with specific configuration
    DjangoFunctionsInstrumentor().instrument(
        instrument_views=True,        # Instrument Django view functions
        instrument_middleware=True,   # Instrument middleware methods  
        instrument_models=True,       # Instrument model operations
        instrument_templates=True,    # Instrument template rendering
        excluded_modules=['myapp.sensitive_module']  # Exclude specific modules
    )

Features
--------

* **View Function Instrumentation**: Automatically traces all Django view functions and class-based views
* **Middleware Instrumentation**: Traces middleware processing methods (process_request, process_response, etc.)
* **Model Operation Tracing**: Optional tracing of Django ORM operations (save, delete, queries)
* **Template Rendering**: Optional tracing of template rendering operations
* **App-Specific Views**: Automatically discovers and instruments views from all installed Django apps
* **Configurable Exclusions**: Exclude sensitive or high-volume modules from instrumentation

Configuration
-------------

Environment Variables
*********************

``OTEL_PYTHON_DJANGO_FUNCTIONS_INSTRUMENT``
    Set to ``false`` to disable the instrumentation entirely.

API
---

.. code:: python

    DjangoFunctionsInstrumentor().instrument(
        instrument_views=True,          # bool: Instrument view functions
        instrument_middleware=True,     # bool: Instrument middleware  
        instrument_models=False,        # bool: Instrument model operations
        instrument_templates=False,     # bool: Instrument template rendering
        excluded_modules=[],           # List[str]: Module patterns to exclude
    )

Span Attributes
---------------

All instrumented functions include the following span attributes:

* ``django.module``: The Python module containing the function
* ``django.function``: The function name
* ``django.component``: The Django component type (view, middleware, model, template)

Examples
--------

Basic Usage
***********

.. code:: python

    from opentelemetry import trace
    from opentelemetry.exporter.jaeger.thrift import JaegerExporter
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor
    from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor

    # Configure tracing
    trace.set_tracer_provider(TracerProvider())
    tracer_provider = trace.get_tracer_provider()

    jaeger_exporter = JaegerExporter(
        agent_host_name="localhost",
        agent_port=6831,
    )

    span_processor = BatchSpanProcessor(jaeger_exporter)
    tracer_provider.add_span_processor(span_processor)

    # Instrument Django functions
    DjangoFunctionsInstrumentor().instrument()

Advanced Configuration
**********************

.. code:: python

    # Instrument only views and middleware, exclude sensitive modules
    DjangoFunctionsInstrumentor().instrument(
        instrument_views=True,
        instrument_middleware=True,
        instrument_models=False,  # Skip model instrumentation for performance
        instrument_templates=False,  # Skip template instrumentation
        excluded_modules=[
            'myapp.payment',  # Exclude payment module
            'admin',          # Exclude admin modules
        ]
    )

References
----------

* `OpenTelemetry Django Instrumentation <https://github.com/open-telemetry/opentelemetry-python-contrib/tree/main/instrumentation/opentelemetry-instrumentation-django>`_
* `OpenTelemetry Python API <https://opentelemetry-python.readthedocs.io/en/latest/api/api.html>`_