from django.contrib import admin
from django.http import HttpResponseRedirect

from .models import Announcement


class PublishAdmin(admin.ModelAdmin):
    change_form_template = "admin/publish_changeform.html"

    def response_change(self, request, obj):
        if "_buffer-add" in request.POST:
            obj.buffer_publish()
            self.message_user(request, "Zu Buffer Queue hinzugefügt.")
            return HttpResponseRedirect(".")
        return super().response_change(request, obj)


admin.site.register(Announcement)
