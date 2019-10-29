# -*- coding: utf-8 -*-
"""Collected utilities for registration and use of text markup.

The site-internal markup supported here is based on Ovid.

"""

import logging
import os
import re

import django.conf

import ovid
import markdown

from . import misc


###########
# CLASSES #
###########

# Registries for site-internal markup:

# Multiline support here should be considered unstable. It may be expensive
# and works poorly with functions that only generate e.g. <span>, without
# taking paragraphs into account and duplicating the span across each.
Inline = ovid.inspecting.SignatureShorthand.variant_class(new_registry=False,
                                                          flags=re.DOTALL)


# A variant follows that will replace Markdown-generated HTML paragraph
# markup around its special delimiters.
# An HTML comment after the markup is allowed, but will be destroyed.
Paragraph = Inline.variant_class(lead_in='<p>{p{',
                                 lead_out='}p}(?: ?<!--.*?-->)?</p>')


#########################
# REPLACEMENT FUNCTIONS #
#########################

# Generic internal markup.


@Inline.register
def br(subject=None):
    """Return a line break.

    This is a workaround for the way that pyaml.dump interacts with
    lines in YAML that end with Markdown's soft break ("  ").

    The presence of any line terminated with a space provokes pyaml
    to choose a flow-styled scalar representation even when pyaml.dump
    is explicitly set to use the '|' block style. The result makes
    affected documents far harder to edit.

    """
    return '<br />'


@Inline.register
def media(path_fragment, subject=None, label=None, transclude=None):
    """Link to media."""
    if not label:
        label = path_fragment

    if transclude:
        # Produce the full contents of e.g. an SVG file. No label.
        filepath = os.path.join(django.conf.settings.MEDIA_ROOT,
                                path_fragment)
        try:
            with open(filepath, mode='r', encoding='utf-8') as f:
                repl = f.read()
        except UnicodeDecodeError:
            logging.error('Failed to read Unicode from {}.'.format(filepath))
            raise
    else:
        # Produce a link.
        root = django.conf.settings.MEDIA_URL
        href = root + path_fragment
        repl = '<a href="{}">{}</a>'.format(href, label)

    return repl


@Inline.register
def static(path_fragment, subject=None, label=None):
    """Link to a static file."""
    if not label:
        label = path_fragment

    # Produce a link.
    root = django.conf.settings.STATIC_URL
    href = root + path_fragment
    repl = '<a href="{}">{}</a>'.format(href, label)

    return repl


@Inline.register
def table_of_contents(subject=None, heading='Contents'):
    """Produce Markdown for a TOC with a heading that won't appear in it."""
    return '<h2 id="{s}">{h}</h2>\n[TOC]'.format(s=misc.slugify(heading),
                                                 h=heading)


#######################
# INTERFACE FUNCTIONS #
#######################


def get_fields(model, classes):
    """Identify fields on passed model that may contain cookable markup.

    Interesting fields are found primarily through a "fields_with_markup"
    attribute, secondarily by class. The primary method is a workaround for
    the fact that Django does not support reclassing (replacing) fields
    inherited from third-party parent model classes with vedm's MarkupField.

    Return a tuple of field instances.

    """
    try:
        fields = model.fields_with_markup
    except AttributeError:
        fields = model._meta.get_fields()
        fields = tuple(filter(lambda f: isinstance(f, classes), fields))

    if not fields:
        s = 'Unable to resolve markup on {}: No suitable fields.'
        logging.debug(s.format(model))

    return fields


def internal_on_string(raw, **kwargs):
    """Modify a string (e.g. text field content) based on internal markup.

    This will only be fully effective when it happens after Markdown has
    been resolved, due to the functioning of Paragraph.

    """
    paragraph = Paragraph.collective_sub(raw, **kwargs)
    inline = Inline.collective_sub(paragraph, **kwargs)
    return inline


def markdown_on_string(raw):
    """Convert markdown to HTML with standardized extensions.

    This requires the raw input to be unwrapped already.

    """
    extensions = ['markdown.extensions.footnotes',
                  'markdown.extensions.toc']
    return markdown.markdown(raw, extensions=extensions)


def all_on_string(string, **kwargs):
    """Resolve all markup in passed string.

    The order of operations here is intended for inline internal
    markup to be able to produce new Markdown, and for the resolution
    of Markdown to be able to produce the correct triggering pattern
    for internal paragraph markup.

    """
    string = Inline.collective_sub(string, **kwargs)
    string = markdown_on_string(string)
    string = Paragraph.collective_sub(string, **kwargs)
    return string
