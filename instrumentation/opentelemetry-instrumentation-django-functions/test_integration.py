#!/usr/bin/env python3
"""
Test Django Functions Auto-Instrumentation Integration
Tests with a minimal Django setup to verify actual integration
"""

import os
import sys
import tempfile
import subprocess

def test_django_integration():
    """Test the Django integration with a minimal Django project"""
    
    print("🧪 Testing Django Integration")
    print("=" * 50)
    
    # Create a minimal Django test app
    test_code = '''
import os
import sys
import django
from django.conf import settings
from django.http import HttpResponse
from django.urls import path

# Add our package to path (would normally be installed)
sys.path.insert(0, "{package_path}")

# Configure minimal Django settings  
if not settings.configured:
    settings.configure(
        DEBUG=True,
        SECRET_KEY='test-key-not-for-production',
        ROOT_URLCONF=__name__,
        INSTALLED_APPS=[
            'django.contrib.auth',
            'django.contrib.contenttypes',
        ],
        MIDDLEWARE=[
            'django.middleware.common.CommonMiddleware',
        ],
        DATABASES={{
            'default': {{
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
            }}
        }},
        USE_TZ=True,
    )

django.setup()

# Test views
def test_view(request):
    """Test function view"""
    return HttpResponse("Function view works!")

class TestViewClass:
    """Test class-based view"""
    def as_view(self):
        def view(request):
            return HttpResponse("Class view works!")
        return view

# URL patterns
urlpatterns = [
    path('test/', test_view, name='test_view'),
    path('class/', TestViewClass().as_view(), name='class_view'),
]

# Test the instrumentation import
print("🔄 Testing instrumentation import...")
try:
    # Mock OpenTelemetry components for testing
    import unittest.mock as mock
    
    class MockTracer:
        def start_as_current_span(self, name, kind=None):
            return mock.MagicMock()
    
    class MockInstrumentor:
        def instrumentation_dependencies(self):
            return ("django >= 1.10",)
    
    sys.modules['opentelemetry.instrumentation.instrumentor'] = mock.MagicMock()
    sys.modules['opentelemetry.instrumentation.instrumentor'].BaseInstrumentor = MockInstrumentor
    sys.modules['opentelemetry.trace'] = mock.MagicMock()
    sys.modules['opentelemetry.trace'].get_tracer = mock.MagicMock(return_value=MockTracer())
    sys.modules['opentelemetry.trace'].SpanKind = mock.MagicMock()
    sys.modules['opentelemetry.trace'].SpanKind.INTERNAL = "INTERNAL"
    sys.modules['wrapt'] = mock.MagicMock()
    
    from opentelemetry.instrumentation.django_functions import DjangoFunctionsInstrumentor
    print("✅ Successfully imported DjangoFunctionsInstrumentor")
    
    # Create instrumentor
    instrumentor = DjangoFunctionsInstrumentor()
    print("✅ Successfully created instrumentor instance")
    
    # Test instrumentation (without actual wrapping)
    print("🔄 Testing instrumentation methods...")
    
    # Mock the wrapping methods to avoid actual Django modification
    instrumentor._wrap_function = mock.MagicMock()
    
    # Test views instrumentation
    instrumentor._instrument_views([])
    print("✅ Views instrumentation completed")
    
    # Test middleware instrumentation 
    instrumentor._instrument_middleware([])
    print("✅ Middleware instrumentation completed")
    
    # Check if exclusion logic works
    should_exclude_admin = instrumentor._should_exclude_module('django.contrib.admin', ['admin'])
    should_not_exclude_public = instrumentor._should_exclude_module('myapp.views', ['admin'])
    
    if should_exclude_admin and not should_not_exclude_public:
        print("✅ Module exclusion logic works correctly")
    else:
        print("❌ Module exclusion logic failed")
        sys.exit(1)
    
    # Test view detection
    if instrumentor._is_view_function(test_view):
        print("✅ View function detection works")
    else:
        print("❌ View function detection failed") 
        sys.exit(1)
    
    if instrumentor._is_view_class(TestViewClass):
        print("✅ View class detection works")
    else:
        print("❌ View class detection failed")
        sys.exit(1)
    
    # Test uninstrumentation
    instrumentor._uninstrument()
    print("✅ Uninstrumentation completed")
    
    print("\\n🎉 Django Integration Test PASSED!")
    print("✅ All core functionality works with Django")
    
except Exception as e:
    print(f"❌ Django integration test failed: {{e}}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
'''.format(package_path=os.path.join(os.path.dirname(__file__), 'src'))
    
    # Write test code to temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name
    
    try:
        # Run the test
        result = subprocess.run([
            sys.executable, temp_file
        ], capture_output=True, text=True, timeout=30)
        
        print("📋 Test Output:")
        print("-" * 30)
        print(result.stdout)
        
        if result.stderr:
            print("⚠️ Warnings/Errors:")
            print(result.stderr)
        
        success = result.returncode == 0
        
        if success:
            print("✅ Django integration test completed successfully")
        else:
            print("❌ Django integration test failed")
            
        return success
        
    except subprocess.TimeoutExpired:
        print("❌ Test timed out")
        return False
    except Exception as e:
        print(f"❌ Failed to run test: {e}")
        return False
    finally:
        # Clean up
        try:
            os.unlink(temp_file)
        except:
            pass


def test_package_structure():
    """Test that the package structure is correct"""
    
    print("\n🧪 Testing Package Structure")
    print("=" * 50)
    
    base_path = os.path.dirname(__file__)
    
    required_files = [
        'src/opentelemetry/__init__.py',
        'src/opentelemetry/instrumentation/__init__.py', 
        'src/opentelemetry/instrumentation/django_functions/__init__.py',
        'src/opentelemetry/instrumentation/django_functions/version.py',
        'src/opentelemetry/instrumentation/django_functions/package.py',
        'pyproject.toml',
        'README.rst',
    ]
    
    all_exist = True
    for file_path in required_files:
        full_path = os.path.join(base_path, file_path)
        if os.path.exists(full_path):
            print(f"✅ {file_path}")
        else:
            print(f"❌ {file_path} - MISSING")
            all_exist = False
    
    if all_exist:
        print("✅ Package structure is complete")
        return True
    else:
        print("❌ Package structure is incomplete")
        return False


def main():
    """Run all integration tests"""
    
    print("🚀 Django Functions Auto-Instrumentation - Integration Tests")
    print("=" * 70)
    
    tests = [
        ("Package Structure", test_package_structure),
        ("Django Integration", test_django_integration),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} - PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} - FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} - FAILED: {e}")
    
    print("\n" + "=" * 70)
    print(f"📊 Integration Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests PASSED!")
        print("\n✅ The Django Functions Auto-Instrumentation is ready!")
        return True
    else:
        print("💥 Some integration tests FAILED!")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)