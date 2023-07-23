# -*- coding: utf-8 -*-
"""Unit tests for yamlwrap.

Some of these test cases originated when yamlwrap was pure Python. These now
serve mainly as characterization tests for the punwrap/runwrap upstream.

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

from pytest import mark
from yamlwrap import dump as dump_file
from yamlwrap import load as load_string
from yamlwrap import rewrap, unwrap, wrap


def _rewrap(w0, u0, width=3):
    w1 = wrap(w0, width)  # Wrap already-wrapped content.
    assert w0 == w1  # Else unstable (not idempotent) when wrapped.
    u1 = unwrap(w1)  # Unwrap wrapped content.
    assert u0 == u1  # Else product does not match unwrapped oracle.
    u2 = unwrap(u0)  # Unwrap already-unwrapped content.
    assert u0 == u2  # Else unstable (not idempotent) when unwrapped.
    w2 = wrap(u2, width)  # Wrap unwrapped content.
    assert w0 == w2  # Else product does not match wrapped oracle.
    r1 = rewrap(w0, width)  # Round trip.
    assert w0 == r1  # Else unstable in round trip only.


def test_trivial():
    wrapped = 'aa\nbb'
    no_wrap = 'aa bb'
    _rewrap(wrapped, no_wrap)


def test_softbreak():
    """Check that a Markdown soft break is preserved.

    Although this is supported, it is deprecated because of its secondary
    consequences for pyaml string styles.

    """
    dirty = 'aa  \naa'  # Markdown soft break.
    degenerate = 'aa   aa'  # Unwapping preserves the soft break’s spaces.
    clean = 'aa\naa'  # Wrapping destroys all trailing space.
    flat = 'aa aa'  # Soft break destroyed in a round trip.

    assert unwrap(dirty) == degenerate
    assert wrap(dirty) == clean
    assert unwrap(clean) == flat
    assert rewrap(dirty) == degenerate


def test_short_simple():
    wrapped = 'aa\nbb\n\ncc\n\n\ndd\n\nee'
    no_wrap = 'aa bb\n\ncc\n\n\ndd\n\nee'
    _rewrap(wrapped, no_wrap)


def test_enclosing_single_blanks():
    wrapped = '\naa\nbb\n\ncc\n'
    no_wrap = '\naa bb\n\ncc\n'
    _rewrap(wrapped, no_wrap)


def test_enclosing_double_blanks():
    wrapped = '\n\naa\nbb\n\ncc\n\n'
    no_wrap = '\n\naa bb\n\ncc\n\n'
    _rewrap(wrapped, no_wrap)


def test_width_ineffective():
    wrapped = 'a a\n\nb b b b\n\nc-c-c-c'
    no_wrap = 'a a\n\nb b b b\n\nc-c-c-c'
    _rewrap(wrapped, no_wrap, width=7)


def test_width_effective():
    wrapped = 'a a\n\nb b b\nb\n\nc-c-c-c'
    no_wrap = 'a a\n\nb b b b\n\nc-c-c-c'
    _rewrap(wrapped, no_wrap, width=6)


def test_block_html_minimal():
    wrapped = '<a>\n</a>'
    no_wrap = '<a>\n</a>'
    _rewrap(wrapped, no_wrap, width=5)


@mark.parametrize(
    'text,width',
    [
        (
            '<table>\n\n'
            '  <tr>\n\n'
            '    <td>The only\ndata</td>\n\n'
            '  </tr>\n\n'
            '</table>',
            15,
        ),
        (
            '<table>\n'
            '  <tr>\n'
            '    <td>The only data</td>\n'
            '  </tr>\n'
            '</table>\n',
            15,
        ),
        ('a a\n\n* b\n\nc c', 3),
        ('a a\n\n* b\nb\n\nc c', 3),
        ('a a\n\n* b b\n\nc c', 3),
        ('a a\n\n* b b\nb\n* b\n\nc c\n', 5),
        ('a a\n\n* b b\nb\n    * B\n* b\n\nc c\n', 5),
        # As in runwrap, only multi-paragraph list items are treated.
        (
            'a a\n'
            '\n'
            '* b b b b b b b b b b b b b\n'
            '* b\n'
            '    * B B\n'
            '      B\n'
            '        * bb\n'
            '          bb\n'
            '    * B B B B B\n'
            '        * bb bb bb\n'
            '        * bb\n'
            '            * BB\n'
            '\n'
            'c c\n',
            10,
        ),
    ],
)
def test_idempotent(text, width):
    _rewrap(text, text, width=width)


def test_inline_html():
    wrapped = 'a a a a a\n<b>a a</b>\na a a a a'
    no_wrap = 'a a a a a <b>a a</b> a a a a a'
    _rewrap(wrapped, no_wrap, width=10)


def test_numbered_list_trivial():
    wrapped = 'a a\n\n1. b\n\nc c'
    _rewrap(wrapped, wrapped, width=4)


def test_numbered_list_2digit():
    # Like the trivial case but with a two-digit line number.
    wrapped = 'a a\n\n29. b\n\nc c'
    _rewrap(wrapped, wrapped, width=5)


def test_numbered_list_indented_starting_long():
    # An indented trailing line as part of the first bullet point should
    # not be affected.
    wrapped = 'a a\n' '\n' '2. b b\n' '   b\n' '3. b\n' '\n' 'c c\n'
    _rewrap(wrapped, wrapped, width=6)
    _rewrap(wrapped, wrapped, width=60)


def test_numbered_list_indented_starting_short():
    # This is the workaround for the expected failure in
    # test_numbered_list_unindented_starting_short.
    wrapped = 'a a\n' '\n' '2. b\n' '3. b b\n' '   b\n' '\n' 'c c\n'
    _rewrap(wrapped, wrapped, width=6)
    _rewrap(wrapped, wrapped, width=60)


def test_mixed_list_singleparagraphs():
    wrapped = (
        'a a\n'
        '\n'
        '3. b b\n'
        '   b\n'
        '2. b\n'
        '   b\n'
        '    * B B\n'
        '    * B\n'
        '\n'
        'c c\n'
    )
    _rewrap(wrapped, wrapped, width=6)
    _rewrap(wrapped, wrapped, width=60)


def test_markup():
    wrapped = '{{mark|Aa a|param=Bb\nb}}\n\nCc c.'
    no_wrap = '{{mark|Aa a|param=Bb b}}\n\nCc c.'
    _rewrap(wrapped, no_wrap, width=20)


def test_asymmetric_single_space_leading_line():
    dirty = 'aa\n aa'  # Leading space.
    clean = 'aa\naa'  # Leading space destroyed.
    flat = 'aa aa'  # Line break destroyed (not space-constrained).

    assert unwrap(dirty) == flat
    assert wrap(dirty) == dirty
    assert unwrap(clean) == flat
    assert rewrap(dirty) == flat


def test_asymmetric_single_space_terminating_line():
    dirty = 'aa \naa'  # Trailing space.
    degenerate = 'aa  aa'  # Straight wrap preserves trailing space.
    clean = 'aa\naa'  # Trailing space destroyed.
    flat = 'aa aa'  # Line break destroyed (not space-constrained).

    assert unwrap(dirty) == degenerate
    assert wrap(dirty) == clean
    assert unwrap(clean) == flat
    assert rewrap(dirty) == degenerate


def test_asymmetric_dirty_multiline():
    wrapped = 'a a\na a a\na a a a'
    no_wrap = 'a a a a a a a a a'
    re_wrap = 'a a a a a a a\na a'
    actual = unwrap(wrapped)
    assert no_wrap == actual
    actual = wrap(actual, 13)
    assert re_wrap == actual


@mark.parametrize(
    '_, init, ref_final, ref_loaded, ref_reserialized',
    (
        [
            'middle',
            'key: |-\n  alpha \n  beta\n',
            'key: |-\n  alpha\n  beta\n',
            {'key': 'alpha \nbeta'},
            'key: "alpha \\nbeta"\n',
        ],
        [
            'end',
            'key: |-\n  alpha\n  beta \n',
            'key: |-\n  alpha\n  beta\n',
            {'key': 'alpha\nbeta '},
            'key: "alpha\\nbeta "\n',
        ],
        [
            'date',
            # This test case doesn’t really concern wrapping.
            # Instead, it’s about the data type of the key.
            '2021-08-15: skub',
            '2021-08-15: skub\n',
            {date(2021, 8, 15): 'skub'},
            '2021-08-15: skub\n',
        ],
    ),
)
def test_round_trip(_, init, ref_final, ref_loaded, ref_reserialized):
    """Check round-tripping loading and dumping.

    If the string 'key' is used in the data, check how rewrapping a single
    trailing space affects serialization. Once unwrapped and rewrapped, a
    string containing a single space before a newline should lose it, and this
    in turn should cause pyaml.dump to pick a string style that works well for
    long human-editable text.

    Losing that final space is a feature: It’s supposed to prevent disastrous
    reformatting over an errant space character that has no significance in
    e.g. Markdown.

    Extraneous leading spaces are not covered because the YAML parser treats
    them as inconsistent indentation, raising a ParserError (tested above).

    """
    loaded = load_string(init)
    assert loaded == ref_loaded
    assert dump_file(loaded) == ref_reserialized

    recomposed = ref_loaded
    if 'key' in ref_loaded:
        initial_value = loaded['key']
        # Rewrap at a width sufficient for one word only.
        rewrapped = wrap(unwrap(initial_value), 8)
        recomposed = dict(key=rewrapped)

    assert dump_file(recomposed) == ref_final
