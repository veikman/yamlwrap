#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''A generic management command.'''


from django.db import transaction
from django.conf import settings

import vedm


class Command(vedm.management.misc.LoggingLevelCommand):
    help = 'Resolves all markup in text fields into HTML.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        super().handle(**kwargs)

        try:
            pass_instance = settings.MARKUP_INSTANCE_AS_SUBJECT
        except AttributeError:
            pass_instance = True

        field_classes = (vedm.models.MarkupField,)

        def treat_field(instance, string):
            '''Manipulate a string, which is the content of a text field.'''
            string = vedm.util.file.unwrap_paragraphs(string)

            kwargs = dict()
            if pass_instance:
                kwargs = dict(subject=instance)

            string = vedm.util.markup.all_on_string(string, **kwargs)
            return string

        def treat_model(model):
            fields = vedm.util.markup.get_fields(model, field_classes)

            def treat_instance(instance):
                vedm.util.traverse.instance(treat_field, instance, fields)
                instance.save()

            if fields:
                vedm.util.traverse.model(treat_instance, model)

        def treat_app(app):
            vedm.util.traverse.app(treat_model, app)

        vedm.util.traverse.site(treat_app)
