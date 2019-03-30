from django.db import models


class Announcement(models.Model):
    message = models.TextField(blank=False)

    def __str__(self):
        return self.message

    class Meta:
        verbose_name = 'Ankündigung'
        verbose_name_plural = "Ankündigungen"
