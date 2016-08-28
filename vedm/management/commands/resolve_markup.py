#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''A generic management command.'''


from django.db import transaction
from django.conf import settings

import vedm


class Command(vedm.management.misc.LoggingLevelCommand):
    '''A command that is useful out of the box but can be customized.'''

    help = 'Resolves all markup in special text fields into HTML.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        super().handle(**kwargs)
        vedm.util.traverse.site(self.treat_app)

    def treat_app(self, app):
        vedm.util.traverse.app(self.treat_model, app)

    def get_field_classes(self):
        return (vedm.models.MarkupField,)

    def treat_model(self, model):
        fields = vedm.util.markup.get_fields(model, self.get_field_classes())

        def treat_instance(instance):
            vedm.util.traverse.instance(self.treat_field, instance, fields)
            instance.save()

        if fields:
            vedm.util.traverse.model(treat_instance, model)

    def treat_field(self, instance, string):
        '''Manipulate a string, which is the content of a text field.'''
        string = vedm.util.file.unwrap_paragraphs(string)

        kwargs = dict()

        try:
            pass_instance = settings.MARKUP_INSTANCE_AS_SUBJECT
        except AttributeError:
            pass_instance = True

        if pass_instance:
            kwargs = dict(subject=instance)

        string = vedm.util.markup.all_on_string(string, **kwargs)
        return string
