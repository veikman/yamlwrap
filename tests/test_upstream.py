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

from django.test import TestCase
from yaml.parser import ParserError

from yamlwrap import dump as dump_file
from yamlwrap import load as load_string


class _PrettyYAML(TestCase):
    """Tests of the third-party pyaml module itself for clarification."""

    def test_trivial(self):
        data = {'key': 'a'}
        ref = 'key: a\n'
        self.assertEqual(ref, dump_file(data))

    def test_provoke_pipe(self):
        data = {'key': 'a\na'}
        ref = 'key: |-\n  a\n  a\n'
        self.assertEqual(ref, dump_file(data))

    def test_failure_to_provoke_pipe_with_terminating_space(self):
        data = {'key': 'a \na'}
        ref = 'key: "a \\na"\n'
        self.assertEqual(ref, dump_file(data))

    def test_loading_list_without_trailing_space(self):
        data = 'key:\n  - a\n'
        ref = {'key': ['a']}
        self.assertEqual(ref, load_string(data))

    def test_loading_list_with_trailing_space(self):
        data = 'key: \n  - a\n'
        ref = {'key': ['a']}
        self.assertEqual(ref, load_string(data))

    def test_loading_block_with_consistent_indentation(self):
        data = 'key: |-\n   a\n   a\n'
        ref = {'key': 'a\na'}
        self.assertEqual(ref, load_string(data))

    def test_loading_block_without_consistent_indentation(self):
        data = 'key: |-\n   a\n  a\n'
        with self.assertRaises(ParserError):
            load_string(data)

    def test_4byte_unicode(self):
        """Check that a 4-byte Unicode character isn’t encoded in hex.

        pyaml should take care of this automatically, whereas PyYAML will not
        do so by default.

        """
        s = '🙄'
        ref = '🙄\n...\n'
        self.assertEqual(ref, dump_file(s))

    def test_4byte_unicode_with_pipe(self):
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
        self.assertEqual(ref, dump_file(s))
