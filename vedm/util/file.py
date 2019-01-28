# -*- coding: utf-8 -*-
'''Functions for text files of serialized data.

This module is concerned with the maintenance of text for use on Django sites:
In particular, with the maintenance of text files formatted with YAML and open
to programmatic manipulation (grep etc.).

This module could be expanded with customizations of the yaml/pyaml modules
to work around the fact that they avoid the desired '|' (literal) style for
scalars (strings) with words longer than a suitable line length. This is
particularly a problem when raw text records contain long URLs.

'''


###########
# IMPORTS #
###########


import collections
import difflib
import logging
import os
import re
import textwrap

import yaml  # PyPI: PyYAML.
import pyaml

from vedm.util import misc


#############
# CONSTANTS #
#############


# A custom wrapper adapted for reversibility.
# Also respects Markdown soft-break line endings ("  ").
_WRAPPER = textwrap.TextWrapper(break_long_words=False, break_on_hyphens=False)

# Identify a paragraph for some Markdown-like purposes.
_PARAGRAPH = re.compile(r'''
(                # Begin lead-in. This is group 1, just because
                 #   lookbehinds must have a fixed width, and we don't.
(?:^|\n)         # Option 1: Single break for what looks like HTML.
(\s*<)           # This part of option 1 is group 2, which overlaps group 1.
|
^                # Option 2: Start of record under other circumstances.
\n?              # An initial blank line will be respected.
|
\n\n             # Option 3: The normal case: A Markdown paragraph break.
|
\n(?=> .)        # Option 4: Markdown quoted paragraph beginning with "> ".
|
\n(?=>\n)        # Option 4: Empty line inside Markdown quote block.
)                # End lead-in.
(                # Begin paragraph contents. Group 3.
(?:              # Begin unnamed single-character subgroup.
(?(2)            # Begin conditional special treatment of HTML. This
                 #   conditional subgroup identifies a paragraph end.
(?!>(?:\n|$))    # HTML endings. A single break will suffice.
|
(?!\n\n|\n?$))   # Non-HTML endings require a double break.
.)+              # End and repeat unnamed single-character subgroup.
)                # End paragraph contents.
''', flags=re.VERBOSE)

# Identify a line break likely to have been introduced by automatic wrapping.
_WRAP_BREAK = re.compile(r'''
(?<=[^>\n ])     # Lead-in. A positive lookbehind assertion.
                 #   Any character but a ">" or a newline or a space.
                 #   Spaces are used in "  " soft break notation.
                 #   Ideally it'd be double space, but lookbehind is fixed.
((>)?)           # Groups 1 and 2. A possible ">".
\n               # The focal line break.
(?(2)(?!\s*<))   # If ">" ended the first line, and there's a "<" on the
                 #   next line (with only whitespace allowed in between),
                 #   take that to mean we're inside an HTML block, such
                 #   as a table. That would mean the focal break was not
                 #   created by wrappping, so do not match.
(?!>)            # Do not match inside quote blocks.
(?=.)            # Require some content on the following line.
''', flags=re.VERBOSE)

# Unicode space ranges.
_NONPRINTABLE = re.compile(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-'
                           r'\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')


#######################
# INTERFACE FUNCTIONS #
#######################


def find_files(root_folder, identifier=lambda _: True, single_file=None):
    '''Generate relative paths of asset files with prefix, under a folder.

    If a "single_file" argument is provided, it is assumed to be a relative
    path to a single file. This design is intended for ease of use with a
    CLI that takes both folder and file arguments.

    '''
    if single_file:
        if identifier(single_file):
            yield single_file
        return

    for dirpath, _, filenames in os.walk(root_folder):
        logging.debug('Searching for files in {}.'.format(dirpath))
        for f in filenames:
            if identifier(f):
                yield os.path.join(dirpath, f)


def dump(data, **kwargs):
    return pyaml.dump(data, **kwargs)


def load(filepath):
    """Load contents of named file and parse as YAML.

    The main job of this function is to work around the lack of support for
    SMP Unicode characters in PyYaml 3.13. A future release of PyYaml may fix
    this, and there are alternatives available which could take the place of
    PyYaml in this back end.

    """
    yaml.reader.Reader.NON_PRINTABLE = _NONPRINTABLE
    with open(filepath, mode='r', encoding='utf-8') as f:
        return yaml.load(f.read())


