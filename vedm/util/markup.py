# -*- coding: utf-8 -*-
'''Collected utilities for registration and use of text markup.

The site-internal markup supported here is based on Ovid.

'''

import logging

import ovid
import markdown


###########
# CLASSES #
###########

# Registries for site-internal markup:


Inline = ovid.inspecting.SignatureShorthand

# A variant follows that will replace Markdown-generated HTML paragraph
# markup around its special delimiters.
# An HTML comment after the markup is allowed, but will be destroyed.
Paragraph = Inline.variant_class(lead_in='<p>{p{',
                                 lead_out='}p}(?: ?<!--.*?-->)?</p>')


#######################
# INTERFACE FUNCTIONS #
#######################


def get_fields(model, classes):
    '''Identify fields on passed model that may contain cookable markup.

    Interesting fields are found primarily through a "fields_with_markup"
    attribute, secondarily by class. The primary method is a workaround for
    the fact that Django does not support reclassing (replacing) fields
    inherited from third-party parent model classes with vedm's MarkupField.

    Return a tuple of field instances.

    '''

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
    '''Modify a string (e.g. text field content) based on internal markup.'''
    paragraph = Paragraph.collective_sub(raw, **kwargs)
    return Inline.collective_sub(paragraph, **kwargs)


def markdown_on_string(raw):
    '''Convert markdown to HTML with standardized extensions.

    This requires the raw input to be unwrapped already.

    '''
    extensions = ['markdown.extensions.footnotes',
                  'markdown.extensions.toc']
    return markdown.markdown(raw, extensions=extensions)
