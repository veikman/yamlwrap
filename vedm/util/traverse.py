# -*- coding: utf-8 -*-
'''Utilities for traversing Django apps down to text fields.'''

import django.apps


def site(function):
    '''Apply function to all apps on current site.'''
    for app in django.apps.apps.all_models.values():
        function(app)


def app(function, app):
    '''Apply function to all models in app.

    The app here is expected to be packaged as if by django.apps.

    '''
    for model in app.values():
        function(model)


def model(function, model):
    '''Apply function to each instance of passed model.'''
    for instance in model.objects.all():
        function(instance)


def instance(function, instance, fields):
    '''Apply function to selected fields on passed instance of a model.'''
    for field in fields:
        old = getattr(instance, field.name)
        new = function(instance, old)
        setattr(instance, field.name, new)
