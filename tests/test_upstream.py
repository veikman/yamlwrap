# -*- coding: utf-8 -*-
"""Characterization tests for the upstream, not for yamlwrap itself.

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

from datetime import date

from pytest import mark, raises
from yaml.parser import ParserError
from yamlwrap import dump as dump_file
from yamlwrap import load as load_string


def test_trivial():
    data = {'key': 'a'}
    ref = 'key: a\n'
    assert ref == dump_file(data)


def test_provoke_pipe():
    data = {'key': 'a\na'}
    ref = 'key: |-\n  a\n  a\n'
    assert ref == dump_file(data)


def test_failure_to_provoke_pipe_with_terminating_space():
    data = {'key': 'a \na'}
    ref = 'key: "a \\na"\n'
    assert ref == dump_file(data)


def test_loading_list_without_trailing_space():
    data = 'key:\n  - a\n'
    ref = {'key': ['a']}
    assert ref == load_string(data)


def test_loading_list_with_trailing_space():
    data = 'key: \n  - a\n'
    ref = {'key': ['a']}
    assert ref == load_string(data)


def test_loading_block_with_consistent_indentation():
    data = 'key: |-\n   a\n   a\n'
    ref = {'key': 'a\na'}
    assert ref == load_string(data)


def test_loading_block_without_consistent_indentation():
    data = 'key: |-\n   a\n  a\n'
    with raises(ParserError):
        load_string(data)


@mark.parametrize(
    '_, in_, out_',
    (
        ['date', date(2021, 8, 15), '2021-08-15\n'],
        ['datelike_string', '2021-08-15', "'2021-08-15'\n"],
        ['quoted_datelike_string', '"2021-08-15"', """'"2021-08-15"'\n"""],
        [
            '4byte_unicode',
            # Check that a 4-byte Unicode character isn’t encoded in hex. pyaml
            # should take care of this automatically, whereas PyYAML will not
            # do so by default.
            '🙄',
            '🙄\n',
        ],
    ),
)
def test_round_trip(_, in_, out_):
    assert out_ == dump_file(in_)
    assert load_string(out_) == in_


def test_4byte_unicode_with_pipe():
    """Check that a 4-byte Unicode character isn’t encoded in hex.

    Advanced case, with a newline.

    pyaml should take care of this automatically, whereas PyYAML will not
    do so by default.

    Historically, there have been several problems with this:

    The Debian 9 and 10 editions of PyYAML 3.13 came with libyaml, a C back
    end that behaved as expected by this test. However, installed from PyPI
    without libyaml, 3.13 failed this test, implying some problem in the
    libyaml-agnostic pyaml’s use of PyYAML’s internals or a bug in PyYAML.
    PyYAML v4 added extended Unicode support which seems to solve the
    problem even in the PyPI version, though as of 2019-01, v4 is not yet
    released.

    """
    s = '🧐\na'
    ref = '|-\n  🧐\n  a\n'
    assert ref == dump_file(s)
    assert load_string(ref) == s
