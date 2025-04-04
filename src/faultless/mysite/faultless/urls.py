from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from .views import file_manager, get_response, get_rule, view_details

urlpatterns = [
    path("", file_manager, name="file_manager"),
    path("faultless/", get_rule, name="get_rule"),
    path("faultless/details", view_details, name="view_rules"),
    path("faultless/output", get_response, name="get_response"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
