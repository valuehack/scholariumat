from django import template
from ..models import DonationLevel


register = template.Library()


@register.simple_tag
def necessary_level(amount):
    return DonationLevel.get_necessary_level(amount)
