# -*- coding: utf-8 -*-
"""Miscellaneous utility functions.

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

#######################
# INTERFACE FUNCTIONS #
#######################


def is_listlike(object_):
    """Return True if object_ is an iterable container."""
    if (isinstance(object_, collections.abc.Iterable) and
            not isinstance(object_, str)):
        return True
    return False


def is_leaf_mapping(object_):
    """Return True if object_ is a mapping and doesn't contain mappings."""
    if (isinstance(object_, collections.abc.Mapping) and
            not any(map(is_leaf_mapping, object_.values()))):
        return True
    return False
