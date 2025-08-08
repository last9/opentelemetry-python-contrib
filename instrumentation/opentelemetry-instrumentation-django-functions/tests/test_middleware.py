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


class TestMiddleware:
    """Test middleware for instrumentation testing"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        """Process the request"""
        response = self.get_response(request)
        return response
    
    def process_request(self, request):
        """Process request method"""
        request.test_middleware_processed = True
        return None
    
    def process_response(self, request, response):
        """Process response method"""
        response['X-Test-Middleware'] = 'processed'
        return response
    
    def process_exception(self, request, exception):
        """Process exception method"""
        return None
    
    def process_view(self, request, view_func, view_args, view_kwargs):
        """Process view method"""
        return None