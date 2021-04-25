# -*- coding: utf-8 -*-
"""All of yamlwrap’s library functionality.

This module could be expanded with customizations of the yaml/pyaml modules
to work around the fact that they avoid the desired '|' (literal) style for
scalars (strings) with words longer than a suitable line length. This is
particularly a problem when raw text records contain long URLs.

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


###########
# IMPORTS #
###########

import collections
import difflib
import re
from logging import getLogger
from textwrap import TextWrapper
from typing import Any, Callable, List, Optional

import pyaml
import yaml  # PyPI: PyYAML.

#############
# CONSTANTS #
#############


__version__ = '1.0.0'


# Identify a paragraph for some Markdown-like purposes.
_PARAGRAPH = re.compile(r"""
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
|                    For some reason, “\S” does not work in place of “.”.
\n(?=>\n)        # Option 5: Empty line inside Markdown quote block.
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
""", flags=re.VERBOSE)

# Identify a line break likely to have been introduced by automatic wrapping.
_WRAP_BREAK = re.compile(r"""
(?<=[^>\n ])     # Lead-in. A positive lookbehind assertion.
                 #   Any character but a ">" or a newline or a space.
                 #   Spaces are used in "  " soft break notation
                 #   as well as list item continuation. List notation does not
                 #   appear here because new list items are expected only with
                 #   trailing content.
((>)?)           # Groups 1 and 2. A possible ">".
\n               # The focal line break.
(?(2)(?!\s*<))   # If ">" ended the first line, and there's a "<" on the
                 #   next line (with only whitespace allowed in between),
                 #   take that to mean we're inside an HTML block, such
                 #   as a table. That would mean the focal break was not
                 #   created by wrappping, so do not match.
