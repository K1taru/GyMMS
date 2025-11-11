from django import template
from django.core.files.storage import default_storage
import os

register = template.Library()


@register.filter(name='photo_exists')
def photo_exists(photo_field):
    """
    Check if a photo file actually exists on disk
    Usage: {% if member.photo|photo_exists %}
    """
    if not photo_field:
        return False
    
    try:
        # Check if file exists in storage
        return default_storage.exists(photo_field.name)
    except Exception:
        return False
