from django.db import models


class LendingMixin(models.Model):
    """Profile Mixin for managing item lendings"""

    @property
    def lendings_active(self):
        """Returns currently active lendings (not returned)."""
        return self.lending_set.filter(shipped_isnull=False, returned__isnull=True)

    class Meta:
        abstract = True
