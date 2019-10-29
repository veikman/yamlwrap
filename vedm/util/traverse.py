# -*- coding: utf-8 -*-
"""Utilities for traversing Django apps down to text fields."""

import logging

import django.apps
from django.conf import settings


def qualified_class_name(cls):
    """Return a string uniquely identifying a class (not cls.__qualname__).

    Produce the same name that __str__ on a type object does, without the
    "<class '...'>" wrapper.

    This function is meant as part of a workaround for the difficulty of
    importing all the classes into a Django settings module that should
    be banned from treatment for markup.

    """
    return cls.__module__ + "." + cls.__name__


def site(function):
    """Apply function to all apps on current site."""
    for app in django.apps.apps.all_models.values():
        function(app)


def app(function, app):
    """Apply function to all models in app.

    The app here is expected to be packaged as if by django.apps.

    """

    # Support explicit ordering.
    try:
        order = settings.MARKUP_MODEL_ORDER
    except AttributeError:
        order = ()

    def key(model):
        try:
            return order.index(model)
        except ValueError:
            # Not listed. Treat it early.
            return -1

    for model in sorted(app.values(), key=key):

        # Support a blacklist.
        # Not skipping superclasses would create trouble with Django's
        # handling of inheritance (through a OneToOne on the child class).
        try:
            blacklist = settings.MARKUP_MODEL_BLACKLIST
        except AttributeError:
            blacklist = {}

        if model in blacklist or qualified_class_name(model) in blacklist:
            logging.debug('Not traversing {}: Blacklisted.'.format(model))
            continue

        function(model)


def model(function, model, fields):
    """Apply function to each instance of passed model."""
    for instance in model.objects.all():
        function(instance, fields)


def instance(function, instance, fields, **kwargs):
    """Apply function to selected fields on passed instance of a model."""
    for field in fields:
        old = getattr(instance, field.name)
        new = function(instance, old, **kwargs)
        setattr(instance, field.name, new)
