from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import file_manager, get_rule, view_details, check_status, process_result, edit_rule

urlpatterns = [
    path("", file_manager, name="file_manager"),
    path("rule", get_rule, name="get_rule"),
    path('rule/edit/<int:rule_id>/', edit_rule, name='edit_rule'),
    path("details", view_details, name="view_details"),
    path("output", process_result, name="process_result"),
    path('loading/', check_status, name='check_status'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)