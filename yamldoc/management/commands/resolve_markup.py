#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""A generic management command."""


from django.conf import settings
from django.db import transaction

import yamldoc


class Command(yamldoc.management.misc.LoggingLevelCommand):
    """A command that is useful out of the box but can be customized."""

    help = 'Resolves all markup in special text fields into HTML.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        """Handle command."""
        super().handle(**kwargs)
        yamldoc.util.traverse.site(self.treat_app)

    def treat_app(self, app):
        """Treat all models in passed app."""
        yamldoc.util.traverse.app(self.treat_model, app)

    def get_field_classes(self):
        """Return an iterable of subject field types."""
        return (yamldoc.models.MarkupField,)

    def treat_model(self, model):
        """Treat relevant fields on passed model."""
        fields = yamldoc.util.markup.get_fields(model, self.get_field_classes())
        if fields:
            yamldoc.util.traverse.model(self.treat_instance, model, fields)

    def treat_instance(self, instance, fields):
        """Treat passed instance of a model."""
        yamldoc.util.traverse.instance(self.treat_field, instance, fields)
        instance.save()

    def treat_field(self, instance, string):
        """Manipulate a string, which is the content of a text field."""
        string = yamldoc.util.file.unwrap_paragraphs(string)

        try:
            pass_instance = settings.MARKUP_INSTANCE_AS_SUBJECT
        except AttributeError:
            pass_instance = True

        kwargs = dict()
        if pass_instance:
            kwargs.update(subject=instance)

        string = yamldoc.util.markup.all_on_string(string, **kwargs)
        return string