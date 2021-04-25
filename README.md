# `yamlwrap`: VCS-friendly documents in YAML

This is a Python module for maintaining arbitrarily long documents in YAML
mappings, under version control and subject to other text-based tools.

`yamlwrap` serves this purpose by wrapping and unwrapping text. Save your YAML
in wrapped format for meaningful, easily reviewed diffs of short, readable,
editable lines. Unwrap it to process multi-line Jinja markup, grepping for
entire sentences etc.

## Audience

`yamlwrap` is for people who maintain the contents of statically built web
sites and prefer off-line text editors over SQL and plutonian web-based
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

## History

`yamlwrap` was originally part of `django-yamldoc`, when that project was
called `vedm`. It became its own module in 2021.

The project is still in a rudimentary state because it seeks to be idempotent;
a goal incompatible with the arbitrary markup schemes that may exist in YAML.

## Legal

Copyright 2016–2021 Viktor Eikman

`yamlwrap` is licensed as detailed in the accompanying file LICENSE.
