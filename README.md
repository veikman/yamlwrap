`yamlwrap` is a Python module for keeping content ready for the web while
under effective version control.

[![PyPI version](https://badge.fury.io/py/yamlwrap.svg)](https://badge.fury.io/py/yamlwrap)

## Audience

Do you use YAML just for configuration files? Then you don’t need `yamlwrap`.

Do you maintain a statically built web site? Do you want to keep even long
documents with complex internal markup in plain-text files, but always ready
for the ORM? Do you want automatic rewrapping (reflowing) of text for short
lines and neat Git diffs? Do you want to use YAML everywhere, for quick,
unambiguous, syntax-checked conversion to JSON or SQL for publication? Then
`yamlwrap` is for you.

Stop using plutonian web-based administrative interfaces. Use `yamlwrap` and
your favourite text editor.

## Usage

This project is primarily a function library. Its highest-level interface is
`yamlwrap.transform`, which takes and returns serialized YAML, along with
keyword parameters for how to change that YAML. `yamlwrap.unwrap`, which takes
a block of text as one string, is a suitable preprocessor for
line-break-sensitive markup resolution.

The package also comes with a CLI that works on a file level and can produce
diffs or new files from simple transformations.

### Examples

Using the CLI as shown in the [makefile](Makefile), `yamlwrap` took [this
hand-made original](example/a0_original.yaml) and made [this unwrapped
version](example/a2_unwrapped.yaml) as well as [this rewrapped
version](example/a3_rewrapped.yaml) for VCS.

## Development

This project is managed using PyInvoke. Run `inv -l` for a list of common
tasks.

## History

`yamlwrap` was originally part of
[`django-yamldoc`](https://github.com/veikman/django-yamldoc), when that
project was called `vedm`. It became its own module (v1.0.0) in 2021. Later
that year, internal logic based on Python regexes was stripped out in favour of
[`punwrap`](https://github.com/veikman/punwrap), resulting in a more narrow
focus (Markdown instead of arbitrary markup) and substantial behavioural
changes (v2.0.0).

Later changes are described in the [change log](CHANGELOG.md).

## Legal

Copyright 2016–2023 Viktor Eikman

`yamlwrap` is licensed as detailed in the accompanying file LICENSE.
