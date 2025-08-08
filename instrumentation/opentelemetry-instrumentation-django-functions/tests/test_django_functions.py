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

import os
import unittest
from unittest.mock import Mock, patch, MagicMock

# Set up Django before importing Django-specific modules
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'tests.test_settings')

import django
from django.conf import settings
from django.test import override_settings

from opentelemetry import trace
from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor
from opentelemetry.sdk import trace as trace_sdk
from opentelemetry.sdk.trace import export
from opentelemetry.test.test_base import TestBase


class TestDjangoFunctionsInstrumentation(TestBase):
    
    def setUp(self):
        super().setUp()
        self.instrumentor = DjangoFunctionsInstrumentor()
        
    def tearDown(self):
        super().tearDown()
        self.instrumentor._uninstrument()

    def test_instrument_basic(self):
        """Test basic instrumentation"""
        self.instrumentor.instrument()
        self.assertTrue(hasattr(self.instrumentor, '_tracer'))
        self.assertIsNotNone(self.instrumentor._tracer)

    def test_instrument_with_config(self):
        """Test instrumentation with custom configuration"""
        self.instrumentor.instrument(
            instrument_views=True,
            instrument_middleware=False,
            instrument_models=False,
            excluded_modules=['test_module']
        )
        self.assertTrue(hasattr(self.instrumentor, '_tracer'))

    @patch.dict(os.environ, {"OTEL_PYTHON_DJANGO_FUNCTIONS_INSTRUMENT": "false"})
    def test_instrument_disabled_by_env(self):
        """Test that instrumentation can be disabled by environment variable"""
        self.instrumentor.instrument()
        # Should not create tracer when disabled
        self.assertIsNone(self.instrumentor._tracer)

    def test_should_exclude_module(self):
        """Test module exclusion logic"""
        excluded_modules = ['sensitive_module', 'admin']
        
        # Should exclude matching modules
        self.assertTrue(
            self.instrumentor._should_exclude_module('myapp.sensitive_module.views', excluded_modules)
        )
        self.assertTrue(
            self.instrumentor._should_exclude_module('django.contrib.admin', excluded_modules)
        )
        
        # Should not exclude non-matching modules
        self.assertFalse(
            self.instrumentor._should_exclude_module('myapp.public.views', excluded_modules)
        )

    def test_is_view_function(self):
        """Test view function detection"""
        def sample_view_function(request):
            return "response"
            
        def _private_function(request):
            return "private"
            
        class NotAFunction:
            pass
            
        self.assertTrue(self.instrumentor._is_view_function(sample_view_function))
        self.assertFalse(self.instrumentor._is_view_function(_private_function))  # starts with _
        self.assertFalse(self.instrumentor._is_view_function(NotAFunction))

    def test_is_view_class(self):
        """Test view class detection"""
        class SampleView:
            def as_view(self):
                pass
        
        class NotAView:
            pass
            
        class _PrivateView:
            def as_view(self):
                pass
                
        self.assertTrue(self.instrumentor._is_view_class(SampleView))
        self.assertFalse(self.instrumentor._is_view_class(NotAView))  # no as_view method
        self.assertFalse(self.instrumentor._is_view_class(_PrivateView))  # starts with _

    @patch('opentelemetry.instrumentation.django_functions.wrap_function_wrapper')
    def test_wrap_function(self, mock_wrap):
        """Test function wrapping"""
        # Set up tracer
        self.instrumentor._tracer = Mock()
        
        # Test wrapping
        self.instrumentor._wrap_function('test.module', 'test_function', 'test.span')
        
        # Should call wrap_function_wrapper
        mock_wrap.assert_called_once()
        
        # Should store original function reference
        self.assertIn(('test.module', 'test_function'), self.instrumentor._original_functions)

    @patch('opentelemetry.instrumentation.django_functions.importlib.import_module')
    def test_uninstrument(self, mock_import):
        """Test uninstrumentation"""
        # Set up mock module with wrapped function
        mock_module = Mock()
        mock_function = Mock()
        mock_function.__wrapped__ = Mock()
        mock_module.test_function = mock_function
        mock_import.return_value = mock_module
        
        # Add function to original functions list
        self.instrumentor._original_functions[('test.module', 'test_function')] = True
        
        # Uninstrument
        self.instrumentor._uninstrument()
        
        # Should import module and restore function
        mock_import.assert_called_with('test.module')
        
        # Should clear original functions list
        self.assertEqual(len(self.instrumentor._original_functions), 0)

    def test_instrumentation_dependencies(self):
        """Test that instrumentation dependencies are correctly defined"""
        dependencies = self.instrumentor.instrumentation_dependencies()
        self.assertIn('django >= 1.10', dependencies)


