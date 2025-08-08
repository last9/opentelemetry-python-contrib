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
Auto-instrumentation for Django functions and middleware as internal spans.

This instrumentation automatically wraps Django view functions, middleware methods,
and other Django framework functions to create internal spans for detailed tracing.

Usage
-----

.. code:: python

    from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor

    # Auto-instrument all Django functions
    DjangoFunctionsInstrumentor().instrument()

    # Or with specific configuration
    DjangoFunctionsInstrumentor().instrument(
        instrument_views=True,
        instrument_middleware=True,
        instrument_models=True,
        instrument_templates=True,
        excluded_modules=['myapp.sensitive_module']
    )

Configuration
-------------

instrument_views (bool): Whether to instrument Django view functions (default: True)
instrument_middleware (bool): Whether to instrument middleware methods (default: True)
instrument_models (bool): Whether to instrument Django model operations (default: False)
instrument_templates (bool): Whether to instrument template rendering (default: False)
excluded_modules (list): List of module patterns to exclude from instrumentation
"""

import inspect
import logging
from os import environ
from typing import Collection, Dict, Any, Callable, Optional, List
import importlib
import sys

try:
    import django
    from django.conf import settings
    from django.core.exceptions import ImproperlyConfigured
    from django.utils.module_loading import import_string
except ImportError:
    django = None

from opentelemetry.instrumentation.instrumentor import BaseInstrumentor
from opentelemetry.instrumentation.django_functions.package import _instruments
from opentelemetry.instrumentation.django_functions.version import __version__
from opentelemetry.trace import get_tracer, SpanKind
from wrapt import wrap_function_wrapper

_logger = logging.getLogger(__name__)

# Environment variable to control instrumentation
OTEL_PYTHON_DJANGO_FUNCTIONS_INSTRUMENT = "OTEL_PYTHON_DJANGO_FUNCTIONS_INSTRUMENT"

# Modules and functions to instrument by default
DEFAULT_VIEW_MODULES = [
    'django.views.generic',
    'django.contrib.admin.views',
    'django.contrib.auth.views',
]

DEFAULT_MIDDLEWARE_MODULES = [
    'django.middleware',
    'django.contrib',
]

DEFAULT_MODEL_MODULES = [
    'django.db.models',
]

DEFAULT_TEMPLATE_MODULES = [
    'django.template',
]


class DjangoFunctionsInstrumentor(BaseInstrumentor):
    """Instrumentor for Django functions and middleware"""

    def __init__(self):
        super().__init__()
        self._tracer = None
        self._original_functions = {}

    def instrumentation_dependencies(self) -> Collection[str]:
        return _instruments

    def _instrument(self, **kwargs):
        """Instrument Django functions and middleware"""
        if not django:
            _logger.warning("Django not found, skipping Django functions instrumentation")
            return

        if environ.get(OTEL_PYTHON_DJANGO_FUNCTIONS_INSTRUMENT, "").lower() == "false":
            return

        # Get configuration
        instrument_views = kwargs.get('instrument_views', True)
        instrument_middleware = kwargs.get('instrument_middleware', True)
        instrument_models = kwargs.get('instrument_models', False)
        instrument_templates = kwargs.get('instrument_templates', False)
        excluded_modules = kwargs.get('excluded_modules', [])

        tracer_provider = kwargs.get("tracer_provider")
        self._tracer = get_tracer(
            __name__,
            __version__,
            tracer_provider=tracer_provider,
        )

        # Instrument different Django components
        if instrument_views:
            self._instrument_views(excluded_modules)
        
        if instrument_middleware:
            self._instrument_middleware(excluded_modules)
        
        if instrument_models:
            self._instrument_models(excluded_modules)
        
        if instrument_templates:
            self._instrument_templates(excluded_modules)

    def _uninstrument(self, **kwargs):
        """Remove instrumentation from Django functions"""
        # Restore original functions
        for module_path, function_name in self._original_functions:
            try:
                module = importlib.import_module(module_path)
                if hasattr(module, function_name):
                    # Remove wrapt decoration
                    func = getattr(module, function_name)
                    if hasattr(func, '__wrapped__'):
                        setattr(module, function_name, func.__wrapped__)
            except Exception as e:
                _logger.debug(f"Failed to uninstrument {module_path}.{function_name}: {e}")
        
        self._original_functions.clear()

    def _should_exclude_module(self, module_name: str, excluded_modules: List[str]) -> bool:
        """Check if a module should be excluded from instrumentation"""
        for pattern in excluded_modules:
            if pattern in module_name:
                return True
        return False

    def _instrument_views(self, excluded_modules: List[str]):
        """Instrument Django view functions"""
        _logger.debug("Instrumenting Django views")
        
        # Instrument generic views
        self._instrument_module_functions(
            'django.views.generic.base',
            ['View.dispatch', 'TemplateView.get'],
            excluded_modules,
            'django.view'
        )
        
        # Instrument user-defined views by scanning installed apps
        self._instrument_app_views(excluded_modules)

    def _instrument_middleware(self, excluded_modules: List[str]):
        """Instrument Django middleware"""
        _logger.debug("Instrumenting Django middleware")
        
        # Get middleware from settings
        try:
            middleware_classes = getattr(settings, 'MIDDLEWARE', [])
            if not middleware_classes:
                middleware_classes = getattr(settings, 'MIDDLEWARE_CLASSES', [])
            
            for middleware_class in middleware_classes:
                if self._should_exclude_module(middleware_class, excluded_modules):
                    continue
                    
                try:
                    # Import middleware class
                    middleware = import_string(middleware_class)
                    module_name = middleware.__module__
                    class_name = middleware.__name__
                    
                    # Instrument common middleware methods
                    methods_to_instrument = [
                        'process_request',
                        'process_view',
                        'process_template_response',
                        'process_response',
                        'process_exception',
                        '__call__'
                    ]
                    
                    for method_name in methods_to_instrument:
                        if hasattr(middleware, method_name):
                            full_method_name = f"{class_name}.{method_name}"
                            self._wrap_function(
                                module_name,
                                full_method_name,
                                f"django.middleware.{class_name.lower()}.{method_name}"
                            )
                            
                except Exception as e:
                    _logger.debug(f"Failed to instrument middleware {middleware_class}: {e}")
                    
        except Exception as e:
            _logger.debug(f"Failed to get middleware classes: {e}")

    def _instrument_models(self, excluded_modules: List[str]):
        """Instrument Django model operations"""
        _logger.debug("Instrumenting Django models")
        
        # Instrument common model operations
        model_methods = [
            'django.db.models.Model.save',
            'django.db.models.Model.delete', 
            'django.db.models.QuerySet.filter',
            'django.db.models.QuerySet.get',
            'django.db.models.QuerySet.create',
            'django.db.models.QuerySet.update',
            'django.db.models.QuerySet.delete',
        ]
        
        for method_path in model_methods:
            module_path, method_name = method_path.rsplit('.', 1)
            if not self._should_exclude_module(module_path, excluded_modules):
                self._wrap_function(
                    module_path,
                    method_name,
                    f"django.model.{method_name}"
                )

    def _instrument_templates(self, excluded_modules: List[str]):
        """Instrument Django template rendering"""
        _logger.debug("Instrumenting Django templates")
        
        # Instrument template rendering
        template_methods = [
            'django.template.Template.render',
            'django.template.loader.get_template',
            'django.template.loader.render_to_string',
        ]
        
        for method_path in template_methods:
            module_path, method_name = method_path.rsplit('.', 1)
            if not self._should_exclude_module(module_path, excluded_modules):
                self._wrap_function(
                    module_path,
                    method_name,
                    f"django.template.{method_name}"
                )

    def _instrument_app_views(self, excluded_modules: List[str]):
        """Instrument views from installed Django apps"""
        try:
            from django.apps import apps
            
            # Ensure all apps are ready
            if not apps.ready:
                _logger.debug("Django apps not ready, deferring view instrumentation")
                return
            
            for app_config in apps.get_app_configs():
                app_name = app_config.name
                
                if self._should_exclude_module(app_name, excluded_modules):
                    continue
                
                try:
                    # Try to import views module from each app
                    views_module_name = f"{app_name}.views"
                    
                    # Check if module is already imported
                    if views_module_name in sys.modules:
                        views_module = sys.modules[views_module_name]
                    else:
                        # Try to import, but don't fail if it doesn't exist
                        try:
                            views_module = importlib.import_module(views_module_name)
                        except ImportError:
                            continue
                    
                    # Find view functions and classes
                    for name in dir(views_module):
                        if name.startswith('_'):
                            continue
                            
                        try:
                            obj = getattr(views_module, name)
                            if self._is_view_function(obj) or self._is_view_class(obj):
                                self._wrap_function(
                                    views_module_name,
                                    name,
                                    f"django.app_view.{app_name}.{name}"
                                )
                        except Exception as e:
                            _logger.debug(f"Failed to instrument {name} in {views_module_name}: {e}")
                            
                except Exception as e:
                    _logger.debug(f"Failed to process app {app_name}: {e}")
                    
        except Exception as e:
            _logger.debug(f"Failed to instrument app views: {e}")
            
        # Also try to instrument URL-discovered views
        self._instrument_url_views(excluded_modules)
    
    def _instrument_url_views(self, excluded_modules: List[str]):
        """Instrument views discovered through URL patterns"""
        try:
            from django.urls import get_resolver
            from django.urls.resolvers import URLPattern, URLResolver
            
            resolver = get_resolver()
            self._traverse_url_patterns(resolver.url_patterns, excluded_modules)
            
        except Exception as e:
            _logger.debug(f"Failed to instrument URL views: {e}")
    
    def _traverse_url_patterns(self, patterns, excluded_modules: List[str]):
        """Recursively traverse URL patterns to find views"""
        for pattern in patterns:
            if isinstance(pattern, URLPattern):
                # Found a view
                callback = pattern.callback
                if callback:
                    module_name = callback.__module__
                    function_name = callback.__name__
                    
                    if not self._should_exclude_module(module_name, excluded_modules):
                        try:
                            self._wrap_function(
                                module_name,
                                function_name,
                                f"django.url_view.{function_name}"
                            )
                        except Exception as e:
                            _logger.debug(f"Failed to instrument URL view {module_name}.{function_name}: {e}")
                            
            elif isinstance(pattern, URLResolver):
                # Recurse into included URLs
                try:
                    self._traverse_url_patterns(pattern.url_patterns, excluded_modules)
                except Exception as e:
                    _logger.debug(f"Failed to traverse URL resolver: {e}")

    def _is_view_function(self, obj) -> bool:
        """Check if object is a Django view function"""
        return (
            callable(obj) and 
            inspect.isfunction(obj) and
            not obj.__name__.startswith('_')
        )

    def _is_view_class(self, obj) -> bool:
        """Check if object is a Django view class"""
        return (
            inspect.isclass(obj) and
            not obj.__name__.startswith('_') and
            hasattr(obj, 'as_view')  # Django class-based views have as_view method
        )

    def _instrument_module_functions(self, module_path: str, function_names: List[str], 
                                   excluded_modules: List[str], span_prefix: str):
        """Instrument specific functions in a module"""
        if self._should_exclude_module(module_path, excluded_modules):
            return
            
        for func_name in function_names:
            self._wrap_function(module_path, func_name, f"{span_prefix}.{func_name}")

    def _wrap_function(self, module_path: str, function_name: str, span_name: str):
        """Wrap a specific function with OpenTelemetry tracing"""
        try:
            # Store original function reference for uninstrumentation
            self._original_functions[(module_path, function_name)] = True
            
            def _traced_wrapper(wrapped, instance, args, kwargs):
                """Wrapper function that creates spans for the wrapped function"""
                if not self._tracer:
                    return wrapped(*args, **kwargs)
                
                # Create span name from module and function
                full_span_name = span_name
                if instance is not None:
                    # For instance methods, include class name
                    class_name = instance.__class__.__name__
                    full_span_name = f"{span_name}.{class_name}"
                
                with self._tracer.start_as_current_span(
                    full_span_name,
                    kind=SpanKind.INTERNAL,
                ) as span:
                    # Add function attributes
                    if span.is_recording():
                        span.set_attribute("django.module", module_path)
                        span.set_attribute("django.function", function_name)
                        
                        # Add additional context for specific function types
                        if 'view' in span_name.lower():
                            span.set_attribute("django.component", "view")
                        elif 'middleware' in span_name.lower():
                            span.set_attribute("django.component", "middleware")
                        elif 'model' in span_name.lower():
                            span.set_attribute("django.component", "model")
                        elif 'template' in span_name.lower():
                            span.set_attribute("django.component", "template")
                    
                    try:
                        result = wrapped(*args, **kwargs)
                        return result
                    except Exception as e:
                        if span.is_recording():
                            span.record_exception(e)
                            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
                        raise
            
            # Apply the wrapper
            wrap_function_wrapper(module_path, function_name, _traced_wrapper)
            _logger.debug(f"Instrumented {module_path}.{function_name}")
            
        except Exception as e:
            _logger.debug(f"Failed to instrument {module_path}.{function_name}: {e}")


# Make the import work correctly
from opentelemetry import trace