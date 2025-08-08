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

from django.urls import path
from tests.test_app import views

urlpatterns = [
    path('function/', views.test_function_view, name='function_view'),
    path('class/', views.TestClassView.as_view(), name='class_view'),
    path('template/', views.TestTemplateView.as_view(), name='template_view'),
]