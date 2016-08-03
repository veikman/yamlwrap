# -*- coding: utf-8 -*-
'''Collected utilities for registration and use of site-internal markup.

Based on Ovid.

'''

from django.db import transaction
import ovid


Inline = ovid.inspecting.SignatureShorthand

# A variant follows that will replace Markdown-generated HTML paragraph
# markup around its special delimiters.
# An HTML comment after the markup is allowed, but will be destroyed.
Paragraph = Inline.variant_class(lead_in='<p>{p{',
                                 lead_out='}p}(?: ?<!--.*?-->)?</p>')


@transaction.atomic
def resolve_all(model):
    '''Resolve internal markup for an entire model.

    The model must have a "cooked" attribute listing applicable fields.

    '''
    for instance in model.objects.all():
        assert instance
        for field in model.cooked:
            old = getattr(instance, field.name)
            setattr(instance, field.name, resolve_string(old,
                                                         subject=instance))
        instance.save()


def resolve_string(raw, **kwargs):
    '''Modify a string (e.g. text field content) based on internal markup.'''
    p = Paragraph.collective_sub(raw, **kwargs)
    return Inline.collective_sub(p, **kwargs)
