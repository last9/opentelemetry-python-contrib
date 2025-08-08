#!/usr/bin/env python3
"""
Django Functions Auto-Instrumentation - Sample Spans Demo

This demo shows exactly what spans are created by the instrumentation
with realistic Django request examples.
"""

import json
from datetime import datetime, timezone
import uuid

def generate_sample_spans():
    """Generate sample spans showing what the instrumentation produces"""
    
    print("🔍 Django Functions Auto-Instrumentation - Sample Spans")
    print("=" * 70)
    print("These are the actual spans created for Django requests:\n")

    # Sample 1: Simple function-based view request
    print("📋 EXAMPLE 1: Simple Function-Based View Request")
    print("URL: GET /api/users/")
    print("View: myapp.views.list_users")
    print("-" * 50)
    
    sample_1_spans = [
        {
            "name": "GET /api/users/",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x1234567890abcdef",
                "trace_state": "[]"
            },
            "kind": "SpanKind.SERVER",
            "parent_id": None,
            "start_time": "2024-08-08T15:30:00.000000Z",
            "end_time": "2024-08-08T15:30:00.250000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "http.method": "GET",
                "http.url": "http://localhost:8000/api/users/",
                "http.route": "/api/users/",
                "http.status_code": 200,
                "http.user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            },
            "events": [],
            "links": [],
            "resource": {
                "service.name": "my-django-app",
                "service.version": "1.0.0"
            }
        }
    ]
    
    # Child spans created by Django Functions instrumentation
    child_spans = [
        {
            "name": "django.middleware.CommonMiddleware.process_request",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc", 
                "span_id": "0x2345678901bcdefg",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1234567890abcdef",
            "start_time": "2024-08-08T15:30:00.001000Z",
            "end_time": "2024-08-08T15:30:00.003000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.middleware.common",
                "django.function": "process_request",
                "django.component": "middleware"
            }
        },
        {
            "name": "django.middleware.AuthenticationMiddleware.process_request",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x3456789012cdefgh", 
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1234567890abcdef",
            "start_time": "2024-08-08T15:30:00.003000Z",
            "end_time": "2024-08-08T15:30:00.008000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.contrib.auth.middleware",
                "django.function": "process_request", 
                "django.component": "middleware"
            }
        },
        {
            "name": "django.app_view.myapp.list_users",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x456789013defghij",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL", 
            "parent_id": "0x1234567890abcdef",
            "start_time": "2024-08-08T15:30:00.010000Z",
            "end_time": "2024-08-08T15:30:00.180000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "myapp.views",
                "django.function": "list_users",
                "django.component": "view"
            }
        },
        {
            "name": "django.model.User.objects.all",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x56789014efghijkl",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x456789013defghij",  # Child of view span
            "start_time": "2024-08-08T15:30:00.015000Z", 
            "end_time": "2024-08-08T15:30:00.165000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.db.models.query",
                "django.function": "all",
                "django.component": "model"
            }
        },
        {
            "name": "django.middleware.AuthenticationMiddleware.process_response",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x6789015fghijklmn",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1234567890abcdef",
            "start_time": "2024-08-08T15:30:00.185000Z",
            "end_time": "2024-08-08T15:30:00.187000Z", 
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.contrib.auth.middleware",
                "django.function": "process_response",
                "django.component": "middleware"
            }
        },
        {
            "name": "django.middleware.CommonMiddleware.process_response",
            "context": {
                "trace_id": "0xfd720cffceba94bbf75940ff3caaf3cc",
                "span_id": "0x789016ghijklmno",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1234567890abcdef",
            "start_time": "2024-08-08T15:30:00.187000Z",
            "end_time": "2024-08-08T15:30:00.190000Z",
            "status": {"status_code": "UNSET"}, 
            "attributes": {
                "django.module": "django.middleware.common",
                "django.function": "process_response",
                "django.component": "middleware"
            }
        }
    ]
    
    print("🔥 ROOT SPAN (from standard Django instrumentation):")
    print(json.dumps(sample_1_spans[0], indent=2))
    
    print("\n🆕 INTERNAL SPANS (from Django Functions instrumentation):")
    for i, span in enumerate(child_spans, 1):
        print(f"\n📌 Internal Span {i}:")
        print(json.dumps(span, indent=2))
    
    # Sample 2: Class-based view with error
    print("\n" + "=" * 70)
    print("📋 EXAMPLE 2: Class-Based View with Error") 
    print("URL: POST /api/users/create/")
    print("View: myapp.views.UserCreateView.post")
    print("Result: Error occurred")
    print("-" * 50)
    
    error_spans = [
        {
            "name": "POST /api/users/create/",
            "context": {
                "trace_id": "0xae630bddcdb84c8af74850ee2caaedcc",
                "span_id": "0xabcdef1234567890",
                "trace_state": "[]"
            },
            "kind": "SpanKind.SERVER",
            "parent_id": None,
            "start_time": "2024-08-08T15:31:00.000000Z",
            "end_time": "2024-08-08T15:31:00.120000Z",
            "status": {"status_code": "ERROR", "description": "Internal Server Error"},
            "attributes": {
                "http.method": "POST",
                "http.url": "http://localhost:8000/api/users/create/", 
                "http.route": "/api/users/create/",
                "http.status_code": 500
            }
        }
    ]
    
    error_child_spans = [
        {
            "name": "django.app_view.myapp.UserCreateView.post",
            "context": {
                "trace_id": "0xae630bddcdb84c8af74850ee2caaedcc",
                "span_id": "0xbcdef12345678901", 
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0xabcdef1234567890",
            "start_time": "2024-08-08T15:31:00.010000Z",
            "end_time": "2024-08-08T15:31:00.095000Z", 
            "status": {"status_code": "ERROR", "description": "ValidationError: Invalid user data"},
            "attributes": {
                "django.module": "myapp.views", 
                "django.function": "post",
                "django.component": "view"
            },
            "events": [
                {
                    "name": "exception",
                    "timestamp": "2024-08-08T15:31:00.092000Z",
                    "attributes": {
                        "exception.type": "ValidationError",
                        "exception.message": "Invalid user data", 
                        "exception.stacktrace": "Traceback (most recent call last):\n  File \"myapp/views.py\", line 45, in post\n    user.save()\nValidationError: Invalid user data"
                    }
                }
            ]
        },
        {
            "name": "django.model.User.save",
            "context": {
                "trace_id": "0xae630bddcdb84c8af74850ee2caaedcc",
                "span_id": "0xcdef123456789012",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0xbcdef12345678901",  # Child of view span
            "start_time": "2024-08-08T15:31:00.050000Z",
            "end_time": "2024-08-08T15:31:00.092000Z",
            "status": {"status_code": "ERROR", "description": "ValidationError: Invalid user data"},
            "attributes": {
                "django.module": "myapp.models", 
                "django.function": "save",
                "django.component": "model"
            },
            "events": [
                {
                    "name": "exception", 
                    "timestamp": "2024-08-08T15:31:00.092000Z",
                    "attributes": {
                        "exception.type": "ValidationError",
                        "exception.message": "Invalid user data",
                        "exception.stacktrace": "Traceback (most recent call last):\n  File \"myapp/models.py\", line 23, in save\n    self.full_clean()\nValidationError: Invalid user data"
                    }
                }
            ]
        }
    ]
    
    print("🔥 ROOT SPAN:")
    print(json.dumps(error_spans[0], indent=2))
    
    print("\n💥 INTERNAL SPANS WITH ERROR:")
    for i, span in enumerate(error_child_spans, 1):
        print(f"\n📌 Internal Span {i}:")
        print(json.dumps(span, indent=2))

    # Sample 3: Complex view with multiple operations
    print("\n" + "=" * 70)
    print("📋 EXAMPLE 3: Complex View with Multiple Operations")
    print("URL: GET /dashboard/")
    print("View: dashboard.views.DashboardView.get") 
    print("Operations: Database queries, template rendering, cache operations")
    print("-" * 50)
    
    complex_child_spans = [
        {
            "name": "django.app_view.dashboard.DashboardView.get", 
            "context": {
                "trace_id": "0x1a2b3c4d5e6f7890abcdef1234567890",
                "span_id": "0x1111222233334444",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0xaaabbbcccdddeeee",
            "start_time": "2024-08-08T15:32:00.010000Z",
            "end_time": "2024-08-08T15:32:00.450000Z",
            "status": {"status_code": "UNSET"}, 
            "attributes": {
                "django.module": "dashboard.views",
                "django.function": "get", 
                "django.component": "view"
            }
        },
        {
            "name": "django.app_view.dashboard.DashboardView.get_context_data",
            "context": {
                "trace_id": "0x1a2b3c4d5e6f7890abcdef1234567890",
                "span_id": "0x2222333344445555", 
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1111222233334444",  # Child of main view
            "start_time": "2024-08-08T15:32:00.015000Z",
            "end_time": "2024-08-08T15:32:00.380000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "dashboard.views",
                "django.function": "get_context_data",
                "django.component": "view"
            }
        },
        {
            "name": "django.model.Order.objects.filter",
            "context": {
                "trace_id": "0x1a2b3c4d5e6f7890abcdef1234567890",
                "span_id": "0x3333444455556666",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL", 
            "parent_id": "0x2222333344445555",  # Child of get_context_data
            "start_time": "2024-08-08T15:32:00.020000Z",
            "end_time": "2024-08-08T15:32:00.120000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.db.models.query",
                "django.function": "filter",
                "django.component": "model"
            }
        },
        {
            "name": "django.model.User.objects.count", 
            "context": {
                "trace_id": "0x1a2b3c4d5e6f7890abcdef1234567890",
                "span_id": "0x4444555566667777",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x2222333344445555",  # Child of get_context_data
            "start_time": "2024-08-08T15:32:00.125000Z", 
            "end_time": "2024-08-08T15:32:00.180000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.db.models.query",
                "django.function": "count",
                "django.component": "model"
            }
        },
        {
            "name": "django.template.Template.render",
            "context": {
                "trace_id": "0x1a2b3c4d5e6f7890abcdef1234567890",
                "span_id": "0x5555666677778888",
                "trace_state": "[]"
            },
            "kind": "SpanKind.INTERNAL",
            "parent_id": "0x1111222233334444",  # Child of main view 
            "start_time": "2024-08-08T15:32:00.385000Z",
            "end_time": "2024-08-08T15:32:00.445000Z",
            "status": {"status_code": "UNSET"},
            "attributes": {
                "django.module": "django.template.base",
                "django.function": "render", 
                "django.component": "template"
            }
        }
    ]
    
    print("🆕 COMPLEX INTERNAL SPANS:")
    for i, span in enumerate(complex_child_spans, 1):
        print(f"\n📌 Internal Span {i}:")
        print(json.dumps(span, indent=2))

    # Summary
    print("\n" + "=" * 70)
    print("🎯 SPAN STRUCTURE SUMMARY")
    print("=" * 70)
    
    print("""
📊 SPAN HIERARCHY EXAMPLES:

Example 1 - Function View:
  🌐 GET /api/users/ (SERVER span - standard Django)
  ├── 🔧 django.middleware.CommonMiddleware.process_request (INTERNAL)
  ├── 🔧 django.middleware.AuthMiddleware.process_request (INTERNAL) 
  ├── 📱 django.app_view.myapp.list_users (INTERNAL)
  │   └── 🗄️ django.model.User.objects.all (INTERNAL)
  ├── 🔧 django.middleware.AuthMiddleware.process_response (INTERNAL)
  └── 🔧 django.middleware.CommonMiddleware.process_response (INTERNAL)

Example 2 - Class View with Error:
  🌐 POST /api/users/create/ (SERVER span - ERROR)
  └── 📱 django.app_view.myapp.UserCreateView.post (INTERNAL - ERROR)
      └── 🗄️ django.model.User.save (INTERNAL - ERROR with exception)

Example 3 - Complex View:
  🌐 GET /dashboard/ (SERVER span - standard Django)
  └── 📱 django.app_view.dashboard.DashboardView.get (INTERNAL)
      ├── 📱 django.app_view.dashboard.DashboardView.get_context_data (INTERNAL)
      │   ├── 🗄️ django.model.Order.objects.filter (INTERNAL)
      │   └── 🗄️ django.model.User.objects.count (INTERNAL)
      └── 📄 django.template.Template.render (INTERNAL)
""")
    
    print("🔍 SPAN ATTRIBUTES:")
    print("""
All internal spans include:
• django.module     - Python module containing the function
• django.function   - Function or method name  
• django.component  - Component type (view|middleware|model|template)

Additional context from parent SERVER span:
• http.method, http.url, http.route, http.status_code
• Custom request attributes (if configured)
• Trace context and correlation IDs
""")
    
    print("💡 BENEFITS:")
    print("""
✅ Complete visibility into Django request processing
✅ Identify slow views, middleware, or database operations
✅ Track errors to specific functions with full stack traces  
✅ Monitor middleware processing time and order
✅ Correlate frontend requests with backend processing
✅ Performance optimization insights
✅ Debugging and troubleshooting capabilities
""")

if __name__ == "__main__":
    generate_sample_spans()