(?!              # Negative lookahead. Do not match inside lists or “>” blocks.
(?:              # Start options of different lengths for lookahead.
\*               # Do not match items in unnumbered lists.
|
\d\.             # Do not match items in numbered lists.
|
>                # Do not match in block quotes.
)                # End option section of lookahead, but not lookahead.
\s               # Require one space in all preceding options for lookahead.
)                # End lookahead for being inside lists or quote blocks.
(?=\S)           # Require some content on the following line.
""", flags=re.VERBOSE)

# Identify a soft break at the end of a line in e.g. Markdown.
_MARKDOWN_SOFTBREAK = re.compile(r'((  )?)$')

# Unicode space ranges.
_NONPRINTABLE = re.compile(r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-'
                           r'\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]')


###########
# OBJECTS #
###########


log = getLogger('yamlwrap')


#######################
# INTERFACE FUNCTIONS #
#######################


# Round out the yamlwrap API by exposing pyaml.dump as an interface.
# This could become a wrapper in a future version of yamlwrap.
dump = pyaml.dump


def load(data: str) -> str:
    """Parse passed string as YAML.

    The main job of this function is to work around the lack of support for
    SMP Unicode characters in PyYaml 3.13. A future release of PyYaml may fix
    this, and there are alternatives available which could take the place of
    PyYaml in this back end.

    """
    yaml.reader.Reader.NON_PRINTABLE = _NONPRINTABLE
    return yaml.safe_load(data)


def transform(raw: str, twopass=True, unwrap=False, wrap=False,
              lint_fn: Optional[Callable[[str], None]] = None,
              map_fn=lambda x: x, postdescent_fn=lambda x: x) -> Optional[str]:
    """Modify a serialized YAML string if needed.

    Return a string if changes are suggested, else return None.

    This is a crude high-level API that deserializes YAML, walks through an
    arbitrarily complex data structure inside, and round-trips back to
    serialized data. Not all options for lower-level functions conditionally
    called from here are exposed.

    """
    data = load(raw)

    dump_args = dict(width=160)
    if unwrap and not wrap:
        dump_args['string_val_style'] = '|'

    if isinstance(data, collections.abc.Mapping):
        data = map_fn(data)

    string_fns: List[Callable[[str], str]] = list()
    if unwrap and wrap and twopass:
        string_fns.append(_rewrap)
    else:
        if unwrap:
            string_fns.append(_unwrap)
        if wrap:
            string_fns.append(_wrap)

    if lint_fn is not None:
        def lint(r: str) -> str:
            lint_fn(r)
            return r
        string_fns.append(lint)

    _descend(data, map_fn, string_fns)

    postdescent_fn(data)

    cooked = dump(data, **dump_args)

    if raw == cooked:
        # File mtime is used as default time of last mod in some apps.
        # No real change to save in this case. Signalled with None.
        return None

    return cooked


def warn_on_long_paragraph(string: str, threshold=1200):
    """Inspect string for paragraphs that are impractically long.

    Markup resolvers and human readers both tend to perform at a
    worse-than-linear rate with longer strings of text.

    This is an example of a linter function, for use with _descend(), either by
    transform() or in a continuous-integration pipeline etc.

    """
    for line in unwrap(string).split('\n'):
        if len(line) > threshold:
            log.info(f'Long paragraph begins "{line[:50]}...".')


def unwrap(string: str) -> str:
    """Unwrap lines of text on a paragraph level in subject string."""
    try:
        return _WRAP_BREAK.sub(r'\1 ', string)
    except TypeError:
        log.critical(f'Unable to unwrap "{string!r}".')
        raise


def wrap(string: str,
         wrapper=TextWrapper(break_long_words=False, break_on_hyphens=False,
                             width=70)) -> str:
    """Wrap lines of text on a paragraph level in subject string.

    This function uses a regular expression to identify paragraphs, passing
    these to a TextWrapper adapted for reversibility.

    The function protects Markdown's soft-break notation from the wrapper
    object by passing only part of the paragraph to it. This effect
    can apparently not be achieved by disabling "drop_whitespace".

    Words longer than pyaml's heuristic threshold will cause
    problems with dumping because they are exempt from wrapping.

    """
    def replace(match: re.Match) -> str:
        lead, _, body = match.groups()
        return ''.join((lead, wrapper.fill(body),
                        _MARKDOWN_SOFTBREAK.search(body).group(1)))

    return _PARAGRAPH.sub(replace, string)


def rewrap(string: str, **kwargs):
    """Run a one- or two-pass combination of wrapping and unwrapping.

    A single pass is designed to be non-destructive of single trailing
    whitespace characters, but destroying such characters is beneficial
    where it preserves a VCS-friendly YAML string style.

    """
    new_string = _rewrap(string, **kwargs)
    if string == new_string:  # First pass had no impact. Skip second pass.
        return string
    return _rewrap(new_string, **kwargs)


############
# INTERNAL #
############


# Aliases defined for the benefit of transform, where user-friendly keyword
# arguments would otherwise be identical to the names of the functions aliased
# here.
_rewrap = rewrap
_unwrap = unwrap
_wrap = wrap


def _is_listlike(object_: Any) -> bool:
    """Return True if object_ is an iterable container."""
    if (isinstance(object_, collections.abc.Iterable) and
            not isinstance(object_, str)):
        return True
    return False


def _is_leaf_mapping(object_: Any) -> bool:
    """Return True if object_ is a mapping and doesn't contain mappings."""
    if (isinstance(object_, collections.abc.Mapping) and
            not any(map(_is_leaf_mapping, object_.values()))):
        return True
    return False


def _descend(object_: Any, map_fn, string_fns, **kwargs):
    """Walk down through mutable containers, applying functions."""
    if isinstance(object_, collections.abc.Mapping):
        for key, value in object_.items():
            if isinstance(value, str):
                for f in string_fns:
                    object_[key] = f(object_[key], **kwargs)

                if value != object_[key] and len(string_fns) > 1:
                    _log_string_change(value, object_[key])

            _descend(object_[key], map_fn, string_fns, **kwargs)

    elif _is_listlike(object_):
        for i, content in enumerate(object_):
            if isinstance(content, collections.abc.Mapping):
                object_[i] = map_fn(object_[i])

            _descend(object_[i], map_fn, string_fns, **kwargs)


def _log_string_change(old: str, new: str):
    d = difflib.unified_diff(old.splitlines(), new.splitlines(), n=1)
    for i, line in enumerate(d):
        if i > 1:
            log.debug(line.strip())


def _rewrap(string, **kwargs):
    """One full pass of unwrapping and wrapping."""
    return wrap(unwrap(string), **kwargs)
