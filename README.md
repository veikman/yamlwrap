# `yamlwrap`: VCS-friendly documents in YAML

This is a Python module for maintaining arbitrarily long Markdown documents in
YAML mappings, under version control and subject to other text-based tools.

`yamlwrap` serves this purpose by adding YAML support to
`[punwrap](https://github.com/veikman/punwrap)`, a Rust extension for wrapping
Markdown.

## Audience

`yamlwrap` is for people who maintain the contents of statically built web
sites as YAML and prefer off-line text editors over SQL and plutonian web-based
administrative interfaces. It won’t do much good for configuration files.

## Usage

This is primarily a function library. Its main interface is
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

`yamlwrap` was originally part of `django-yamldoc`, when that project was
called `vedm`. It became its own module (v1.0.0) in 2021. Later that year,
internal logic based on Python regexes was stripped out in favour of `punwrap`,
resulting in a more narrow focus (Markdown instead of arbitrary markup) and
substantial behavioural changes (v2.0.0).

Later changes are described in the [change log](CHANGELOG.md).

## Legal

Copyright 2016–2021 Viktor Eikman

`yamlwrap` is licensed as detailed in the accompanying file LICENSE.
