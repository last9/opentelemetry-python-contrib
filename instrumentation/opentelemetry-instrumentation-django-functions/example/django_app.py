#!/usr/bin/env python3
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
Example Django application demonstrating Django Functions Auto-Instrumentation

This example shows how to use the OpenTelemetry Django Functions instrumentation
to automatically trace all Django functions and middleware as internal spans.

Run with:
    python django_app.py
"""

import os
import sys
import django
from django.conf import settings
from django.core.management import execute_from_command_line
from django.http import HttpResponse, JsonResponse
from django.views import View
from django.views.generic import TemplateView
from django.urls import path
from django.core.wsgi import get_wsgi_application

# Configure Django settings
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='demo-secret-key-not-for-production',
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
            DemoMiddleware,  # Custom middleware to demonstrate instrumentation
        ],
        DATABASES={
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }
        },
        USE_TZ=True,
        TEMPLATES=[{
            'BACKEND': 'django.template.backends.django.DjangoTemplates',
            'OPTIONS': {
                'context_processors': [
                    'django.template.context_processors.debug',
                    'django.template.context_processors.request',
                ],
            },
        }],
    )

django.setup()

# OpenTelemetry setup
from opentelemetry import trace
from opentelemetry.exporter.console import ConsoleSpanExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.django import DjangoInstrumentor
from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor

# Configure tracing
trace.set_tracer_provider(TracerProvider())
tracer_provider = trace.get_tracer_provider()

# Use console exporter for demo (in production, use Jaeger, OTLP, etc.)
console_exporter = ConsoleSpanExporter()
span_processor = BatchSpanProcessor(console_exporter)
tracer_provider.add_span_processor(span_processor)

# Instrument Django (standard HTTP instrumentation)
DjangoInstrumentor().instrument()

# Instrument Django functions (our new auto-instrumentation)
DjangoFunctionsInstrumentor().instrument(
    instrument_views=True,           # Trace view functions
    instrument_middleware=True,      # Trace middleware methods
    instrument_models=False,         # Skip models for this demo
    instrument_templates=False,      # Skip templates for this demo
    excluded_modules=[],             # No exclusions for demo
)

print("🔍 Django Functions Auto-Instrumentation Demo")
print("=" * 50)
print("This demo shows internal spans created for:")
print("✓ View functions and class-based views")
print("✓ Middleware processing methods")
print("✓ Django framework functions")
print("\nMake requests to see the traces:")
print("• http://localhost:8000/hello/       - Simple function view")
print("• http://localhost:8000/api/data/    - Class-based view")
print("• http://localhost:8000/slow/        - View with slow operations")
print("• http://localhost:8000/error/       - View that raises exceptions")
print("=" * 50)
print()


# Custom middleware to demonstrate middleware instrumentation
class DemoMiddleware:
    """Demo middleware that will be automatically instrumented"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        print("📡 DemoMiddleware initialized")
    
    def __call__(self, request):
        print(f"📡 DemoMiddleware processing request to {request.path}")
        response = self.get_response(request)
        print(f"📡 DemoMiddleware processed response with status {response.status_code}")
        return response
    
    def process_request(self, request):
        """This method will create an internal span"""
        request.demo_start_time = time.time()
        return None
    
    def process_response(self, request, response):
        """This method will create an internal span"""
        if hasattr(request, 'demo_start_time'):
            duration = time.time() - request.demo_start_time
            response['X-Request-Duration'] = f"{duration:.3f}s"
        return response


# View functions to demonstrate view instrumentation
def hello_view(request):
    """Simple function view that will be automatically instrumented"""
    print("👋 Processing hello view")
    
    # Simulate some work
    import time
    time.sleep(0.1)
    
    return HttpResponse("Hello from instrumented Django view!")


def slow_view(request):
    """View with multiple slow operations to show detailed tracing"""
    print("🐌 Processing slow view with multiple operations")
    
    # Simulate database query
    simulate_db_query()
    
    # Simulate external API call
    simulate_api_call()
    
    # Simulate template rendering
    simulate_template_render()
    
    return JsonResponse({
        'message': 'Slow operations completed',
        'operations': ['db_query', 'api_call', 'template_render']
    })


def error_view(request):
    """View that raises an exception to demonstrate error tracing"""
    print("💥 Processing view that will raise an exception")
    
    # Simulate some work before error
    import time
    time.sleep(0.05)
    
    # This exception will be recorded in the span
    raise ValueError("Demo exception for tracing")


class DataApiView(View):
    """Class-based view that will be automatically instrumented"""
    
    def get(self, request):
        print("📊 Processing API data GET request")
        
        # Simulate data processing
        data = self.process_data()
        
        return JsonResponse({
            'data': data,
            'count': len(data),
            'method': 'GET'
        })
    
    def post(self, request):
        print("📊 Processing API data POST request")
        
        # Simulate data creation
        result = self.create_data()
        
        return JsonResponse({
            'created': result,
            'method': 'POST'
        })
    
    def process_data(self):
        """This method will create an internal span"""
        import time
        time.sleep(0.05)
        return ['item1', 'item2', 'item3']
    
    def create_data(self):
        """This method will create an internal span"""
        import time
        time.sleep(0.08)
        return {'id': 123, 'name': 'new_item'}


# Helper functions to simulate work (these will also be traced if they're Django-related)
def simulate_db_query():
    """Simulate a database query"""
    import time
    time.sleep(0.03)
    print("  🗄️ Simulated database query")


def simulate_api_call():
    """Simulate an external API call"""
    import time
    time.sleep(0.05)
    print("  🌐 Simulated external API call")


def simulate_template_render():
    """Simulate template rendering"""
    import time
    time.sleep(0.02)
    print("  📄 Simulated template rendering")


# URL configuration
urlpatterns = [
    path('hello/', hello_view, name='hello'),
    path('api/data/', DataApiView.as_view(), name='api_data'),
    path('slow/', slow_view, name='slow'),
    path('error/', error_view, name='error'),
]

# WSGI application
application = get_wsgi_application()

if __name__ == '__main__':
    import time
    
    # Fix middleware reference
    settings.MIDDLEWARE = [
        'django.middleware.common.CommonMiddleware',
        '__main__.DemoMiddleware',
    ]
    
    if len(sys.argv) > 1:
        # Run Django management commands
        execute_from_command_line(sys.argv)
    else:
        # Run development server
        print("\n🚀 Starting Django development server...")
        print("Press Ctrl+C to stop\n")
        
        try:
            from django.core.management.commands.runserver import Command
            command = Command()
            command.run_from_argv(['django_app.py', 'runserver', '8000'])
        except KeyboardInterrupt:
            print("\n👋 Server stopped")
            
            # Clean up instrumentation
            DjangoFunctionsInstrumentor()._uninstrument()
            DjangoInstrumentor()._uninstrument()
            print("✅ Instrumentation cleaned up")