# Django Functions Auto-Instrumentation Example

This example demonstrates how to use the OpenTelemetry Django Functions instrumentation to automatically trace Django functions and middleware as internal spans.

## Features Demonstrated

- ✅ **View Function Tracing**: Automatically traces function-based and class-based views
- ✅ **Middleware Tracing**: Traces middleware processing methods (`process_request`, `process_response`, etc.)
- ✅ **Internal Spans**: Creates internal spans showing detailed execution flow
- ✅ **Error Handling**: Properly records exceptions in spans
- ✅ **Configurable**: Shows how to configure what gets instrumented

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the demo:**
   ```bash
   python django_app.py
   ```

3. **Make requests to see traces:**
   ```bash
   # In another terminal
   curl http://localhost:8000/hello/
   curl http://localhost:8000/api/data/
   curl http://localhost:8000/slow/
   curl http://localhost:8000/error/  # This will show error tracing
   ```

## What You'll See

When you make requests, you'll see detailed trace output in the console showing:

1. **HTTP Request Spans**: From the standard Django instrumentation
2. **Middleware Spans**: Internal spans for each middleware method
3. **View Spans**: Internal spans for view functions and methods
4. **Framework Spans**: Internal spans for Django framework functions

### Example Trace Output

```
{
  "name": "GET /hello/",
  "context": {...},
  "kind": "SpanKind.SERVER",
  "parent_id": null,
  "start_time": "2024-01-01T12:00:00.000000Z",
  "end_time": "2024-01-01T12:00:00.150000Z",
  "status": {"status_code": "UNSET"},
  "attributes": {
    "http.method": "GET",
    "http.url": "http://localhost:8000/hello/",
    "http.status_code": 200
  },
  "children": [
    {
      "name": "django.middleware.DemoMiddleware.process_request",
      "kind": "SpanKind.INTERNAL",
      "attributes": {
        "django.module": "__main__",
        "django.function": "process_request",
        "django.component": "middleware"
      }
    },
    {
      "name": "django.app_view.__main__.hello_view",
      "kind": "SpanKind.INTERNAL",
      "attributes": {
        "django.module": "__main__",
        "django.function": "hello_view",
        "django.component": "view"
      }
    },
    {
      "name": "django.middleware.DemoMiddleware.process_response",
      "kind": "SpanKind.INTERNAL",
      "attributes": {
        "django.module": "__main__",
        "django.function": "process_response",
        "django.component": "middleware"
      }
    }
  ]
}
```

## Configuration Options

The example shows different configuration options:

```python
# Full configuration
DjangoFunctionsInstrumentor().instrument(
    instrument_views=True,           # Trace view functions
    instrument_middleware=True,      # Trace middleware methods
    instrument_models=True,          # Trace model operations
    instrument_templates=True,       # Trace template rendering
    excluded_modules=[              # Exclude specific modules
        'sensitive_app.views',
        'admin'
    ]
)

# Minimal configuration (views only)
DjangoFunctionsInstrumentor().instrument(
    instrument_views=True,
    instrument_middleware=False,
    instrument_models=False,
    instrument_templates=False
)
```

## Performance Considerations

- **Overhead**: Each instrumented function adds a small overhead
- **Volume**: High-traffic applications may generate many spans
- **Filtering**: Use `excluded_modules` to skip high-volume or sensitive modules
- **Sampling**: Configure trace sampling in production

## Production Usage

For production use, replace the console exporter with a proper backend:

```python
# Jaeger example
from opentelemetry.exporter.jaeger.thrift import JaegerExporter

jaeger_exporter = JaegerExporter(
    agent_host_name="jaeger",
    agent_port=6831,
)

# OTLP example  
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

otlp_exporter = OTLPSpanExporter(
    endpoint="http://otel-collector:4317"
)
```

## Integration with Standard Django Instrumentation

This instrumentation works alongside the standard OpenTelemetry Django instrumentation:

- **Standard Django**: Traces HTTP requests/responses
- **Django Functions**: Adds internal spans showing detailed execution

Both instrumentations complement each other to provide complete visibility.

## Testing

Run the included tests:

```bash
cd ..
python -m pytest tests/
```

## Troubleshooting

### Common Issues

1. **No spans appearing**: Check that Django is properly configured and the app is running
2. **Import errors**: Ensure all dependencies are installed
3. **Performance issues**: Use `excluded_modules` to reduce instrumentation scope

### Debug Mode

Enable debug logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

This will show detailed information about what functions are being instrumented.