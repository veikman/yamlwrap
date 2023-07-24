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
from typing import Any, Callable, Dict, List, Optional, Union

import punwrap
import pyaml
import yaml  # PyPI: PyYAML.

#############
# CONSTANTS #
#############


__version__ = '2.1.1'


# Unicode space ranges.
_NONPRINTABLE = re.compile(
    r'[^\x09\x0A\x0D\x20-\x7E\x85\xA0-'
    r'\uD7FF\uE000-\uFFFD\U00010000-\U0010FFFF]'
)


WIDTH_DEFAULT = 70
WIDTH_DUMP = 160


###########
# OBJECTS #
###########


log = getLogger('yamlwrap')


#######################
# INTERFACE FUNCTIONS #
#######################


def dump(data, sort_keys=False, width=WIDTH_DUMP, **kwargs) -> str:
    """Serialize passed data structure as YAML.

    The main job of this function is to preserve the order of mappings for
    readability.

    """
    return pyaml.dump(data, sort_keys=sort_keys, width=width, **kwargs)


def load(data: str):
    """Parse passed string as YAML.

    The main job of this function is to work around the lack of support for
    SMP Unicode characters in PyYaml 3.13. A future release of PyYaml may fix
    this, and there are alternatives available which could take the place of
    PyYaml in this back end.

    """
    yaml.reader.Reader.NON_PRINTABLE = _NONPRINTABLE
    return yaml.safe_load(data)


def transform(
    raw: str,
    twopass=True,
    unwrap=False,
    wrap=False,
    loader=load,
    dumper=dump,
    lint_fn: Optional[Callable[[str], None]] = None,
    map_fn=lambda x: x,
    postdescent_fn=lambda x: x,
) -> Optional[str]:
    """Modify a serialized YAML string if needed.

    Return a string if changes are suggested, else return None.

    This is a crude high-level API that deserializes YAML, walks through an
    arbitrarily complex data structure inside, and round-trips back to
    serialized data. Not all options for lower-level functions conditionally
    called from here are exposed.

    The default loader and dumper used here are intended for backwards
    compatibility and are expected to change in a future major version of
    yamlwrap. They are parametrized in the function signature to allow for the
    use of e.g. yaml.load_all, closing over sort_keys=False, etc.

    """
    data = loader(raw)

    dump_args: Dict[str, Union[int, str, bool]] = {}
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
            lint_fn(r)  # type: ignore[misc]
            return r

        string_fns.append(lint)

    _descend(data, map_fn, string_fns)

    postdescent_fn(data)

    cooked = dumper(data, **dump_args)

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
    return punwrap.unwrap(string)


def wrap(string: str, width=WIDTH_DEFAULT) -> str:
    """Wrap lines of text on a paragraph level in subject string.

    Words longer than pyaml's heuristic threshold will cause
    problems with dumping because they are exempt from wrapping.

    """
    return punwrap.wrap(string, width)


def rewrap(string: str, width=WIDTH_DEFAULT):
    """Rewrap lines of text on a paragraph level in subject string."""
    return punwrap.rewrap(string, width)


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
    if isinstance(object_, collections.abc.Iterable) and not isinstance(
        object_, str
    ):
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