def transform(raw, model=None, order=True, unwrap=None, wrap=None, lint=None,
              arbitrary=None):
    '''Modify a serialized YAML string if needed.

    Return a string if changes are suggested, else return None.

    '''
    data = yaml.load(raw)

    dump_args = dict(width=160)
    if unwrap and not wrap:
        dump_args['string_val_style'] = '|'

    container_functions = list()
    if order:
        container_functions.append(order_raw_asset_dict)

    # Sort top-level data.
    if isinstance(data, collections.Mapping):
        for f in container_functions:
            data = f(model, data)

    string_functions = list()
    if unwrap:
        string_functions.append(unwrap_paragraphs)
    if wrap:
        string_functions.append(wrap_paragraphs)
    if lint:
        string_functions.append(paragraph_length_warning)

    if container_functions or string_functions:
        _descend(data, model, container_functions, string_functions)

    if arbitrary:
        arbitrary(data)

    cooked = dump(data, **dump_args)

    if raw == cooked:
        # File mtime is used as default time of last mod in some apps.
        # No real change to save in this case. Signalled with None.
        return

    return cooked


def paragraph_length_warning(string, threshold=1200):
    '''A lint function for use with _descend().'''

    for line in unwrap_paragraphs(string).split('\n'):
        if len(line) > threshold:
            s = 'Long paragraph begins "{}...".'
            logging.info(s.format(line[:50]))

    return string


def unwrap_paragraphs(string):
    '''A modifying function for use with _descend().

    Useful for Unix-style searching and batch processing.

    '''
    try:
        return re.sub(_WRAP_BREAK, r'\1 ', string)
    except TypeError:
        s = 'Unable to unwrap "{}".'
        logging.critical(s.format(repr(string)))
        raise


def wrap_paragraphs(string, width=None):
    '''A modifying function for use with _descend().

    Use a custom regex to identify paragraphs, passing these to a
    lightly customized TextWrapper.

    Useful for terminal reading, manual editing and neat re-dumping with
    pyaml. Words longer than pyaml's heuristic threshold will cause
    problems with dumping because they are exempt from wrapping.

    '''
    if width:  # Custom TextWrapper instances don't take keyword arguments.
        _WRAPPER.width = width
    else:
        _WRAPPER.width = 70

    return re.sub(_PARAGRAPH, _wrap, string)


def order_raw_asset_dict(model, mapping):
    '''A modifying function for use with _descend().

    Produce an ordered dictionary for replacement of a regular one.

    The passed dictionary should correspond to a model instance.
    The ordering is based on database schema and is meant to simplify
    human editing of e.g. YAML.

    The yaml module saves an OrderedDict as if it were a regular dict,
    but does respect its ordering, until it is loaded again.

    '''
    ordered = collections.OrderedDict()
    if model:
        for f in (f.name for f in model._meta.fields):
            if f in mapping:
                ordered[f] = mapping[f]
        for f in mapping:
            # Any metadata or raw data not named like database fields.
            if f not in ordered:
                ordered[f] = mapping[f]
    else:
        for f in sorted(mapping):
            ordered[f] = mapping[f]

    if 'tags' in ordered:
        # Sort alphabetically and remove duplicates.
        ordered['tags'] = sorted(set(ordered['tags']))

    return ordered


############
# INTERNAL #
############


def _descend(object_, model, container_functions, string_functions, **kwargs):
    '''Walk down through mutable containers, applying functions.'''

    if isinstance(object_, collections.Mapping):
        for key, value in object_.items():
            if isinstance(value, str):
                for f in string_functions:
                    object_[key] = f(object_[key], **kwargs)

                if value != object_[key] and len(string_functions) > 1:
                    _log_string_change(value, object_[key])

            _descend(object_[key], model, container_functions,
                     string_functions, **kwargs)

    elif misc.is_listlike(object_):
        for i, content in enumerate(object_):
            if isinstance(content, collections.Mapping):
                for f in container_functions:
                    object_[i] = f(model, object_[i])

            _descend(object_[i], model, container_functions, string_functions,
                     **kwargs)


def _log_string_change(old, new):
    d = difflib.unified_diff(old.splitlines(), new.splitlines(), n=1)
    for i, line in enumerate(d):
        if i > 1:
            logging.debug(line.strip())


def _wrap(matchobject):
    '''Wrap text in a found paragraph.

    Protect Markdown's awkward soft-break notation from the wrapper
    object by passing only part of the paragraph to it. This effect
    can apparently not be achieved by disabling "drop_whitespace".

    '''
    return ''.join((matchobject.group(1),
                    _WRAPPER.fill(matchobject.group(3)),
                    re.search(r'((  )?)$', matchobject.group(3)).group(1)))
