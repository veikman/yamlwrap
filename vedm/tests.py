# -*- coding: utf-8 -*-

from unittest import mock

from django.test import TestCase
from django.core.management import call_command
import django.template.defaultfilters

from vedm.models import MarkupField
from vedm.models import Document
from vedm.util.markup import Inline
from vedm.util.markup import Paragraph
from vedm.util.markup import get_fields
from vedm.util.markup import internal_on_string
from vedm.util.markup import markdown_on_string
from vedm.util.misc import slugify
from vedm.util.file import dump as dump_file
from vedm.util.file import transform
from vedm.util.file import wrap_paragraphs
from vedm.util.file import unwrap_paragraphs


class Models(TestCase):
    def test_document(self):
        fields = get_fields(Document, (MarkupField,))
        ref = (Document._meta.get_field('summary'),
               Document._meta.get_field('ingress'),
               Document._meta.get_field('body'))
        self.assertEqual(ref, fields)


class Wrapping(TestCase):
    def _rewrap(self, w0, u0, width=3):
        self.maxDiff = None

        w1 = wrap_paragraphs(w0, width=width)
        self.assertEqual(w0, w1)  # Wrapped to wrapped.
        u1 = unwrap_paragraphs(w1)
        self.assertEqual(u0, u1)  # Wrapped to unwrapped.

        u2 = unwrap_paragraphs(u0)
        self.assertEqual(u0, u2)  # Unwrapped to unwrapped.
        w2 = wrap_paragraphs(u2, width=width)
        self.assertEqual(w0, w2)  # Unwrapped to wrapped.

    def test_trivial(self):
        wrapped = 'aa\nbb'
        no_wrap = 'aa bb'
        self._rewrap(wrapped, no_wrap)

    def test_softbreak(self):
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

    def test_quote_block_oneparagraph(self):
        wrapped = ('a a\n\n> b\nb\n\nc c')
        no_wrap = ('a a\n\n> b b\n\nc c')
        self._rewrap(wrapped, no_wrap)

    def test_quote_block_multiparagraph(self):
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

    def test_markup(self):
        wrapped = ('{{mark|Aa a|param=Bb\nb}}\n\nCc c.')
        no_wrap = ('{{mark|Aa a|param=Bb b}}\n\nCc c.')
        self._rewrap(wrapped, no_wrap, width=20)

    def test_asymmetric_single_space_terminating_line(self):
        wrapped = 'aa \naa'
        no_wrap = 'aa \naa'  # Respected by unwrapper only!
        re_wrap = 'aa\naa'   # Destroyed.
        actual = unwrap_paragraphs(wrapped)
        self.assertEqual(no_wrap, actual)
        actual = wrap_paragraphs(actual, width=4)
        self.assertEqual(re_wrap, actual)

    def test_asymmetric_dirty_multiline(self):
        wrapped = 'a a\na a a\na a a a'
        no_wrap = 'a a a a a a a a a'
        re_wrap = 'a a a a a a a\na a'
        actual = unwrap_paragraphs(wrapped)
        self.assertEqual(no_wrap, actual)
        actual = wrap_paragraphs(actual, width=13)
        self.assertEqual(re_wrap, actual)


class PrettyYAML(TestCase):
    # Tests mainly of the third-party pyaml module itself for clarification.

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
        ref0 = 'key: |-\n  a \n  a\n'
        self.assertNotEqual(ref0, dump_file(data))
        ref1 = 'key: "a \\na"\n'
        self.assertEqual(ref1, dump_file(data))

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


class CookingMarkdown(TestCase):

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

    def test_flat_bullet_list(self):
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

    def test_nested_bullet_list(self):
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


class CookingInternalMarkup(TestCase):

    def test_nested(self):
        def paragraph():
            return '{{inline}}'

        Paragraph(paragraph)

        def inline():
            return 'i'

        Inline(inline)

        s = ('<p>{p{paragraph}p}</p>\n'
             '<p>{p{paragraph}p}<!--comment!--></p>\n'
             '<p>{p{paragraph}p} <!--another comment!--></p>\n'
             '<p>{{inline}}</p>\n')
        ref = ('i\n'
               'i\n'
               'i\n'
               '<p>i</p>\n')

        self.assertEqual(ref, internal_on_string(s))

    def test_multiline(self):
        def mask(s):
            return s

        Inline(mask)

        s0 = """Uh {{mask|huh.

        Nu}} uh."""
        s1 = """Uh huh.

        Nu uh."""
        self.assertEqual(Inline.collective_sub(s0), s1)


class CookingStructure(TestCase):

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


class CookingSite(TestCase):

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

        # Depending on the Django project wherein VEDM is tested,
        # traverse.app may fail to include Document.
        # This is the only reason for patching here.
        with mock.patch('vedm.util.traverse.app', new=replacement):
            call_command('resolve_markup')

        doc.refresh_from_db()

        ref = '<p><strong>Cove</strong> is a city in Union County.</p>'
        self.assertEqual(ref, doc.body)


class Other(TestCase):

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
