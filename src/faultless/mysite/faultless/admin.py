from django.contrib import admin

from .models import Rules, Document, Trace

# Register your models here.
admin.site.register(Rules)
#admin.site.register(Document)
@admin.register(Document)
class Document(admin.ModelAdmin):
    fields = ("file", "path", "uploaded_at")
    readonly_fields = ("uploaded_at",)
admin.site.register(Trace)
