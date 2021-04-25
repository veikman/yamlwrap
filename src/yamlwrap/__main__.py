"""A CLI application for yamlwrap, operating on files."""

import argparse
import logging
import sys
from difflib import unified_diff as diff
from pathlib import Path

from yamlwrap import __version__, transform

log = logging.getLogger('yamlwrap')


def before_and_after(args):
    """Transform contents. Return old and new contents."""
    before = args.source.read_text()
    after = transform(before, wrap=args.wrap or args.rewrap,
                      unwrap=args.unwrap or args.rewrap)
    return (before, before if after is None else after)


def write(args):
    """Write transformed contents to file."""
    _, new_target_contents = before_and_after(args)
    target = args.source if args.in_place else args.target
    target.write_text(new_target_contents)
    return 0


def diff_(args):
    """Show transformation."""
    old_source_contents, new_source_contents = before_and_after(args)

    target_contents = new_source_contents
    if args.reference is not None:
        target_contents = args.reference.read_text()

    old = old_source_contents.splitlines()
    new = target_contents.splitlines()
    tofile = args.reference or f'{args.source} [transformed]'
    for line in diff(old, new, fromfile=str(args.source),
                     tofile=str(tofile), lineterm=""):
        print(line)
    return 0


def path(mandatory=False, must_exist=False):
    """Close over a “type” function for argparse."""
    def parser(raw):
        try:
            if not mandatory and raw is None:
                return None
            p = Path(raw)
            if must_exist and not p.exists():
                raise argparse.ArgumentTypeError(f'File “{p}” not found.')
            return p
        except argparse.ArgumentTypeError:
            raise
        except Exception as e:
            # argparse might eat this exception without comment.
            print(f'Exception in path interpretation: {e!r}', file=sys.stderr)
            raise
    return parser


def define_cli():
    """Construct a CLI argument parser."""
    s = 'Transform YAML.'
    parser = argparse.ArgumentParser(prog='yamlwrap', description=s)
    level = parser.add_mutually_exclusive_group()
    level.set_defaults(logging_level=logging.INFO)
    level.add_argument('--verbose', dest='logging_level', action='store_const',
                       const=logging.DEBUG, help='extra logging')
    level.add_argument('--quiet', dest='logging_level', action='store_const',
                       const=logging.NOTSET, help='less logging')

    modes = parser.add_subparsers(title='mode', required=True)

    def add_mode(name, function, transform=False):
        subparser = modes.add_parser(name)
        subparser.set_defaults(function=function)

        if transform:
            subparser.add_argument('source',
                                   type=path(mandatory=True, must_exist=True),
                                   help='source file path')
            group = subparser.add_mutually_exclusive_group(required=True)
            group.add_argument('--wrap', default=False, action='store_true',
                               help='keep lines short')
            group.add_argument('--unwrap', default=False, action='store_true',
                               help='one long line per paragraph')
            group.add_argument('--rewrap', default=False, action='store_true',
                               help='unwrap and then wrap to clean document')

        return subparser

    add_mode('version', lambda _: print(__version__))

    writem = add_mode('write', write, transform=True)
    target = writem.add_mutually_exclusive_group(required=True)
    target.add_argument('--in-place', action='store_true',
                        help='replace the contents of the source file; '
                             'no backup is created')
    target.add_argument('--target', metavar='FILE', type=path(),
                        help='file path for storing the results of '
                             'transforming the contents of the source file; '
                             'if this file exists it will be overwritten')

    diffm = add_mode('diff', diff_, transform=True)
    diffm.add_argument('--reference', metavar='FILE',
                       type=path(must_exist=True),
                       help='file path for comparison; if omitted, compare '
                            'source file contents before and after '
                            'transformation')

    return parser


def main():
    """Run yamlwrap as a an application."""
    args = define_cli().parse_args()

    logging.basicConfig(level=args.logging_level)

    return args.function(args)


if __name__ == '__main__':
    sys.exit(main())
