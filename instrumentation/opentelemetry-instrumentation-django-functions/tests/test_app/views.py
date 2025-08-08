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

from django.http import HttpResponse
from django.views import View
from django.views.generic import TemplateView


def test_function_view(request):
    """Test function-based view"""
    return HttpResponse("Function view response")


def _private_view(request):
    """Private view that should not be instrumented"""
    return HttpResponse("Private view")


class TestClassView(View):
    """Test class-based view"""
    
    def get(self, request):
        return HttpResponse("Class view GET response")
    
    def post(self, request):
        return HttpResponse("Class view POST response")


class TestTemplateView(TemplateView):
    """Test template-based view"""
    template_name = "test.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['message'] = 'Template view context'
        return context


class _PrivateClassView(View):
    """Private class view that should not be instrumented"""
    
    def get(self, request):
        return HttpResponse("Private class view")


# Non-view functions that should not be instrumented
def helper_function():
    """Helper function that's not a view"""
    return "helper result"


class NonViewClass:
    """Class that's not a view"""
    
    def some_method(self):
        return "non-view method"