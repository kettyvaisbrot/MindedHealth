@register.filter
def dictlookup(obj, key):
    return getattr(obj, key)
