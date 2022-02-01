from django import template

from app_blogs.access import has_access


register = template.Library()

has_access = register.filter(has_access)