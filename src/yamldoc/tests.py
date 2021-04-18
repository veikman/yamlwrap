# -*- coding: utf-8 -*-
"""App unit tests."""

from unittest import expectedFailure, mock

import django.template.defaultfilters
from django.core.management import call_command
from django.test import TestCase
from yaml.parser import ParserError

from yamldoc.models import Document, MarkupField
from yamldoc.util.file import dump as dump_file
from yamldoc.util.file import load as load_string
from yamldoc.util.file import (rewrap_paragraphs, transform, unwrap_paragraphs,
                               wrap_paragraphs)
from yamldoc.util.markup import Inline, get_fields, markdown_on_string
from yamldoc.util.misc import slugify


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


class _Models(TestCase):
    def test_document(self):
        fields = get_fields(Document, (MarkupField,))
        ref = (Document._meta.get_field('summary'),
               Document._meta.get_field('ingress'),
               Document._meta.get_field('body'))
        self.assertEqual(ref, fields)


class _Wrapping(TestCase):

    def _rewrap(self, w0, u0, width=3):
        self.maxDiff = None

        w1 = wrap_paragraphs(w0, width=width)
        self.assertEqual(w0, w1,
                         msg='Unstable when wrapped. '
                             'Wrapping the already-wrapped version (+) '
                             'did not produce the wrapped oracle (-).')
        u1 = unwrap_paragraphs(w1)
        self.assertEqual(u0, u1,
                         msg='Failed to unwrap. '
                             'Unwrapping the wrapped product (+) '
                             'did not produce the unwrapped oracle (-).')

        u2 = unwrap_paragraphs(u0)
        self.assertEqual(u0, u2,
                         msg='Unstable when unwrapped. '
                             'Unwrapping the already-unwrapped version (+) '
                             'did not produce the unwrapped oracle (-).')
        w2 = wrap_paragraphs(u2, width=width)
        self.assertEqual(w0, w2,
                         msg='Failed to wrap. '
                             'Rewrapping the unwrapped product (+) '
                             'did not produce the wrapped oracle (-).')

        r1 = rewrap_paragraphs(w0, width=width)
        self.assertEqual(w0, r1)  # Round trip.

    def test_trivial(self):
        wrapped = 'aa\nbb'
        no_wrap = 'aa bb'
        self._rewrap(wrapped, no_wrap)

    def test_softbreak(self):
        """Check that a Markdown soft break is preserved.

        Although this is supported, it is deprecated because of its secondary
        consequences for pyaml string styles. See yamldoc.util.markup.br.

        """
        wrapped = 'aa  \nbb'
        no_wrap = 'aa  \nbb'
        self._rewrap(wrapped, no_wrap, width=5)

    def test_short_simple(self):
        wrapped = 'aa\nbb\n\ncc\n\n\ndd\n\nee'
        no_wrap = 'aa bb\n\ncc\n\n\ndd\n\nee'
        self._rewrap(wrapped, no_wrap)

    def test_enclosing_single_blanks(self):
        wrapped = '\naa\nbb\n\ncc\n'
        no_wrap = '\naa bb\n\ncc\n'
        self._rewrap(wrapped, no_wrap)

    def test_enclosing_double_blanks(self):
        wrapped = '\n\naa\nbb\n\ncc\n\n'
        no_wrap = '\n\naa bb\n\ncc\n\n'
        self._rewrap(wrapped, no_wrap)

    def test_width_ineffective(self):
        wrapped = 'a a\n\nb b b b\n\nc-c-c-c'
        no_wrap = 'a a\n\nb b b b\n\nc-c-c-c'
        self._rewrap(wrapped, no_wrap, width=7)

    def test_width_effective(self):
        wrapped = 'a a\n\nb b b\nb\n\nc-c-c-c'
        no_wrap = 'a a\n\nb b b b\n\nc-c-c-c'
        self._rewrap(wrapped, no_wrap, width=6)

    def test_block_html_minimal(self):
        wrapped = '<a>\n</a>'
        no_wrap = '<a>\n</a>'
        self._rewrap(wrapped, no_wrap, width=5)

    def test_block_html_uncondensed(self):
        wrapped = ('<table>\n\n'
                   '  <tr>\n\n'
                   '    <td>The only\ndata</td>\n\n'
                   '  </tr>\n\n'
                   '</table>')
        no_wrap = ('<table>\n\n'
                   '  <tr>\n\n'
                   '    <td>The only data</td>\n\n'
                   '  </tr>\n\n'
                   '</table>')
        self._rewrap(wrapped, no_wrap, width=15)

    def test_block_html_compact(self):
        wrapped = ('<table>\n'
                   '  <tr>\n'
                   '    <td>The only\ndata</td>\n'
                   '  </tr>\n'
                   '</table>\n')
        no_wrap = ('<table>\n'
                   '  <tr>\n'
                   '    <td>The only data</td>\n'
                   '  </tr>\n'
                   '</table>\n')
        self._rewrap(wrapped, no_wrap, width=15)

    def test_inline_html(self):
        wrapped = ('a a a a a\n<b>a a</b>\na a a a a')
        no_wrap = ('a a a a a <b>a a</b> a a a a a')
        self._rewrap(wrapped, no_wrap, width=10)

    def test_bullet_trivial(self):
        wrapped = ('a a\n\n* b\n\nc c')
        self._rewrap(wrapped, wrapped)

    def test_bullet_single(self):
        wrapped = ('a a\n\n* b\nb\n\nc c')
        no_wrap = ('a a\n\n* b b\n\nc c')
        self._rewrap(wrapped, no_wrap)

    def test_bullet_unindented(self):
        wrapped = ('a a\n'
                   '\n'
                   '* b b\n'
                   'b\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '* b b b\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_bullet_indented_simple(self):
        wrapped = ('a a\n'
                   '\n'
                   '* b b\n'
                   'b\n'
                   '    * B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '* b b b\n'
                   '    * B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_bullet_indented_no_manual_wrap(self):
        # Here, an indented item exceeds the wrapping width and is ignored.
        wrapped = ('a a\n'
                   '\n'
                   '* b b\n'
                   'b\n'
                   '    * B B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '* b b b\n'
                   '    * B B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_bullet_indented_manual_wrap_short(self):
        wrapped = ('a a\n'
                   '\n'
                   '* b b\n'
                   'b\n'
                   '    * B\n'
                   '      B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '* b b b\n'
                   '    * B\n'
                   '      B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_bullet_indented_manual_wrap_long(self):
        # Three lines instead of the two in the preceding case.
        wrapped = ('a a\n'
                   '\n'
                   '* b b\n'
                   'b\n'
                   '    * B\n'
                   '      B\n'
                   '      B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '* b b b\n'
                   '    * B\n'
                   '      B\n'
                   '      B\n'
                   '* b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_bullet_deeply_indented(self):
        # Again, intended items are ignored.
        wrapped = ('a a\n'
                   '\n'
                   '* b b b b b b\n'
                   'b b b b b b b\n'
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
                   'c c\n')
        no_wrap = ('a a\n'
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
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=13)

    def test_numbered_list_trivial(self):
        wrapped = ('a a\n\n1. b\n\nc c')
        self._rewrap(wrapped, wrapped, width=4)

    def test_numbered_list_width(self):
        # At default width for this unit test, break even the simplest
        # possible numbered list.
        wrapped = ('a a\n\n1.\nb\n\nc c')
        no_wrap = ('a a\n\n1. b\n\nc c')
        self._rewrap(wrapped, no_wrap)

    def test_numbered_list_2digit(self):
        # Like the trivial case but with a two-digit line number.
        wrapped = ('a a\n\n29. b\n\nc c')
        self._rewrap(wrapped, wrapped, width=5)

    def test_numbered_list_single_line(self):
        wrapped = ('a a\n\n1. b\nb\n\nc c')
        no_wrap = ('a a\n\n1. b b\n\nc c')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_numbered_list_unindented_starting_long(self):
        wrapped = ('a a\n'
                   '\n'
                   '2. b b\n'
                   'b\n'
                   '3. b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '2. b b b\n'
                   '3. b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=6)

    @expectedFailure
    def test_numbered_list_unindented_starting_short(self):
        wrapped = ('a a\n'
                   '\n'
                   '2. b\n'
                   '3. b b\n'
                   'b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '2. b\n'
                   '3. b b b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=6)

        # NOTE: As of 2020-08, the last wrap on item 3 is identified as
        # purposeful and is not undone. This is arguably bad behaviour;
        # see below for the supported workaround.

    def test_numbered_list_indented_starting_long(self):
        # An indented trailing line as part of the first bullet point should
        # not be affected.
        wrapped = ('a a\n'
                   '\n'
                   '2. b b\n'
                   '   b\n'
                   '3. b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, wrapped, width=6)
        self._rewrap(wrapped, wrapped, width=60)

    def test_numbered_list_indented_starting_short(self):
        # This is the workaround for the expected failure in
        # test_numbered_list_unindented_starting_short.
        wrapped = ('a a\n'
                   '\n'
                   '2. b\n'
                   '3. b b\n'
                   '   b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, wrapped, width=6)
        self._rewrap(wrapped, wrapped, width=60)

    def test_numbered_list_indented(self):
        # Here, the indented line is not broken up.
        # Nested lists currently require manual wrapping.
        wrapped = ('a a\n'
                   '\n'
                   '2. b b b b\n'
                   'b\n'
                   '    1. B B B\n'
                   '3. b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '2. b b b b b\n'
                   '    1. B B B\n'
                   '3. b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=10)

    def test_mixed_list(self):
        wrapped = ('a a\n'
                   '\n'
                   '3. b b\n'
                   '   b\n'
                   '2. b\n'
                   '   b\n'
                   '    * B B\n'
                   '    * B\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '3. b b\n'
                   '   b\n'
                   '2. b\n'
                   '   b\n'
                   '    * B B\n'
                   '    * B\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=7)

    def test_quote_block_oneparagraph(self):
        wrapped = ('a a\n\n> b\nb\n\nc c')
        no_wrap = ('a a\n\n> b b\n\nc c')
        self._rewrap(wrapped, no_wrap)

    def test_quote_block_multiparagraph_starting_long(self):
        wrapped = ('a a\n'
                   '\n'
                   '> b b\n'
                   'b\n'
                   '>\n'
                   '> b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '> b b b\n'
                   '>\n'
                   '> b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_quote_block_multiparagraph_starting_short(self):
        wrapped = ('a a\n'
                   '\n'
                   '> b b\n'
                   '>\n'
                   '> b b\n'
                   'b\n'
                   '\n'
                   'c c\n')
        no_wrap = ('a a\n'
                   '\n'
                   '> b b\n'
                   '>\n'
                   '> b b b\n'
                   '\n'
                   'c c\n')
        self._rewrap(wrapped, no_wrap, width=5)

    def test_markup(self):
        wrapped = ('{{mark|Aa a|param=Bb\nb}}\n\nCc c.')
        no_wrap = ('{{mark|Aa a|param=Bb b}}\n\nCc c.')
        self._rewrap(wrapped, no_wrap, width=20)

    def test_asymmetric_single_space_terminating_line(self):
        dirty = 'aa \naa'  # Trailing space, respected by unwrapper only!
        clean = 'aa\naa'   # Trailing space destroyed.
        flat = 'aa aa'     # Line break destroyed (not space-constrained).

        self.assertEqual(dirty, unwrap_paragraphs(dirty))
        self.assertEqual(clean, wrap_paragraphs(dirty))
        self.assertEqual(flat, unwrap_paragraphs(clean))
        self.assertEqual(flat, rewrap_paragraphs(dirty))

    def test_asymmetric_dirty_multiline(self):
        wrapped = 'a a\na a a\na a a a'
        no_wrap = 'a a a a a a a a a'
        re_wrap = 'a a a a a a a\na a'
        actual = unwrap_paragraphs(wrapped)
        self.assertEqual(no_wrap, actual)
        actual = wrap_paragraphs(actual, width=13)
        self.assertEqual(re_wrap, actual)


class _BlockStyleVersusRewrap(TestCase):
    """Check how rewrapping a single trailing space affects serialization.

    Once unwrapped and rewrapped, a string containing a single space before a
    newline should lose it, and this in turn should cause pyaml.dump to pick a
    string style that works well for long human-editable text.

    This is a feature: It’s supposed to prevent disastrous reformatting
    over an errant space character that has no significance in Markdown.

    Extraneous leading spaces are not covered because the YAML parser treats
    them as inconsistent indentation, raising a ParserError (tested above).

    """

    def _round_trip(self, init, ref_final, ref_loaded, ref_reserialized):
        loaded = load_string(init)
        self.assertEqual(loaded, ref_loaded)
        self.assertEqual(dump_file(loaded), ref_reserialized)
        initial_value = loaded['key']
        rewrapped = wrap_paragraphs(unwrap_paragraphs(initial_value),
                                    width=8)  # Enough for one word only.
        recomposed = dict(key=rewrapped)
        self.assertEqual(dump_file(recomposed), ref_final)

    def test_middle(self):
        self._round_trip('key: |-\n  alpha \n  beta\n',
                         'key: |-\n  alpha\n  beta\n',
                         {'key': 'alpha \nbeta'},
                         'key: "alpha \\nbeta"\n')

    def test_end(self):
        self._round_trip('key: |-\n  alpha\n  beta \n',
                         'key: |-\n  alpha\n  beta\n',
                         {'key': 'alpha\nbeta '},
                         'key: "alpha\\nbeta "\n')


class _CookingMarkdown(TestCase):

    def test_two_single_line_paragraphs(self):
        s = 'Line 1.\n\nLine 2.'
        ref = '<p>Line 1.</p>\n<p>Line 2.</p>'
        self.assertEqual(ref, markdown_on_string(s))

    def test_minor_indentation_is_ignored(self):
        # This is normal behaviour for Python's markdown.
        # Not a consequence of the site's paragraph wrapping/unwrapping.
        s = 'Line 1.\n\n  Line 2.'
        ref = '<p>Line 1.</p>\n<p>Line 2.</p>'
        self.assertEqual(ref, markdown_on_string(s))

    def test_major_indentation_is_noted(self):
        s = 'Line 1.\n\n    Line 2.'
        ref = ('<p>Line 1.</p>\n'
               '<pre><code>Line 2.\n</code></pre>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_flat_sparse_bullet_list(self):
        s = ('* Bullet A.\n'
             '\n'
             '* Bullet B.')
        ref = ('<ul>\n'
               '<li>\n'
               '<p>Bullet A.</p>\n'
               '</li>\n'
               '<li>\n'
               '<p>Bullet B.</p>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_flat_dense_bullet_list(self):
        s = ('* Bullet A.\n'
             '* Bullet B.')
        ref = ('<ul>\n'
               '<li>Bullet A.</li>\n'
               '<li>Bullet B.</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_nested_sparse_bullet_list(self):
        # As with <pre> above, this needs four spaces of indentation.
        s = ('* Bullet Aa.\n'
             '\n'
             '    * Bullet Ab.')
        ref = ('<ul>\n'
               '<li>\n'
               '<p>Bullet Aa.</p>\n'
               '<ul>\n'
               '<li>Bullet Ab.</li>\n'
               '</ul>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))

    def test_nested_dense_bullet_list(self):
        s = ('* Bullet A.\n'
             '    * Bullet B.')
        ref = ('<ul>\n'
               '<li>Bullet A.<ul>\n'
               '<li>Bullet B.</li>\n'
               '</ul>\n'
               '</li>\n'
               '</ul>')
        self.assertEqual(ref, markdown_on_string(s))


class _CookingInternalMarkup(TestCase):

    def test_multiline(self):
        def mask(s):
            return s

        Inline(mask)

        s0 = """Uh {{mask|huh.

        Nu}} uh."""
        s1 = """Uh huh.

        Nu uh."""
        self.assertEqual(Inline.collective_sub(s0), s1)


class _CookingStructure(TestCase):

    def test_sort_single_object_without_model(self):
        o = ("b: 2\n"
             "a: 1")
        ref = ("a: 1\n"
               "b: 2\n")
        self.assertEqual(ref, transform(o))

    def test_sort_list(self):
        o = ("- b: 2\n"
             "  a: 1\n"
             "- c: 3\n")
        ref = ("- a: 1\n"
               "  b: 2\n"
               "- c: 3\n")
        self.assertEqual(ref, transform(o))


class _CookingSite(TestCase):

    def test_chain(self):
        raws = dict(title='Cove, Oregon',
                    body='**Cove** is a city\nin Union County.\n',
                    date_created='2016-08-03',
                    date_updated='2016-08-04')
        doc = Document.create(**raws)

        ref = '**Cove** is a city\nin Union County.\n'
        self.assertEqual(ref, doc.body,
                         msg='Text mutated in document creation.')

        def replacement(callback, app):
            callback(Document)

        # Depending on the Django project wherein yamldoc is tested,
        # traverse.app may fail to include Document.
        # This is the only reason for patching here.
        with mock.patch('yamldoc.util.traverse.app', new=replacement):
            call_command('resolve_markup')

        doc.refresh_from_db()

        ref = '<p><strong>Cove</strong> is a city in Union County.</p>'
        self.assertEqual(ref, doc.body)


class _Other(TestCase):

    def test_slugification(self):
        s = 'This <em>sentence</em> has <span class="vague">some</span> HTML'
        ref = 'this-sentence-has-some-html'
        self.assertEqual(ref, slugify(s))

    def test_strip(self):
        s = 'A salute to <a href="www.plaid.com">plaid</a>.'
        ref = 'A salute to plaid.'
        self.assertEqual(ref, django.template.defaultfilters.striptags(s))

    def test_markdown_multiline(self):
        s = ('# A', '', '## a', '', '* li', '', 'p', '')
        ref = ('<h1 id="a">A</h1>', '<h2 id="a_1">a</h2>',
               '<ul>', '<li>li</li>', '</ul>',
               '<p>p</p>')

        self.assertEqual('\n'.join(ref),
                         markdown_on_string('\n'.join(s)))