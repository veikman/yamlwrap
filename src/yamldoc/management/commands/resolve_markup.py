#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""A generic management command for site-wide markup resolution.

Author: Viktor Eikman <viktor.eikman@gmail.com>

-------

This program is free software: you can redistribute it and/or modify it under
the terms of the GNU General Public License as published by the Free Software
Foundation, either version 3 of the License, or (at your option) any later
version.

This program is distributed in the hope that it will be useful, but WITHOUT ANY
WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
PARTICULAR PURPOSE. See the GNU General Public License for more details.

You should have received a copy of the GNU General Public License along with
this program. If not, see <https://www.gnu.org/licenses/>.

"""

from django.conf import settings
from django.db import transaction

from yamldoc.management.misc import LoggingLevelCommand
from yamldoc.models import MarkupField
from yamldoc.util.file import unwrap_paragraphs
from yamldoc.util.markup import all_on_string, get_fields
from yamldoc.util.traverse import app as traverse_app
from yamldoc.util.traverse import instance as traverse_instance
from yamldoc.util.traverse import model as traverse_model
from yamldoc.util.traverse import site as traverse_site


class Command(LoggingLevelCommand):
    """A command that is useful out of the box but can be customized."""

    help = ('Resolves all markup in special text fields into HTML, by the '
            'methods built into yamldoc.')

    @transaction.atomic
    def handle(self, *args, **kwargs):
        """Handle CLI command."""
        super().handle(**kwargs)
        traverse_site(self.treat_app)

    def treat_app(self, app):
        """Treat all models in passed app."""
        traverse_app(self.treat_model, app)

    def get_field_classes(self):
        """Return an iterable of subject field types."""
        return (MarkupField,)

    def treat_model(self, model):
        """Treat relevant fields on passed model."""
        if fields := get_fields(model, self.get_field_classes()):
            traverse_model(self.treat_instance, model, fields)

    def treat_instance(self, instance, fields):
        """Treat passed instance of a model."""
        traverse_instance(self.treat_field, instance, fields)
        instance.save()

    def treat_field(self, instance, string: str, treatment=all_on_string):
        """Manipulate a string, which is the content of a text field."""
        string = unwrap_paragraphs(string)

        try:
            pass_instance = settings.MARKUP_INSTANCE_AS_SUBJECT
        except AttributeError:
            pass_instance = True

        kwargs = dict()
        if pass_instance:
            kwargs.update(subject=instance)

        return treatment(string, **kwargs)
