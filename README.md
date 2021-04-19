# `yamlwrap`: VCS-friendly documents in YAML

This is a Python module for maintaining arbitrarily long documents in YAML
mappings, under version control.

`yamlwrap` serves this purpose by wrapping and unwrapping text. Save your YAML
in wrapped format for meaningful, easily reviewd diffs of short, readable
lines. Unwrap it to process multi-line Jinja markup etc.

`yamlwrap` is for people who maintain statically built web sites and prefer
off-line text editors over SQL and plutonian web-based administrative
interfaces.

## History

`yamlwrap` was originally part `django-yamldoc` of (`vedm`). It became its own
module in 2021.

## Legal

Copyright 2016–2021 Viktor Eikman

`yamlwrap` is licensed as detailed in the accompanying file LICENSE.
