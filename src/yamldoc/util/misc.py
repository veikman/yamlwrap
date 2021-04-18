# -*- coding: utf-8 -*-
"""Miscellaneous utility functions."""

###########
# IMPORTS #
###########

import collections

import django.utils.html
import django.utils.text
import unidecode
from django.template.defaultfilters import slugify as default_slugify

#######################
# INTERFACE FUNCTIONS #
#######################


def is_listlike(object_):
    """Return True if object_ is an iterable container."""
    if (isinstance(object_, collections.abc.Iterable) and
            not isinstance(object_, str)):
        return True
    return False


def is_leaf_mapping(object_):
    """Return True if object_ is a mapping and doesn't contain mappings."""
    if (isinstance(object_, collections.abc.Mapping) and
            not any(map(is_leaf_mapping, object_.values()))):
        return True
    return False


def slugify(string):
    """Return a slug representing passed string."""
    clean = django.utils.html.strip_tags(str(string))
    if not clean:
        s = 'Failed to slugify "{}": Nothing left after HTML tags.'
        raise ValueError(s.format(string))

    # The following imitates django-taggit.
    slug = default_slugify(unidecode.unidecode(clean))

    if not slug:
        s = 'Failed to slugify "{}": Put in {}, got nothing back.'
        raise ValueError(s.format(string, clean))

    return slug