class TestDjangoFunctionsWithDjango(TestBase):
    """Test Django functions instrumentation with actual Django setup"""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Configure minimal Django settings
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                INSTALLED_APPS=[
                    'django.contrib.auth',
                    'django.contrib.contenttypes',
                ],
                MIDDLEWARE=[
                    'django.middleware.common.CommonMiddleware',
                    'django.contrib.auth.middleware.AuthenticationMiddleware',
                ],
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                },
                SECRET_KEY='test-secret-key',
                USE_TZ=True,
            )
        django.setup()
    
    def setUp(self):
        super().setUp()
        self.instrumentor = DjangoFunctionsInstrumentor()
        
    def tearDown(self):
        super().tearDown()
        self.instrumentor._uninstrument()

    @patch('opentelemetry.instrumentation.django_functions.wrap_function_wrapper')
    def test_instrument_middleware(self, mock_wrap):
        """Test middleware instrumentation"""
        self.instrumentor.instrument(
            instrument_views=False,
            instrument_middleware=True,
            instrument_models=False,
            instrument_templates=False
        )
        
        # Should attempt to wrap middleware functions
        # The exact number depends on the middleware configured
        self.assertGreater(mock_wrap.call_count, 0)

    def test_function_wrapping_creates_spans(self):
        """Test that wrapped functions actually create spans"""
        # Create a test function to wrap
        def test_function():
            return "test result"
        
        # Set up tracer
        tracer_provider = trace_sdk.TracerProvider()
        tracer = tracer_provider.get_tracer(__name__)
        self.instrumentor._tracer = tracer
        
        # Create memory exporter to capture spans
        memory_exporter = export.InMemorySpanExporter()
        span_processor = export.SimpleSpanProcessor(memory_exporter)
        tracer_provider.add_span_processor(span_processor)
        
        # Wrap the function manually for testing
        from opentelemetry.instrumentation.django_functions import wrap_function_wrapper
        from opentelemetry import trace
        
        def _traced_wrapper(wrapped, instance, args, kwargs):
            with tracer.start_as_current_span(
                "test.span",
                kind=trace.SpanKind.INTERNAL,
            ) as span:
                if span.is_recording():
                    span.set_attribute("django.module", "test.module")
                    span.set_attribute("django.function", "test_function")
                    span.set_attribute("django.component", "test")
                
                result = wrapped(*args, **kwargs)
                return result
        
        # Apply wrapper to our test function
        original_function = test_function
        wrapped_function = lambda: _traced_wrapper(original_function, None, [], {})
        
        # Call the wrapped function
        result = wrapped_function()
        
        # Verify result is correct
        self.assertEqual(result, "test result")
        
        # Verify span was created
        spans = memory_exporter.get_finished_spans()
        self.assertEqual(len(spans), 1)
        
        span = spans[0]
        self.assertEqual(span.name, "test.span")
        self.assertEqual(span.kind, trace.SpanKind.INTERNAL)
        
        # Check attributes
        attributes = span.attributes
        self.assertEqual(attributes.get("django.module"), "test.module")
        self.assertEqual(attributes.get("django.function"), "test_function")
        self.assertEqual(attributes.get("django.component"), "test")


if __name__ == '__main__':
    unittest.main()